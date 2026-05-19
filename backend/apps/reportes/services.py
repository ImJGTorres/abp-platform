from decimal import Decimal

from django.db.models import Avg, Q


def _get_parametro(clave, default):
    from apps.configuracion.models import ParametroSistema
    try:
        p = ParametroSistema.objects.get(clave=clave)
        return type(default)(p.valor)
    except ParametroSistema.DoesNotExist:
        return default


def calcular_rendimiento_estudiante(estudiante_id, proyecto_id=None, curso_id=None):
    """
    Calcula indicadores de rendimiento de un estudiante.
    Retorna dict con nota_promedio, porcentaje_actividades_incumplidas,
    entregables_rechazados, totales, en_riesgo y alertas.
    """
    from apps.cursos.models import Actividad, AvanceActividad
    from apps.entregables.models import Entregable
    from apps.equipos.models import MiembroEquipo

    umbral_nota = _get_parametro('umbral_nota_bajo_rendimiento', Decimal('3.0'))
    umbral_pct_incumplidas = _get_parametro('umbral_porcentaje_actividades_incumplidas', 50)
    umbral_rechazados = _get_parametro('umbral_entregables_rechazados', 2)

    equipos_qs = MiembroEquipo.objects.filter(usuario_id=estudiante_id, estado='activo')
    if proyecto_id:
        equipos_qs = equipos_qs.filter(equipo__proyecto_id=proyecto_id)
    if curso_id:
        equipos_qs = equipos_qs.filter(equipo__proyecto__id_curso_id=curso_id)

    equipo_ids = list(equipos_qs.values_list('equipo_id', flat=True))

    avances = AvanceActividad.objects.filter(id_usuario_id=estudiante_id)
    if proyecto_id or curso_id:
        avances = avances.filter(id_actividad__id_equipo_asignado_id__in=equipo_ids)

    nota_raw = avances.aggregate(avg=Avg('porcentaje_completado'))['avg'] or 0
    nota_promedio = round((nota_raw / 100) * 5, 2)

    actividades_qs = Actividad.objects.filter(
        Q(id_responsable_id=estudiante_id) | Q(id_equipo_asignado_id__in=equipo_ids)
    )
    if proyecto_id:
        actividades_qs = actividades_qs.filter(id_fase__id_proyecto_id=proyecto_id)
    if curso_id:
        actividades_qs = actividades_qs.filter(id_fase__id_proyecto__id_curso_id=curso_id)

    total_actividades = actividades_qs.count()
    actividades_incumplidas = actividades_qs.filter(~Q(estado='completada')).count()
    pct_incumplidas = round(
        (actividades_incumplidas / total_actividades * 100) if total_actividades > 0 else 0, 2
    )

    entregables_qs = Entregable.objects.filter(id_equipo_id__in=equipo_ids)
    total_entregables = entregables_qs.count()
    entregables_rechazados = entregables_qs.filter(estado='rechazado').count()

    alertas = []
    if nota_promedio < float(umbral_nota):
        alertas.append(f"Nota promedio {nota_promedio} está por debajo del umbral {umbral_nota}")
    if pct_incumplidas >= umbral_pct_incumplidas:
        alertas.append(
            f"{pct_incumplidas}% de actividades incumplidas (umbral: {umbral_pct_incumplidas}%)"
        )
    if entregables_rechazados >= umbral_rechazados:
        alertas.append(
            f"{entregables_rechazados} entregables rechazados (umbral: {umbral_rechazados})"
        )

    return {
        'nota_promedio': nota_promedio,
        'porcentaje_actividades_incumplidas': pct_incumplidas,
        'actividades_incumplidas': actividades_incumplidas,
        'total_actividades': total_actividades,
        'entregables_rechazados': entregables_rechazados,
        'total_entregables': total_entregables,
        'en_riesgo': len(alertas) > 0,
        'alertas': alertas,
    }


def get_estudiantes_bajo_rendimiento(curso_id=None, proyecto_id=None, periodo_id=None):
    """Retorna lista de estudiantes en riesgo con sus indicadores."""
    from apps.usuarios.models import Usuario
    from apps.equipos.models import MiembroEquipo

    estudiantes_qs = Usuario.objects.filter(tipo_rol='estudiante', estado='activo')

    if periodo_id:
        estudiantes_qs = estudiantes_qs.filter(
            cursos_inscritos__curso__id_periodo_academico_id=periodo_id,
            cursos_inscritos__estado='activo',
        ).distinct()

    if curso_id:
        estudiantes_qs = estudiantes_qs.filter(
            cursos_inscritos__curso_id=curso_id,
            cursos_inscritos__estado='activo',
        ).distinct()

    if proyecto_id:
        member_ids = MiembroEquipo.objects.filter(
            equipo__proyecto_id=proyecto_id,
            estado='activo',
        ).values_list('usuario_id', flat=True)
        estudiantes_qs = estudiantes_qs.filter(id__in=member_ids)

    resultado = []
    for est in estudiantes_qs:
        indicadores = calcular_rendimiento_estudiante(
            est.id, proyecto_id=proyecto_id, curso_id=curso_id
        )
        if indicadores['en_riesgo']:
            resultado.append({
                'id': est.id,
                'nombre': est.nombre,
                'apellido': est.apellido,
                'correo': est.correo,
                'codigo_estudiante': est.codigo_estudiante,
                **indicadores,
            })

    return resultado
