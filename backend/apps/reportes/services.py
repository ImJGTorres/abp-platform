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
    # Solo se alerta por nota si el estudiante ya tiene actividades asignadas
    if total_actividades > 0 and nota_promedio < float(umbral_nota):
        alertas.append(f"Nota promedio {nota_promedio} está por debajo del umbral {umbral_nota}")
    if total_actividades > 0 and pct_incumplidas >= umbral_pct_incumplidas:
        alertas.append(
            f"{pct_incumplidas}% de actividades incumplidas (umbral: {umbral_pct_incumplidas}%)"
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


def get_estudiantes_bajo_rendimiento(curso_id=None, proyecto_id=None, periodo_id=None, solo_riesgo=True):
    """Retorna lista de estudiantes con sus indicadores, filtrados o no por riesgo."""
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
        if solo_riesgo and not indicadores['en_riesgo']:
            continue
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
                'usuario__correo', 'usuario__codigo', 'rol_interno',
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
                u.codigo,
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


# ── HU-032 ─────────────────────────────────────────────────────────────────

def _peso(clave, default):
    """Lee un peso de parametro_sistema y lo retorna como float 0–1."""
    try:
        from apps.configuracion.models import ParametroSistema
        return float(ParametroSistema.objects.get(clave=clave).valor) / 100.0
    except Exception:
        return default


def calcular_nota_ponderada(nota_docente_5, nota_auto_5=None, nota_co_5=None):
    """
    Nota final ponderada en escala 0-5.
    Cuando auto/co son None, su peso se redistribuye al docente.
    """
    w_doc = _peso('peso_evaluacion_docente', 0.70)
    w_auto = _peso('peso_autoevaluacion', 0.15)
    w_co = _peso('peso_coevaluacion', 0.15)

    peso_total = w_doc
    componentes = {'docente': (nota_docente_5, w_doc)}

    if nota_auto_5 is not None:
        componentes['autoevaluacion'] = (nota_auto_5, w_auto)
        peso_total += w_auto
    if nota_co_5 is not None:
        componentes['coevaluacion'] = (nota_co_5, w_co)
        peso_total += w_co

    if peso_total == 0:
        return 0.0

    nota_final = sum(nota * (w / peso_total) for nota, w in componentes.values())

    return {
        'nota_final': round(nota_final, 2),
        'componentes': {
            k: {'nota': round(v[0], 2), 'peso_aplicado': round(v[1] / peso_total * 100, 1)}
            for k, v in componentes.items()
        },
        'nota_docente_5': round(nota_docente_5, 2),
        'nota_auto_5': nota_auto_5,
        'nota_co_5': nota_co_5,
    }


def reporte_estudiante_proyecto(estudiante_id, proyecto_id):
    """
    Reporte completo de un estudiante en un proyecto específico.
    """
    from django.apps import apps as dj_apps

    Usuario              = dj_apps.get_model('usuarios', 'Usuario')
    Proyecto             = dj_apps.get_model('cursos', 'Proyecto')
    Actividad            = dj_apps.get_model('cursos', 'Actividad')
    Entregable           = dj_apps.get_model('entregables', 'Entregable')
    MiembroEquipo        = dj_apps.get_model('equipos', 'MiembroEquipo')
    ResultadoAprendizaje = dj_apps.get_model('cursos', 'ResultadoAprendizaje')

    try:
        estudiante = Usuario.objects.get(id=estudiante_id)
        proyecto = Proyecto.objects.select_related('id_curso').get(id=proyecto_id)
    except (Usuario.DoesNotExist, Proyecto.DoesNotExist):
        return None

    membresia = MiembroEquipo.objects.filter(
        usuario_id=estudiante_id,
        equipo__proyecto_id=proyecto_id,
        estado='activo',
    ).select_related('equipo').first()

    if not membresia:
        equipo = None
        equipo_id = None
    else:
        equipo = {'id': membresia.equipo.id, 'nombre': membresia.equipo.nombre}
        equipo_id = membresia.equipo.id

    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM vista_desempeno_estudiante WHERE usuario_id = %s AND proyecto_id = %s",
            [estudiante_id, proyecto_id],
        )
        cols = [c[0] for c in cur.description]
        row = cur.fetchone()
        desempeno = dict(zip(cols, row)) if row else {}

    nota_docente = float(desempeno.get('nota_docente_5') or 0)
    nota_pond = calcular_nota_ponderada(nota_docente)

    historial_entregables = []
    if equipo_id:
        entregables_qs = (
            Entregable.objects
            .filter(id_equipo_id=equipo_id)
            .select_related('id_actividad', 'id_docente_validador')
            .order_by('-fecha_creacion')
        )
        historial_entregables = [
            {
                'id': e.id,
                'titulo': e.titulo,
                'tipo': e.tipo,
                'estado': e.estado,
                'numero_version': e.numero_version,
                'fecha_envio': e.fecha_envio.isoformat() if e.fecha_envio else None,
                'fecha_validacion': e.fecha_validacion.isoformat() if e.fecha_validacion else None,
                'retroalimentacion': e.retroalimentacion,
                'docente_validador': (
                    f"{e.id_docente_validador.nombre} {e.id_docente_validador.apellido}"
                    if e.id_docente_validador_id else None
                ),
                'actividad': e.id_actividad.nombre if e.id_actividad_id else None,
                'fecha_limite_actividad': (
                    str(e.id_actividad.fecha_limite) if e.id_actividad_id else None
                ),
                'entregado_a_tiempo': (
                    e.fecha_envio.date() <= e.id_actividad.fecha_limite
                    if e.fecha_envio and e.id_actividad_id else None
                ),
            }
            for e in entregables_qs
        ]

    filtro = Q(id_responsable_id=estudiante_id)
    if equipo_id:
        filtro |= Q(id_equipo_asignado_id=equipo_id)
    actividades_qs = (
        Actividad.objects
        .filter(id_fase__id_proyecto_id=proyecto_id)
        .filter(filtro)
        .order_by('fecha_limite')
    )
    historial_actividades = list(
        actividades_qs.values('id', 'nombre', 'estado', 'fecha_limite', 'prioridad')
    )

    resultados = list(
        ResultadoAprendizaje.objects.filter(proyecto_id=proyecto_id)
        .values('id', 'nombre', 'descripcion', 'porcentaje_evaluacion', 'competencia_asociada')
    )

    return {
        'estudiante': {
            'id': estudiante.id,
            'nombre': estudiante.nombre,
            'apellido': estudiante.apellido,
            'correo': estudiante.correo,
            'codigo': estudiante.codigo,
        },
        'proyecto': {
            'id': proyecto.id,
            'nombre': proyecto.nombre,
            'estado': proyecto.estado,
            'curso': proyecto.id_curso.nombre if proyecto.id_curso_id else None,
        },
        'equipo': equipo,
        'nota_final': nota_pond,
        'desempeno': {
            'total_actividades_equipo': desempeno.get('total_actividades_equipo', 0),
            'actividades_completadas': desempeno.get('actividades_completadas', 0),
            'actividades_vencidas': desempeno.get('actividades_vencidas', 0),
            'total_avances_registrados': desempeno.get('total_avances_registrados', 0),
            'promedio_avance_pct': desempeno.get('promedio_avance_pct', 0),
            'total_entregables': desempeno.get('total_entregables', 0),
            'entregables_aprobados': desempeno.get('entregables_aprobados', 0),
            'entregables_rechazados': desempeno.get('entregables_rechazados', 0),
            'entregables_a_tiempo': desempeno.get('entregables_a_tiempo', 0),
        },
        'resultados_aprendizaje': resultados,
        'historial_entregables': historial_entregables,
        'historial_actividades': historial_actividades,
    }


def reporte_equipo_estudiantes(equipo_id):
    """
    Comparativa de desempeño de todos los miembros de un equipo.
    """
    from django.apps import apps as dj_apps

    Equipo        = dj_apps.get_model('equipos', 'Equipo')
    MiembroEquipo = dj_apps.get_model('equipos', 'MiembroEquipo')

    try:
        equipo = Equipo.objects.select_related('proyecto').get(id=equipo_id)
    except Equipo.DoesNotExist:
        return None

    miembros = list(
        MiembroEquipo.objects.filter(equipo_id=equipo_id, estado='activo')
        .select_related('usuario')
        .values(
            'usuario__id', 'usuario__nombre', 'usuario__apellido',
            'usuario__correo', 'usuario__codigo', 'rol_interno',
        )
    )

    usuario_ids = [m['usuario__id'] for m in miembros]

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM vista_desempeno_estudiante
            WHERE usuario_id = ANY(%s) AND equipo_id = %s
            """,
            [usuario_ids, equipo_id],
        )
        cols = [c[0] for c in cur.description]
        desempenos = {row[0]: dict(zip(cols, row)) for row in cur.fetchall()}

    comparativa = []
    for m in miembros:
        uid = m['usuario__id']
        d = desempenos.get(uid, {})
        nota_docente = float(d.get('nota_docente_5') or 0)
        nota_pond = calcular_nota_ponderada(nota_docente)
        comparativa.append({
            'estudiante': {
                'id': uid,
                'nombre': m['usuario__nombre'],
                'apellido': m['usuario__apellido'],
                'correo': m['usuario__correo'],
                'codigo': m['usuario__codigo'],
                'rol_interno': m['rol_interno'],
            },
            'nota_final': nota_pond['nota_final'],
            'promedio_avance_pct': d.get('promedio_avance_pct', 0),
            'actividades_completadas': d.get('actividades_completadas', 0),
            'actividades_vencidas': d.get('actividades_vencidas', 0),
            'total_avances_registrados': d.get('total_avances_registrados', 0),
            'entregables_aprobados': d.get('entregables_aprobados', 0),
            'entregables_rechazados': d.get('entregables_rechazados', 0),
        })

    comparativa.sort(key=lambda x: x['nota_final'], reverse=True)

    return {
        'equipo': {
            'id': equipo.id,
            'nombre': equipo.nombre,
            'proyecto_id': equipo.proyecto_id,
            'proyecto_nombre': equipo.proyecto.nombre,
        },
        'total_miembros': len(comparativa),
        'miembros': comparativa,
    }


# ── HU-033 ─────────────────────────────────────────────────────────────────

def _indicadores_estudiantes_riesgo_por_curso(periodo_id=None, curso_id=None):
    """
    Retorna conteo de estudiantes en riesgo agrupado por curso.
    Usa umbral desde parametro_sistema.
    """
    try:
        from apps.configuracion.models import ParametroSistema
        umbral = float(ParametroSistema.objects.get(clave='umbral_nota_bajo_rendimiento').valor)
    except Exception:
        umbral = 3.0

    with connection.cursor() as cur:
        filtros = []
        params = [umbral]

        if periodo_id:
            filtros.append("AND c.id_periodo_academico_id = %s")
            params.append(periodo_id)
        if curso_id:
            filtros.append("AND c.id = %s")
            params.append(curso_id)

        filtro_sql = " ".join(filtros)

        cur.execute(
            f"""
            SELECT
                c.id                          AS curso_id,
                c.nombre                      AS curso_nombre,
                COUNT(DISTINCT vae.usuario_id) FILTER (
                    WHERE vae.nota_promedio_5 < %s
                )                             AS estudiantes_en_riesgo,
                COUNT(DISTINCT vae.usuario_id) AS total_estudiantes_con_avance
            FROM vista_avance_estudiante_proyecto vae
            JOIN proyecto p  ON p.id = vae.proyecto_id
            JOIN curso c     ON c.id = p.id_curso_id
            WHERE 1=1 {filtro_sql}
            GROUP BY c.id, c.nombre
            ORDER BY estudiantes_en_riesgo DESC
            """,
            params,
        )
        return _fetchall_as_dicts(cur)


def indicadores_dashboard(periodo_id=None, curso_id=None):
    """
    Dashboard de indicadores institucionales.
    Filtros opcionales: periodo_id, curso_id.
    """
    # ── 1. Resumen desde vista_indicadores_periodo ──
    if periodo_id:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT * FROM vista_indicadores_periodo WHERE periodo_id = %s",
                [periodo_id],
            )
            rows = _fetchall_as_dicts(cur)
            resumen_periodo = rows[0] if rows else {}
    else:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT * FROM vista_indicadores_periodo ORDER BY periodo_inicio DESC"
            )
            resumen_periodo = _fetchall_as_dicts(cur)

    # ── 2. Docentes más activos (cursos que tienen en el periodo) ──
    with connection.cursor() as cur:
        filtro_periodo = "AND c.id_periodo_academico_id = %s" if periodo_id else ""
        filtro_curso = "AND c.id = %s" if curso_id else ""
        params_doc = []
        if periodo_id:
            params_doc.append(periodo_id)
        if curso_id:
            params_doc.append(curso_id)

        cur.execute(
            f"""
            SELECT
                u.id,
                u.nombre,
                u.apellido,
                u.correo,
                COUNT(DISTINCT c.id)   AS total_cursos,
                COUNT(DISTINCT p.id)   AS total_proyectos,
                COUNT(DISTINCT a.id)   AS total_actividades_validadas
            FROM usuario u
            JOIN curso c        ON c.id_docente_id = u.id
            LEFT JOIN proyecto p ON p.id_curso_id = c.id
            LEFT JOIN entregable e ON e.id_docente_validador_id = u.id
            LEFT JOIN actividad a  ON a.id = e.id_actividad_id
            WHERE u.tipo_rol IN ('docente', 'director')
              {filtro_periodo}
              {filtro_curso}
            GROUP BY u.id, u.nombre, u.apellido, u.correo
            ORDER BY total_cursos DESC, total_proyectos DESC
            LIMIT 10
            """,
            params_doc,
        )
        docentes_activos = _fetchall_as_dicts(cur)

    # ── 3. Progreso de proyectos activos ──
    with connection.cursor() as cur:
        filtro_p = []
        params_p = []
        if periodo_id:
            filtro_p.append("c.id_periodo_academico_id = %s")
            params_p.append(periodo_id)
        if curso_id:
            filtro_p.append("c.id = %s")
            params_p.append(curso_id)
        where = ("WHERE " + " AND ".join(filtro_p)) if filtro_p else ""

        cur.execute(
            f"""
            SELECT
                p.id, p.nombre, p.estado, p.fecha_inicio, p.fecha_fin_estimada,
                c.nombre AS curso_nombre,
                vpp.porcentaje_progreso,
                vpp.total_actividades,
                vpp.actividades_completadas,
                vep.total_entregables,
                vep.aprobados AS entregables_aprobados,
                vep.tasa_entrega_tiempo_pct
            FROM proyecto p
            JOIN curso c ON c.id = p.id_curso_id
            LEFT JOIN vista_progreso_proyecto vpp ON vpp.id_proyecto = p.id
            LEFT JOIN vista_entregables_proyecto vep ON vep.proyecto_id = p.id
            {where}
            ORDER BY vpp.porcentaje_progreso DESC NULLS LAST
            """,
            params_p,
        )
        proyectos = _fetchall_as_dicts(cur)

    # ── 4. Estudiantes en riesgo por curso ──
    riesgo_por_curso = _indicadores_estudiantes_riesgo_por_curso(
        periodo_id=periodo_id, curso_id=curso_id
    )

    # ── 5. Distribución de avance (rangos) ──
    with connection.cursor() as cur:
        filtro_d = []
        params_d = []
        if periodo_id:
            filtro_d.append("c.id_periodo_academico_id = %s")
            params_d.append(periodo_id)
        if curso_id:
            filtro_d.append("c.id = %s")
            params_d.append(curso_id)
        where_d = ("AND " + " AND ".join(filtro_d)) if filtro_d else ""

        cur.execute(
            f"""
            SELECT
                COUNT(*) FILTER (WHERE vae.nota_promedio_5 < 2.0)              AS rango_0_2,
                COUNT(*) FILTER (WHERE vae.nota_promedio_5 BETWEEN 2.0 AND 2.9) AS rango_2_3,
                COUNT(*) FILTER (WHERE vae.nota_promedio_5 BETWEEN 3.0 AND 3.9) AS rango_3_4,
                COUNT(*) FILTER (WHERE vae.nota_promedio_5 >= 4.0)              AS rango_4_5,
                ROUND(AVG(vae.nota_promedio_5)::numeric, 2)                     AS nota_promedio_global
            FROM vista_avance_estudiante_proyecto vae
            JOIN proyecto p ON p.id = vae.proyecto_id
            JOIN curso c    ON c.id = p.id_curso_id
            WHERE 1=1 {where_d}
            """,
            params_d,
        )
        distribucion = _fetchall_as_dicts(cur)
        distribucion_notas = distribucion[0] if distribucion else {}

    return {
        'filtros_aplicados': {
            'periodo_id': periodo_id,
            'curso_id': curso_id,
        },
        'resumen_periodo': resumen_periodo,
        'distribucion_notas': distribucion_notas,
        'proyectos': proyectos,
        'docentes_activos': docentes_activos,
        'estudiantes_riesgo_por_curso': riesgo_por_curso,
    }


def indicadores_tendencia(n_periodos=4):
    """
    Evolución de indicadores clave comparando los últimos N periodos.
    """
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM vista_indicadores_periodo
            ORDER BY periodo_inicio DESC
            LIMIT %s
            """,
            [n_periodos],
        )
        periodos = _fetchall_as_dicts(cur)

    if not periodos:
        return {'periodos': [], 'tendencias': {}}

    def _tendencia(campo):
        vals = [p.get(campo) for p in periodos if p.get(campo) is not None]
        if len(vals) < 2:
            return None
        try:
            return round(float(vals[0]) - float(vals[-1]), 2)
        except (TypeError, ValueError):
            return None

    tendencias = {
        'avance_proyectos': _tendencia('avance_promedio_proyectos_pct'),
        'tasa_aprobacion': _tendencia('tasa_aprobacion_pct'),
        'total_estudiantes': _tendencia('total_estudiantes'),
        'proyectos_completados': _tendencia('proyectos_completados'),
    }

    return {
        'n_periodos': len(periodos),
        'periodos': list(reversed(periodos)),
        'tendencias': tendencias,
    }
