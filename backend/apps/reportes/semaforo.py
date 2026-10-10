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


def _notas_por_proyecto(proyecto_ids):
    """Nota promedio (0-5) de cada proyecto desde vista_avance_estudiante_proyecto, en una consulta."""
    from django.db import connection

    if not proyecto_ids:
        return {}
    marcadores = ', '.join(['%s'] * len(proyecto_ids))
    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT proyecto_id, AVG(nota_promedio_5)
            FROM vista_avance_estudiante_proyecto
            WHERE proyecto_id IN ({marcadores})
            GROUP BY proyecto_id
            """,
            list(proyecto_ids),
        )
        return {pid: float(nota) for pid, nota in cur.fetchall() if nota is not None}


def semaforos_docente(docente_id, color=None):
    """
    Panel de semáforos del docente (HU-042): un elemento por proyecto no finalizado de sus cursos.
    Nivel RF34 del proyecto = clasificar_semaforo(nota promedio del proyecto, % de actividades
    incumplidas del proyecto) con los umbrales de ParametroSistema (los mismos de HU-029/033/041).
    Avance, total y completadas salen de VistaProgresoProyecto; la nota, de
    vista_avance_estudiante_proyecto (consultas agrupadas, no un ciclo por estudiante).
    color: si se indica, filtra después de calcular el nivel.
    Retorna [{proyecto_id, nombre, curso_id, curso_nombre, nivel, porcentaje_avance}].
    """
    from apps.cursos.models import Proyecto, VistaProgresoProyecto

    proyectos = list(
        Proyecto.objects.filter(id_curso__id_docente_id=docente_id)
        .exclude(estado=Proyecto.Estado.FINALIZADO)
        .select_related('id_curso')
        .order_by('id_curso__nombre', 'nombre', 'id')
    )
    ids = [p.id for p in proyectos]
    progreso = {
        v['id_proyecto']: v for v in VistaProgresoProyecto.objects.filter(id_proyecto__in=ids).values(
            'id_proyecto', 'porcentaje_progreso', 'total_actividades', 'actividades_completadas')
    }
    notas = _notas_por_proyecto(ids)
    umbrales = obtener_umbrales()

    resultado = []
    for p in proyectos:
        datos = progreso.get(p.id, {})
        total = datos.get('total_actividades') or 0
        completadas = datos.get('actividades_completadas') or 0
        pct_incumplidas = round((total - completadas) / total * 100, 2) if total else 0
        nivel = clasificar_semaforo(notas.get(p.id, 0), pct_incumplidas,
                                    tiene_actividades=total > 0, umbrales=umbrales)
        if color and nivel != color:
            continue
        resultado.append({
            'proyecto_id': p.id,
            'nombre': p.nombre,
            'curso_id': p.id_curso_id,
            'curso_nombre': p.id_curso.nombre,
            'nivel': nivel,
            'porcentaje_avance': int(datos.get('porcentaje_progreso') or 0),
        })
    return resultado
