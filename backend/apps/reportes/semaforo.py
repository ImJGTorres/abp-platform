from decimal import Decimal

VERDE = 'verde'
AMARILLO = 'amarillo'
ROJO = 'rojo'
NIVELES_SEMAFORO = (VERDE, AMARILLO, ROJO)


def obtener_umbrales():
    """
    Lee los umbrales del semáforo desde ParametroSistema.
    Si un parámetro no existe se usa su valor por defecto.
    """
    from .services import _get_parametro

    return {
        'nota_rojo': _get_parametro('umbral_nota_bajo_rendimiento', Decimal('3.0')),
        'pct_rojo': _get_parametro('umbral_porcentaje_actividades_incumplidas', 50),
        'nota_amarillo': _get_parametro('umbral_nota_alerta', Decimal('3.5')),
        'pct_amarillo': _get_parametro('umbral_porcentaje_alerta', 25),
    }


def clasificar_semaforo(nota, pct_incumplidas, tiene_actividades=True, umbrales=None):
    """
    Clasifica el rendimiento de un estudiante en un semáforo de 3 niveles (RF34).

    Regla, evaluada en este orden:
      1. Sin actividades asignadas (tiene_actividades=False)  -> 'verde'.
      2. nota < umbral_nota_bajo_rendimiento (3.0)
         o pct_incumplidas >= umbral_porcentaje_actividades_incumplidas (50) -> 'rojo'.
      3. nota < umbral_nota_alerta (3.5)
         o pct_incumplidas >= umbral_porcentaje_alerta (25)                  -> 'amarillo'.
      4. En otro caso                                                        -> 'verde'.

    Los valores entre paréntesis son los usados por defecto; los reales se leen
    de ParametroSistema con obtener_umbrales().

    Parámetros:
      nota             -- nota promedio en escala 0-5.
      pct_incumplidas  -- % de actividades incumplidas (0-100).
      tiene_actividades -- False si el estudiante no tiene actividades asignadas.
      umbrales         -- dict de obtener_umbrales(); si es None se consulta la BD.
                          Pásalo al clasificar muchos estudiantes para no repetir
                          las consultas.

    Retorna 'verde', 'amarillo' o 'rojo'.
    Ejemplos: (2.8, 10) -> 'rojo', (3.2, 10) -> 'amarillo',
              (4.0, 10) -> 'verde', (4.0, 60) -> 'rojo'.
    """
    if not tiene_actividades:
        return VERDE

    if umbrales is None:
        umbrales = obtener_umbrales()

    nota = Decimal(str(nota))
    pct = Decimal(str(pct_incumplidas))

    if nota < umbrales['nota_rojo'] or pct >= umbrales['pct_rojo']:
        return ROJO
    if nota < umbrales['nota_amarillo'] or pct >= umbrales['pct_amarillo']:
        return AMARILLO
    return VERDE


DIAS_PROXIMO_VENCIMIENTO = 3


def semaforo_estudiante(estudiante_id, proyecto_id=None):
    """
    Semáforo personal del estudiante (HU-041). Reutiliza calcular_rendimiento_estudiante()
    (mismos umbrales RF34 que HU-029 y HU-033); no recalcula reglas.

    Retorna {nivel, nota_promedio, porcentaje_actividades_incumplidas,
             entregables_criticos, recomendaciones}.
    entregables_criticos: actividades no completadas vencidas o que vencen en ≤ 3 días
    y entregables rechazados, cada uno con {titulo, fecha, estado, enlace}.
    """
    from datetime import date, timedelta

    from django.db.models import Q

    from apps.cursos.models import Actividad
    from apps.entregables.models import Entregable
    from apps.equipos.models import MiembroEquipo

    from .services import calcular_rendimiento_estudiante

    umbrales = obtener_umbrales()
    rendimiento = calcular_rendimiento_estudiante(estudiante_id, proyecto_id=proyecto_id, umbrales=umbrales)

    # Mismo alcance que calcular_rendimiento_estudiante(): responsable o equipo activo asignado
    equipos = MiembroEquipo.objects.filter(usuario_id=estudiante_id, estado='activo')
    if proyecto_id:
        equipos = equipos.filter(equipo__proyecto_id=proyecto_id)
    equipo_ids = list(equipos.values_list('equipo_id', flat=True))

    hoy = date.today()
    actividades = (Actividad.objects
                   .filter(Q(id_responsable_id=estudiante_id) | Q(id_equipo_asignado_id__in=equipo_ids))
                   .exclude(estado='completada')
                   .filter(fecha_limite__lte=hoy + timedelta(days=DIAS_PROXIMO_VENCIMIENTO))
                   .select_related('id_fase')
                   .distinct()
                   .order_by('fecha_limite', 'id'))
    if proyecto_id:
        actividades = actividades.filter(id_fase__id_proyecto_id=proyecto_id)
    rechazados = (Entregable.objects
                  .filter(id_equipo_id__in=equipo_ids, estado='rechazado')
                  .select_related('id_actividad__id_fase')
                  .order_by('id_actividad__fecha_limite', 'id'))

    def _enlace(actividad):
        return (f'/estudiante/proyectos/{actividad.id_fase.id_proyecto_id}'
                f'/actividades/{actividad.id}/entregables')

    vencidas = [a for a in actividades if a.fecha_limite < hoy]
    criticos = [
        {'titulo': a.nombre, 'fecha': a.fecha_limite.isoformat(),
         'estado': 'vencida' if a.fecha_limite < hoy else 'por_vencer', 'enlace': _enlace(a)}
        for a in actividades
    ] + [
        {'titulo': e.titulo, 'fecha': e.id_actividad.fecha_limite.isoformat(),
         'estado': 'rechazado', 'enlace': _enlace(e.id_actividad)}
        for e in rechazados
    ]

    nivel = rendimiento['nivel_semaforo']
    nota = rendimiento['nota_promedio']
    recomendaciones = []
    if vencidas:
        n = len(vencidas)
        cuantas = '1 actividad vencida' if n == 1 else f'{n} actividades vencidas'
        recomendaciones.append(f'Tienes {cuantas}; empieza por «{vencidas[0].nombre}»')
    if rendimiento['total_actividades'] > 0 and Decimal(str(nota)) < umbrales['nota_amarillo']:
        umbral = umbrales['nota_rojo'] if Decimal(str(nota)) < umbrales['nota_rojo'] else umbrales['nota_amarillo']
        recomendaciones.append(f'Tu promedio ({nota}) está por debajo de {umbral}')
    for e in rechazados:
        recomendaciones.append(f'Corrige y reenvía «{e.titulo}»')
    if not recomendaciones:
        if nivel == VERDE:
            recomendaciones.append('Vas al día; mantén el ritmo')
        else:
            recomendaciones.append(
                f"Tienes el {rendimiento['porcentaje_actividades_incumplidas']}% de tus actividades "
                f"sin completar; revisa tu tablero")

    return {
        'nivel': nivel,
        'nota_promedio': nota,
        'porcentaje_actividades_incumplidas': rendimiento['porcentaje_actividades_incumplidas'],
        'entregables_criticos': criticos,
        'recomendaciones': recomendaciones,
    }
