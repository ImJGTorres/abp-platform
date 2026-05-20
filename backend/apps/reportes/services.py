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


# ── HU-031: Reportes por proyecto ────────────────────────────────────────────

from django.db import connection  # noqa: E402


def _fetchall_as_dicts(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def reporte_proyecto(proyecto_id):
    from django.apps import apps as dj_apps
    Proyecto             = dj_apps.get_model('cursos', 'Proyecto')
    ObjetivoProyecto     = dj_apps.get_model('cursos', 'ObjetivoProyecto')
    ResultadoAprendizaje = dj_apps.get_model('cursos', 'ResultadoAprendizaje')
    HitoProyecto         = dj_apps.get_model('cursos', 'HitoProyecto')
    Equipo               = dj_apps.get_model('equipos', 'Equipo')
    MiembroEquipo        = dj_apps.get_model('equipos', 'MiembroEquipo')
    Entregable           = dj_apps.get_model('entregables', 'Entregable')

    try:
        proyecto = Proyecto.objects.select_related('id_curso').get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return None

    info = {
        'id': proyecto.id,
        'nombre': proyecto.nombre,
        'descripcion': proyecto.descripcion,
        'estado': proyecto.estado,
        'fecha_inicio': str(proyecto.fecha_inicio),
        'fecha_fin_estimada': str(proyecto.fecha_fin_estimada),
        'curso': proyecto.id_curso.nombre if proyecto.id_curso_id else None,
    }

    objetivos = list(
        ObjetivoProyecto.objects.filter(id_proyecto_id=proyecto_id)
        .order_by('orden')
        .values('id', 'descripcion', 'tipo', 'orden')
    )
    resultados = list(
        ResultadoAprendizaje.objects.filter(proyecto_id=proyecto_id)
        .values('id', 'nombre', 'descripcion', 'competencia_asociada', 'porcentaje_evaluacion')
    )

    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM vista_progreso_fase WHERE id_proyecto = %s ORDER BY orden",
            [proyecto_id],
        )
        fases = _fetchall_as_dicts(cur)

    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM vista_progreso_proyecto WHERE id_proyecto = %s",
            [proyecto_id],
        )
        rows = _fetchall_as_dicts(cur)
        progreso_global = rows[0] if rows else {}

    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM vista_entregables_proyecto WHERE proyecto_id = %s",
            [proyecto_id],
        )
        rows = _fetchall_as_dicts(cur)
        resumen_entregables = rows[0] if rows else {}

    equipos_qs = Equipo.objects.filter(proyecto_id=proyecto_id)
    equipos = []
    for eq in equipos_qs:
        miembros = list(
            MiembroEquipo.objects.filter(equipo_id=eq.id, estado='activo')
            .select_related('usuario')
            .values(
                'usuario__id', 'usuario__nombre', 'usuario__apellido',
                'usuario__correo', 'usuario__codigo_estudiante', 'rol_interno',
            )
        )
        ents = Entregable.objects.filter(id_equipo_id=eq.id)
        equipos.append({
            'id': eq.id,
            'nombre': eq.nombre,
            'estado': eq.estado,
            'total_miembros': len(miembros),
            'miembros': miembros,
            'entregables': {
                'total': ents.count(),
                'aprobados': ents.filter(estado='aprobado').count(),
                'rechazados': ents.filter(estado='rechazado').count(),
                'pendientes': ents.filter(estado='borrador').count(),
            },
        })

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT
                vae.usuario_id,
                u.nombre,
                u.apellido,
                u.correo,
                u.codigo_estudiante,
                vae.promedio_avance_pct,
                vae.nota_promedio_5,
                vae.actividades_con_avance
            FROM vista_avance_estudiante_proyecto vae
            JOIN usuario u ON u.id = vae.usuario_id
            WHERE vae.proyecto_id = %s
            ORDER BY vae.nota_promedio_5 ASC
            """,
            [proyecto_id],
        )
        avance_estudiantes = _fetchall_as_dicts(cur)

    umbral = _get_parametro('umbral_nota_bajo_rendimiento', 3.0)

    bajo_rendimiento = [
        e for e in avance_estudiantes
        if e.get('nota_promedio_5') is not None and float(e['nota_promedio_5']) < float(umbral)
    ]

    hitos = list(
        HitoProyecto.objects.filter(id_proyecto_id=proyecto_id)
        .values('id', 'nombre', 'tipo', 'estado', 'fecha_inicio', 'fecha_fin')
    )

    return {
        'proyecto': info,
        'objetivos': objetivos,
        'resultados_aprendizaje': resultados,
        'hitos': hitos,
        'progreso_global': progreso_global,
        'progreso_por_fase': fases,
        'resumen_entregables': resumen_entregables,
        'equipos': equipos,
        'avance_por_estudiante': avance_estudiantes,
        'estudiantes_bajo_rendimiento': bajo_rendimiento,
        'umbral_bajo_rendimiento': float(umbral),
    }


def reporte_curso(curso_id):
    from django.apps import apps as dj_apps
    Curso    = dj_apps.get_model('cursos', 'Curso')
    Proyecto = dj_apps.get_model('cursos', 'Proyecto')

    try:
        curso = Curso.objects.select_related('id_periodo_academico').get(id=curso_id)
    except Curso.DoesNotExist:
        return None

    proyectos = Proyecto.objects.filter(id_curso_id=curso_id)
    proyecto_ids = list(proyectos.values_list('id', flat=True))

    if not proyecto_ids:
        return {
            'curso': {'id': curso.id, 'nombre': curso.nombre, 'codigo': curso.codigo},
            'total_proyectos': 0,
            'proyectos': [],
        }

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM vista_progreso_proyecto
            WHERE id_proyecto = ANY(%s)
            ORDER BY porcentaje_progreso DESC
            """,
            [proyecto_ids],
        )
        progresos = {row['id_proyecto']: row for row in _fetchall_as_dicts(cur)}

    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM vista_entregables_proyecto WHERE proyecto_id = ANY(%s)",
            [proyecto_ids],
        )
        entregables_por_proyecto = {row['proyecto_id']: row for row in _fetchall_as_dicts(cur)}

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT
                proyecto_id,
                ROUND(AVG(nota_promedio_5)::numeric, 2) AS nota_promedio_proyecto
            FROM vista_avance_estudiante_proyecto
            WHERE proyecto_id = ANY(%s)
            GROUP BY proyecto_id
            """,
            [proyecto_ids],
        )
        notas_por_proyecto = {
            row['proyecto_id']: row['nota_promedio_proyecto']
            for row in _fetchall_as_dicts(cur)
        }

    resultado_proyectos = []
    for p in proyectos:
        prog = progresos.get(p.id, {})
        ents = entregables_por_proyecto.get(p.id, {})
        resultado_proyectos.append({
            'id': p.id,
            'nombre': p.nombre,
            'estado': p.estado,
            'fecha_inicio': str(p.fecha_inicio),
            'fecha_fin_estimada': str(p.fecha_fin_estimada),
            'porcentaje_progreso': prog.get('porcentaje_progreso', 0),
            'total_fases': prog.get('total_fases', 0),
            'fases_completadas': prog.get('fases_completadas', 0),
            'total_actividades': prog.get('total_actividades', 0),
            'actividades_completadas': prog.get('actividades_completadas', 0),
            'total_entregables': ents.get('total_entregables', 0),
            'aprobados': ents.get('aprobados', 0),
            'rechazados': ents.get('rechazados', 0),
            'tasa_entrega_tiempo_pct': ents.get('tasa_entrega_tiempo_pct', 0),
            'nota_promedio_grupo': notas_por_proyecto.get(p.id, None),
        })

    return {
        'curso': {
            'id': curso.id,
            'nombre': curso.nombre,
            'codigo': curso.codigo,
            'periodo': curso.id_periodo_academico.nombre if curso.id_periodo_academico_id else None,
        },
        'total_proyectos': len(resultado_proyectos),
        'proyectos': resultado_proyectos,
    }
