"""
Datos de demostración para la prueba de aceptación de HU-040 (SCRUM-536):
calendario unificado, detalle de evento y recordatorio de vencimiento a 48 h.

Idempotente (get_or_create): se puede correr varias veces sin duplicar datos.
Todo lo creado se marca con el prefijo '[DEMO HU-040]' para identificarlo
fácilmente en la base compartida.
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

PREFIJO = '[DEMO HU-040]'
CORREO_ESTUDIANTE = 'jesusgabrieltd@ufps.edu.co'
PASSWORD_ESTUDIANTE = 'Test1234'


class Command(BaseCommand):
    help = 'Crea (o reutiliza) curso, proyecto, equipo y eventos de calendario para la prueba de aceptación de HU-040.'

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.configuracion.models import ParametroSistema, PeriodoAcademico
        from apps.cursos.models import Actividad, AvanceActividad, Curso, FaseProyecto, HitoProyecto, Proyecto
        from apps.equipos.models import Equipo, MiembroEquipo
        from apps.usuarios.models import Usuario

        hoy = date.today()

        ParametroSistema.objects.get_or_create(
            clave='max_estudiantes_por_equipo',
            defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'},
        )

        periodo = PeriodoAcademico.objects.filter(estado=PeriodoAcademico.Estado.ACTIVO).first()
        if periodo is None:
            periodo, _ = PeriodoAcademico.objects.get_or_create(
                nombre=f'{PREFIJO} Periodo',
                defaults={'fecha_inicio': hoy - timedelta(days=60),
                          'fecha_fin': hoy + timedelta(days=120)},
            )

        docente, _ = Usuario.objects.get_or_create(
            correo='demo.docente.hu040@ufps.edu.co',
            defaults={'nombre': 'Docente', 'apellido': 'Demo HU-040',
                      'tipo_rol': Usuario.TipoRol.DOCENTE},
        )

        estudiante, creado = Usuario.objects.get_or_create(
            correo=CORREO_ESTUDIANTE,
            defaults={'nombre': 'Jesus Gabriel', 'apellido': 'Estudiante Demo',
                      'tipo_rol': Usuario.TipoRol.ESTUDIANTE},
        )
        estudiante.set_password(PASSWORD_ESTUDIANTE)
        estudiante.save(update_fields=['password'])

        curso1, _ = Curso.objects.get_or_create(
            codigo=f'DEMO040-IS', id_periodo_academico=periodo,
            defaults={'nombre': f'{PREFIJO} Ingeniería de Software', 'id_docente': docente,
                      'estado': Curso.Estado.ACTIVO},
        )
        curso2, _ = Curso.objects.get_or_create(
            codigo=f'DEMO040-BD', id_periodo_academico=periodo,
            defaults={'nombre': f'{PREFIJO} Bases de Datos', 'id_docente': docente,
                      'estado': Curso.Estado.ACTIVO},
        )

        proyecto1, _ = Proyecto.objects.get_or_create(
            id_curso=curso1, nombre=f'{PREFIJO} Proyecto Ingeniería de Software',
            defaults={'fecha_inicio': hoy - timedelta(days=30),
                      'fecha_fin_estimada': hoy + timedelta(days=60),
                      'estado': Proyecto.Estado.EN_EJECUCION},
        )
        proyecto2, _ = Proyecto.objects.get_or_create(
            id_curso=curso2, nombre=f'{PREFIJO} Proyecto Bases de Datos',
            defaults={'fecha_inicio': hoy - timedelta(days=30),
                      'fecha_fin_estimada': hoy + timedelta(days=60),
                      'estado': Proyecto.Estado.EN_EJECUCION},
        )

        fase1, _ = FaseProyecto.objects.get_or_create(
            id_proyecto=proyecto1, orden=1,
            defaults={'nombre': 'Desarrollo', 'fecha_inicio': hoy - timedelta(days=10),
                      'fecha_fin': hoy + timedelta(days=30),
                      'estado': FaseProyecto.Estado.EN_PROGRESO},
        )
        fase2, _ = FaseProyecto.objects.get_or_create(
            id_proyecto=proyecto2, orden=1,
            defaults={'nombre': 'Modelado', 'fecha_inicio': hoy - timedelta(days=10),
                      'fecha_fin': hoy + timedelta(days=30),
                      'estado': FaseProyecto.Estado.EN_PROGRESO},
        )

        equipo1, _ = Equipo.objects.get_or_create(
            proyecto=proyecto1, nombre=f'{PREFIJO} Equipo IS', defaults={'cupo_maximo': 6},
        )
        equipo2, _ = Equipo.objects.get_or_create(
            proyecto=proyecto2, nombre=f'{PREFIJO} Equipo BD', defaults={'cupo_maximo': 6},
        )
        MiembroEquipo.objects.get_or_create(
            equipo=equipo1, usuario=estudiante, defaults={'rol_interno': 'desarrollador'},
        )
        MiembroEquipo.objects.get_or_create(
            equipo=equipo2, usuario=estudiante, defaults={'rol_interno': 'desarrollador'},
        )

        # Curso 1: una actividad vencida (equipo) y una próxima en 48h (responsable directo,
        # dispara el recordatorio por correo real a jesusgabrieltd@ufps.edu.co).
        act_vencida, _ = Actividad.objects.get_or_create(
            id_fase=fase1, nombre=f'{PREFIJO} Entrega de prototipo',
            defaults={'fecha_limite': hoy - timedelta(days=1), 'id_equipo_asignado': equipo1},
        )
        act_proxima, _ = Actividad.objects.get_or_create(
            id_fase=fase1, nombre=f'{PREFIJO} Documentar API',
            defaults={'fecha_limite': hoy + timedelta(days=1), 'id_responsable': estudiante,
                      'id_equipo_asignado': equipo1},
        )
        AvanceActividad.objects.get_or_create(
            id_actividad=act_proxima, id_usuario=estudiante,
            defaults={'descripcion': 'Avance inicial de la documentación', 'porcentaje_completado': 40},
        )
        HitoProyecto.objects.get_or_create(
            id_proyecto=proyecto1, nombre=f'{PREFIJO} Revisión de avance',
            defaults={'fecha_inicio': hoy + timedelta(days=5), 'fecha_fin': hoy + timedelta(days=5),
                      'tipo': HitoProyecto.Tipo.REVISION},
        )

        # Curso 2: una actividad normal (equipo) y un hito de entrega próximo.
        Actividad.objects.get_or_create(
            id_fase=fase2, nombre=f'{PREFIJO} Modelo ER final',
            defaults={'fecha_limite': hoy + timedelta(days=6), 'id_equipo_asignado': equipo2},
        )
        HitoProyecto.objects.get_or_create(
            id_proyecto=proyecto2, nombre=f'{PREFIJO} Entrega final',
            defaults={'fecha_inicio': hoy + timedelta(days=2), 'fecha_fin': hoy + timedelta(days=2),
                      'tipo': HitoProyecto.Tipo.ENTREGA},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Estudiante: {CORREO_ESTUDIANTE} / {PASSWORD_ESTUDIANTE} "
            f"({'creado' if creado else 'ya existía'}). Cursos: {curso1.nombre}, {curso2.nombre}."
        ))
