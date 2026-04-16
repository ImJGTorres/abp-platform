from django.core.management.base import BaseCommand
from apps.roles.models import Rol, Permiso, RolPermiso


class Command(BaseCommand):
    help = 'Seed roles and permissions base data'

    def handle(self, *args, **options):
        roles_data = [
            {'nombre': 'administrador', 'descripcion': 'Acceso total al sistema'},
            {'nombre': 'director', 'descripcion': 'Supervisión académica y reportes'},
            {'nombre': 'docente', 'descripcion': 'Gestión de cursos y proyectos'},
            {'nombre': 'lider_equipo', 'descripcion': 'Coordinación de actividades del equipo'},
            {'nombre': 'estudiante', 'descripcion': 'Participación en proyectos y entrega de avances'},
        ]

        permisos_data = [
            {'modulo': 'usuarios', 'accion': 'ver'},
            {'modulo': 'usuarios', 'accion': 'crear'},
            {'modulo': 'usuarios', 'accion': 'editar'},
            {'modulo': 'usuarios', 'accion': 'eliminar'},
            {'modulo': 'roles', 'accion': 'ver'},
            {'modulo': 'roles', 'accion': 'crear'},
            {'modulo': 'roles', 'accion': 'editar'},
            {'modulo': 'roles', 'accion': 'eliminar'},
            {'modulo': 'periodos', 'accion': 'ver'},
            {'modulo': 'periodos', 'accion': 'crear'},
            {'modulo': 'periodos', 'accion': 'editar'},
            {'modulo': 'periodos', 'accion': 'eliminar'},
            {'modulo': 'cursos', 'accion': 'ver'},
            {'modulo': 'cursos', 'accion': 'crear'},
            {'modulo': 'cursos', 'accion': 'editar'},
            {'modulo': 'cursos', 'accion': 'eliminar'},
            {'modulo': 'equipos', 'accion': 'ver'},
            {'modulo': 'equipos', 'accion': 'crear'},
            {'modulo': 'equipos', 'accion': 'editar'},
            {'modulo': 'equipos', 'accion': 'eliminar'},
            {'modulo': 'entregables', 'accion': 'ver'},
            {'modulo': 'entregables', 'accion': 'crear'},
            {'modulo': 'entregables', 'accion': 'editar'},
            {'modulo': 'entregables', 'accion': 'validar'},
            {'modulo': 'evaluacion', 'accion': 'ver'},
            {'modulo': 'evaluacion', 'accion': 'crear'},
            {'modulo': 'evaluacion', 'accion': 'editar'},
            {'modulo': 'reportes', 'accion': 'ver'},
            {'modulo': 'reportes', 'accion': 'exportar'},
            {'modulo': 'bitacora', 'accion': 'ver'},
        ]

        permisos_asignados = {
            'administrador': [
                'usuarios.ver', 'usuarios.crear', 'usuarios.editar', 'usuarios.eliminar',
                'roles.ver', 'roles.crear', 'roles.editar', 'roles.eliminar',
                'periodos.ver', 'periodos.crear', 'periodos.editar', 'periodos.eliminar',
                'cursos.ver', 'cursos.crear', 'cursos.editar', 'cursos.eliminar',
                'equipos.ver', 'equipos.crear', 'equipos.editar', 'equipos.eliminar',
                'entregables.ver', 'entregables.crear', 'entregables.editar', 'entregables.validar',
                'evaluacion.ver', 'evaluacion.crear', 'evaluacion.editar',
                'reportes.ver', 'reportes.exportar',
                'bitacora.ver',
            ],
            'director': [
                'periodos.ver', 'periodos.crear', 'periodos.editar', 'periodos.eliminar',
                'cursos.ver',
                'equipos.ver',
                'reportes.ver', 'reportes.exportar',
                'bitacora.ver',
                'usuarios.ver',
            ],
            'docente': [
                'cursos.ver', 'cursos.crear', 'cursos.editar', 'cursos.eliminar',
                'equipos.ver', 'equipos.crear', 'equipos.editar', 'equipos.eliminar',
                'entregables.ver', 'entregables.crear', 'entregables.editar', 'entregables.validar',
                'evaluacion.ver', 'evaluacion.crear', 'evaluacion.editar',
                'reportes.ver',
            ],
            'lider_equipo': [
                'equipos.ver', 'equipos.editar',
                'entregables.ver', 'entregables.crear', 'entregables.editar', 'entregables.validar',
                'evaluacion.ver',
            ],
            'estudiante': [
                'cursos.ver',
                'equipos.ver',
                'entregables.ver', 'entregables.crear',
                'evaluacion.ver',
            ],
        }

        roles_created = 0
        roles_existed = 0

        for rol_data in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults={
                    'descripcion': rol_data['descripcion'],
                    'estado': 'activo',
                }
            )
            if created:
                roles_created += 1
            else:
                roles_existed += 1

        permisos_created = 0
        permisos_existed = 0

        for perm_data in permisos_data:
            codigo = f'{perm_data["modulo"]}.{perm_data["accion"]}'
            permiso, created = Permiso.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'modulo': perm_data['modulo'],
                    'descripcion': f'{perm_data["accion"].capitalize()} {perm_data["modulo"]}',
                }
            )
            if created:
                permisos_created += 1
            else:
                permisos_existed += 1

        asignaciones_created = 0
        asignaciones_existed = 0

        for rol_nombre, permisos_codigos in permisos_asignados.items():
            rol = Rol.objects.get(nombre=rol_nombre)
            for codigo in permisos_codigos:
                permiso = Permiso.objects.get(codigo=codigo)
                _, created = RolPermiso.objects.get_or_create(
                    rol=rol,
                    permiso=permiso
                )
                if created:
                    asignaciones_created += 1
                else:
                    asignaciones_existed += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n=== RESUMEN ===\n'
            f'Roles: {roles_created} creados, {roles_existed} ya existentes\n'
            f'Permisos: {permisos_created} creados, {permisos_existed} ya existentes\n'
            f'Asignaciones: {asignaciones_created} creadas, {asignaciones_existed} ya existentes'
        ))