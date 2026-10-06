from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.authentication import UsuarioJWTAuthentication

from .models import Anuncio
from .serializers import AnuncioSerializer
from .services import publicar_anuncio

ROLES_SIN_PUBLICAR = ('estudiante', 'lider_equipo')
ROLES_GLOBALES = ('director', 'administrador')
CAMPOS_EDITABLES = ('titulo', 'mensaje', 'fecha_publicacion')


class MuroAnunciosView(APIView):
    """
    Muro de anuncios de un curso o de un proyecto (HU-039).

        GET  /api/cursos/<curso_id>/anuncios/        GET  /api/proyectos/<proyecto_id>/anuncios/
        POST /api/cursos/<curso_id>/anuncios/        POST /api/proyectos/<proyecto_id>/anuncios/

    GET: integrantes del curso/proyecto, director o administrador (otro → 403).
    POST: docente del curso, director o administrador; estudiante/líder → 403 (RN-001).
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def _muro(self, curso_id=None, proyecto_id=None):
        """(curso, proyecto) del muro, o None si no existe."""
        from apps.cursos.models import Curso, Proyecto

        if proyecto_id is not None:
            proyecto = Proyecto.objects.select_related('id_curso').filter(id=proyecto_id).first()
            return (proyecto.id_curso, proyecto) if proyecto else None
        curso = Curso.objects.filter(id=curso_id).first()
        return (curso, None) if curso else None

    @staticmethod
    def _es_docente_del_curso(usuario, curso):
        return usuario.tipo_rol == 'docente' and curso is not None and curso.id_docente_id == usuario.id

    def _puede_ver(self, usuario, curso, proyecto):
        from apps.cursos.models import CursoEstudiante
        from apps.equipos.models import MiembroEquipo

        if usuario.tipo_rol in ROLES_GLOBALES or self._es_docente_del_curso(usuario, curso):
            return True
        if curso and CursoEstudiante.objects.filter(curso=curso, estudiante=usuario, estado='activo').exists():
            return True
        miembros = MiembroEquipo.objects.filter(usuario=usuario, estado='activo')
        if proyecto:
            return miembros.filter(equipo__proyecto=proyecto).exists()
        return miembros.filter(equipo__proyecto__id_curso=curso).exists()

    def get(self, request, curso_id=None, proyecto_id=None):
        muro = self._muro(curso_id, proyecto_id)
        if muro is None:
            return Response({'detail': 'Curso o proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        curso, proyecto = muro
        if not self._puede_ver(request.user, curso, proyecto):
            return Response({'detail': 'No tienes acceso a este muro.'}, status=status.HTTP_403_FORBIDDEN)

        anuncios = (Anuncio.objects.filter(id_proyecto=proyecto) if proyecto
                    else Anuncio.objects.filter(id_curso=curso, id_proyecto__isnull=True))
        anuncios = anuncios.select_related('id_autor').order_by('-fecha_publicacion', '-id')
        return Response(AnuncioSerializer(anuncios, many=True).data)

    def post(self, request, curso_id=None, proyecto_id=None):
        usuario = request.user
        if usuario.tipo_rol in ROLES_SIN_PUBLICAR:  # RN-001: antes de validar los datos
            return Response({'detail': 'No tienes permiso para publicar en este muro'},
                            status=status.HTTP_403_FORBIDDEN)

        muro = self._muro(curso_id, proyecto_id)
        if muro is None:
            return Response({'detail': 'Curso o proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        curso, proyecto = muro
        if usuario.tipo_rol not in ROLES_GLOBALES and not self._es_docente_del_curso(usuario, curso):
            return Response({'detail': 'No tienes permiso para publicar en este muro'},
                            status=status.HTTP_403_FORBIDDEN)

        # El curso/proyecto sale de la URL, nunca del body
        datos = {c: request.data[c] for c in CAMPOS_EDITABLES if c in request.data}
        if proyecto:
            datos['id_proyecto'] = proyecto.id
        else:
            datos['id_curso'] = curso.id
        serializer = AnuncioSerializer(data=datos, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        anuncio = publicar_anuncio(usuario, serializer.validated_data, request)
        return Response(AnuncioSerializer(anuncio).data, status=status.HTTP_201_CREATED)
