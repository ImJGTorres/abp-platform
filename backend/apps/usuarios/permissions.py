from rest_framework.permissions import BasePermission

from apps.roles.models import Permiso, Rol, RolPermiso
from apps.usuarios.models import Usuario


# ---------------------------------------------------------------------------
# Utilidad interna compartida por las permission classes de nivel objeto
# ---------------------------------------------------------------------------

def _usuario_tiene_acceso_curso(usuario, curso):
    """Verifica si un usuario tiene acceso a un curso según su rol.

    Reglas de negocio:
        - Administrador: acceso irrestricto.
        - Docente: solo si es el propietario del curso (id_docente).
        - Estudiante / lider_equipo: solo si pertenece activamente a algún equipo
          del curso.
        - Cualquier otro rol: acceso denegado.

    Args:
        usuario: Instancia de Usuario autenticado.
        curso:   Instancia de Curso a verificar.

    Returns:
        bool: True si el usuario tiene acceso, False en caso contrario.
    """
    # Importación local para evitar dependencias circulares entre apps
    from apps.equipos.models import MiembroEquipo

    tipo_rol = getattr(usuario, 'tipo_rol', None)

    if tipo_rol == 'administrador':
        return True
    if tipo_rol == 'docente':
        return curso.id_docente_id == usuario.pk
    if tipo_rol in ('estudiante', 'lider_equipo'):
        return MiembroEquipo.objects.filter(
            equipo__proyecto__id_curso=curso,
            usuario=usuario,
            estado='activo',
        ).exists()
    return False


def TienePermiso(codigo_permiso):
    """
    Factory que retorna una clase de permiso DRF.
    Verifica si el rol del usuario tiene el permiso específico.
    """

    class TienePermisoClass(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            if not user or not isinstance(user, Usuario) or not user.tipo_rol:
                return False

            return RolPermiso.objects.filter(
                rol__nombre__iexact=user.tipo_rol,
                permiso__codigo=codigo_permiso
            ).exists()

    return TienePermisoClass


class EsAdministrador(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'administrador'."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user is not None
            and isinstance(user, Usuario)
            and user.tipo_rol == Usuario.TipoRol.ADMINISTRADOR
            and user.estado == Usuario.Estado.ACTIVO
        )


class EsDocente(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'docente'."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user is not None
            and isinstance(user, Usuario)
            and user.tipo_rol == Usuario.TipoRol.DOCENTE
            and user.estado == Usuario.Estado.ACTIVO
        )


# ---------------------------------------------------------------------------
# Permission classes de nivel objeto (object-level permissions)
# ---------------------------------------------------------------------------

class EsParticipanteCurso(BasePermission):
    """Permite acceso a usuarios que participan activamente en un curso.

    Evalúa el permiso a nivel de objeto (has_object_permission). El objeto
    esperado es una instancia de Curso.

    Reglas de negocio:
        - Administrador: acceso siempre permitido.
        - Docente: solo si es el propietario del curso.
        - Estudiante / lider_equipo: solo si pertenece activamente a algún
          equipo cuyo proyecto esté vinculado al curso.
        - Cualquier otro rol: acceso denegado.

    Uso en vistas:
        permission_classes = [IsAuthenticated, EsParticipanteCurso]

        # Dentro del método:
        self.check_object_permissions(request, curso)
    """

    def has_permission(self, request, view):
        """Requiere autenticación básica antes de la verificación por objeto."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Verifica acceso al objeto Curso.

        Args:
            request: Solicitud HTTP autenticada.
            view:    Vista DRF que invoca la verificación.
            obj:     Instancia de Curso a verificar.

        Returns:
            bool: True si el usuario tiene acceso al curso.
        """
        return _usuario_tiene_acceso_curso(request.user, obj)


class EsParticipanteProyecto(BasePermission):
    """Permite acceso a usuarios que participan activamente en un proyecto.

    Evalúa el permiso a nivel de objeto (has_object_permission). El objeto
    esperado es una instancia de Proyecto (con id_curso seleccionado).

    Reglas de negocio:
        - Administrador: acceso siempre permitido.
        - Docente: solo si es el propietario del curso al que pertenece el proyecto.
        - Estudiante / lider_equipo: solo si pertenece activamente a algún
          equipo del curso del proyecto.
        - Cualquier otro rol: acceso denegado.

    Uso en vistas:
        permission_classes = [IsAuthenticated, EsParticipanteProyecto]

        # Dentro del método:
        self.check_object_permissions(request, proyecto)
    """

    def has_permission(self, request, view):
        """Requiere autenticación básica antes de la verificación por objeto."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Verifica acceso al objeto Proyecto.

        Args:
            request: Solicitud HTTP autenticada.
            view:    Vista DRF que invoca la verificación.
            obj:     Instancia de Proyecto a verificar (debe tener id_curso accesible).

        Returns:
            bool: True si el usuario tiene acceso al proyecto.
        """
        return _usuario_tiene_acceso_curso(request.user, obj.id_curso)
