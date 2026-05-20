import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.authentication import UsuarioJWTAuthentication

from .services import calcular_rendimiento_estudiante, get_estudiantes_bajo_rendimiento

logger = logging.getLogger(__name__)


class BajoRendimientoView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request):
        usuario = request.user
        if usuario.tipo_rol not in ('director', 'docente', 'administrador'):
            return Response(
                {'error': 'No tienes permiso para acceder a este reporte.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        curso_id = request.query_params.get('curso_id')
        proyecto_id = request.query_params.get('proyecto_id')
        periodo_id = request.query_params.get('periodo_id')

        try:
            curso_id = int(curso_id) if curso_id else None
            proyecto_id = int(proyecto_id) if proyecto_id else None
            periodo_id = int(periodo_id) if periodo_id else None
        except ValueError:
            return Response(
                {'error': 'Los parámetros de filtro deben ser enteros.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            estudiantes = get_estudiantes_bajo_rendimiento(
                curso_id=curso_id,
                proyecto_id=proyecto_id,
                periodo_id=periodo_id,
            )

            try:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.ACCESS,
                    modulo='reportes',
                    descripcion=(
                        f"Consulta reporte bajo rendimiento. "
                        f"Filtros: curso={curso_id}, proyecto={proyecto_id}, periodo={periodo_id}"
                    ),
                )
            except Exception:
                logger.warning("No se pudo registrar en bitácora la consulta de bajo rendimiento")

            return Response({'total': len(estudiantes), 'estudiantes': estudiantes},
                            status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error en reporte bajo rendimiento: {e}")
            return Response(
                {'error': 'Error interno al calcular el reporte.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RendimientoEstudianteView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, estudiante_id):
        from apps.usuarios.models import Usuario

        usuario = request.user
        rol = usuario.tipo_rol

        if rol == 'estudiante' and usuario.id != estudiante_id:
            return Response(
                {'error': 'Solo puedes consultar tu propio rendimiento.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if rol not in ('director', 'docente', 'administrador', 'estudiante'):
            return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            estudiante = Usuario.objects.get(id=estudiante_id, tipo_rol='estudiante')
        except Usuario.DoesNotExist:
            return Response({'error': 'Estudiante no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        curso_id = request.query_params.get('curso_id')
        proyecto_id = request.query_params.get('proyecto_id')

        try:
            curso_id = int(curso_id) if curso_id else None
            proyecto_id = int(proyecto_id) if proyecto_id else None
        except ValueError:
            return Response({'error': 'Filtros inválidos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            indicadores = calcular_rendimiento_estudiante(
                estudiante_id, proyecto_id=proyecto_id, curso_id=curso_id
            )
            comparativo = _calcular_promedio_grupo(curso_id=curso_id, proyecto_id=proyecto_id)

            try:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.ACCESS,
                    modulo='reportes',
                    descripcion=f"Consulta rendimiento estudiante id={estudiante_id}",
                )
            except Exception:
                logger.warning("No se pudo registrar en bitácora")

            return Response({
                'estudiante': {
                    'id': estudiante.id,
                    'nombre': estudiante.nombre,
                    'apellido': estudiante.apellido,
                    'correo': estudiante.correo,
                    'codigo_estudiante': estudiante.codigo_estudiante,
                },
                'indicadores': indicadores,
                'comparativo_grupo': comparativo,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error calculando rendimiento de estudiante {estudiante_id}: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── HU-031: Reportes por proyecto ────────────────────────────────────────────

ROLES_DIRECTOR = ('director', 'docente', 'administrador')


class ReporteProyectoView(APIView):
    """GET /api/reportes/proyecto/<proyecto_id>/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, proyecto_id):
        usuario = request.user
        if usuario.tipo_rol not in ROLES_DIRECTOR:
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.reportes.services import reporte_proyecto
        try:
            data = reporte_proyecto(proyecto_id)
        except Exception as e:
            logger.error(f"Error reporte proyecto {proyecto_id}: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data is None:
            return Response({'error': 'Proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta reporte proyecto id={proyecto_id}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


class ReporteCursoView(APIView):
    """GET /api/reportes/curso/<curso_id>/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, curso_id):
        usuario = request.user
        if usuario.tipo_rol not in ROLES_DIRECTOR:
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.reportes.services import reporte_curso
        try:
            data = reporte_curso(curso_id)
        except Exception as e:
            logger.error(f"Error reporte curso {curso_id}: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data is None:
            return Response({'error': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta reporte curso id={curso_id}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


# ── HU-032 ─────────────────────────────────────────────────────────────────

class ReporteEstudianteProyectoView(APIView):
    """GET /api/reportes/estudiante/<estudiante_id>/proyecto/<proyecto_id>/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, estudiante_id, proyecto_id):
        usuario = request.user
        rol = usuario.tipo_rol
        uid = usuario.id

        if rol == 'estudiante' and uid != estudiante_id:
            return Response({'error': 'Solo puedes ver tu propio reporte.'}, status=status.HTTP_403_FORBIDDEN)
        if rol not in ('director', 'docente', 'administrador', 'estudiante'):
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.reportes.services import reporte_estudiante_proyecto
        try:
            data = reporte_estudiante_proyecto(estudiante_id, proyecto_id)
        except Exception as e:
            logger.error(f"Error reporte estudiante {estudiante_id} proyecto {proyecto_id}: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data is None:
            return Response({'error': 'Estudiante o proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta reporte estudiante id={estudiante_id} proyecto id={proyecto_id}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


class ReporteEquipoEstudiantesView(APIView):
    """GET /api/reportes/equipo/<equipo_id>/estudiantes/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, equipo_id):
        usuario = request.user
        if usuario.tipo_rol not in ROLES_DIRECTOR:
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.reportes.services import reporte_equipo_estudiantes
        try:
            data = reporte_equipo_estudiantes(equipo_id)
        except Exception as e:
            logger.error(f"Error reporte equipo {equipo_id}: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data is None:
            return Response({'error': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta reporte equipo id={equipo_id}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


# ── HU-033 ─────────────────────────────────────────────────────────────────

class IndicadoresDashboardView(APIView):
    """GET /api/reportes/indicadores/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request):
        usuario = request.user
        if usuario.tipo_rol not in ('director', 'administrador'):
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        periodo_id = request.query_params.get('periodo_id')
        curso_id = request.query_params.get('curso_id')

        try:
            periodo_id = int(periodo_id) if periodo_id else None
            curso_id = int(curso_id) if curso_id else None
        except ValueError:
            return Response({'error': 'Parámetros inválidos.'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.reportes.services import indicadores_dashboard
        try:
            data = indicadores_dashboard(periodo_id=periodo_id, curso_id=curso_id)
        except Exception as e:
            logger.error(f"Error dashboard indicadores: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta dashboard indicadores. periodo={periodo_id} curso={curso_id}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


class IndicadoresTendenciaView(APIView):
    """GET /api/reportes/indicadores/tendencia/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request):
        usuario = request.user
        if usuario.tipo_rol not in ('director', 'administrador'):
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            n = int(request.query_params.get('n_periodos', 4))
            n = max(2, min(n, 10))
        except ValueError:
            n = 4

        from apps.reportes.services import indicadores_tendencia
        try:
            data = indicadores_tendencia(n_periodos=n)
        except Exception as e:
            logger.error(f"Error tendencia indicadores: {e}")
            return Response({'error': 'Error interno.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='reportes',
                descripcion=f"Consulta tendencia indicadores n={n}",
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


def _calcular_promedio_grupo(curso_id=None, proyecto_id=None):
    from apps.usuarios.models import Usuario
    from apps.equipos.models import MiembroEquipo

    estudiantes_qs = Usuario.objects.filter(tipo_rol='estudiante', estado='activo')
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

    if not estudiantes_qs.exists():
        return {'nota_promedio': 0, 'pct_actividades_incumplidas': 0}

    notas = []
    pcts = []
    for est in estudiantes_qs:
        ind = calcular_rendimiento_estudiante(est.id, proyecto_id=proyecto_id, curso_id=curso_id)
        notas.append(ind['nota_promedio'])
        pcts.append(ind['porcentaje_actividades_incumplidas'])

    return {
        'nota_promedio': round(sum(notas) / len(notas), 2),
        'pct_actividades_incumplidas': round(sum(pcts) / len(pcts), 2),
    }
