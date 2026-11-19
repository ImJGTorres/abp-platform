"""
Datos propios de las specs de Cypress que no tienen seed de HU (hu001, hu002, hu003,
hu036 y parametros). Así las pruebas no usan ni modifican datos reales.

Crea (idempotente):
- Un usuario por rol: cypress.<rol>@example.com / Test1234 (la contraseña se fija en cada
  ejecución por si alguien la cambió).
- El rol '[CYPRESS] Rol con usuarios', asignado a cypress.estudiante, para comprobar que no
  se puede eliminar un rol con usuarios activos (hu003 CP-04).
- El período inactivo '1991-1' con un curso, para comprobar que no se puede eliminar un
  período con cursos (hu036). Fechas en el pasado para no confundirse con el período actual.

Con --limpiar borra los usuarios que crea hu001 (cypress.registro.*@example.com).

Uso: python manage.py seed_cypress [--limpiar]
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.usuarios.seguridad_demo import agregar_argumento_forzar, exigir_entorno_de_desarrollo

PASSWORD = 'Test1234'
ROLES = ('administrador', 'director', 'docente', 'lider_equipo', 'estudiante')
NOMBRE_ROL_CON_USUARIOS = '[CYPRESS] Rol con usuarios'
NOMBRE_PERIODO_CON_CURSOS = '1991-1'


class Command(BaseCommand):
    help = 'Crea los usuarios y datos de prueba de las specs de Cypress (o limpia los de hu001).'

    def add_arguments(self, parser):
        agregar_argumento_forzar(parser)
        parser.add_argument('--limpiar', action='store_true',
                            help='Borra los usuarios de prueba creados por hu001.')

    @transaction.atomic
    def handle(self, *args, **options):
        exigir_entorno_de_desarrollo(options)
        from apps.usuarios.models import Usuario

        if options['limpiar']:
            borrados, _ = Usuario.objects.filter(
                correo__startswith='cypress.registro.', correo__endswith='@example.com',
            ).delete()
            self.stdout.write(self.style.SUCCESS(f'Listo. Registros de prueba borrados: {borrados}.'))
            return

        from apps.configuracion.models import PeriodoAcademico
        from apps.cursos.models import Curso
        from apps.roles.models import Rol
        from apps.usuarios.models import UsuarioRol

        usuarios = {}
        for rol in ROLES:
            usuario, _ = Usuario.objects.get_or_create(
                correo=f'cypress.{rol}@example.com',
                defaults={'nombre': 'Cypress', 'apellido': rol.replace('_', ' ').title(),
                          'tipo_rol': rol},
            )
            usuario.tipo_rol = rol
            usuario.estado = Usuario.Estado.ACTIVO
            usuario.set_password(PASSWORD)
            usuario.save(update_fields=['tipo_rol', 'estado', 'password'])
            usuarios[rol] = usuario

        rol_con_usuarios, _ = Rol.objects.get_or_create(
            nombre=NOMBRE_ROL_CON_USUARIOS,
            defaults={'descripcion': 'Rol de prueba de Cypress (tiene un usuario asignado)'},
        )
        UsuarioRol.objects.get_or_create(usuario=usuarios['estudiante'], rol=rol_con_usuarios)

        periodo, _ = PeriodoAcademico.objects.get_or_create(
            nombre=NOMBRE_PERIODO_CON_CURSOS,
            defaults={'fecha_inicio': date(1991, 1, 15), 'fecha_fin': date(1991, 6, 15),
                      'estado': PeriodoAcademico.Estado.INACTIVO},
        )
        Curso.objects.get_or_create(
            codigo='CYPRESS-1991', id_periodo_academico=periodo,
            defaults={'nombre': '[CYPRESS] Curso del período 1991-1',
                      'id_docente': usuarios['docente'], 'estado': Curso.Estado.ACTIVO},
        )

        self.stdout.write(self.style.SUCCESS(
            f'Listo. Usuarios cypress.<rol>@example.com / {PASSWORD}, '
            f"rol '{NOMBRE_ROL_CON_USUARIOS}' y período '{NOMBRE_PERIODO_CON_CURSOS}' con un curso."
        ))
