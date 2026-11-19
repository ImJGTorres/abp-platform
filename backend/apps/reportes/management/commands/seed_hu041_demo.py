"""
Datos de demostración para la prueba de aceptación de HU-041 (SCRUM-550):
semáforo personal del estudiante (verde) y un director con acceso al panel
de riesgo para comparar el color del mismo estudiante.

Crea además un estudiante en 'rojo' propio de la demo (2 actividades vencidas sin
completar, nota 1.0) para que las pruebas no dependan de datos reales que cambian.

Idempotente (get_or_create / update_or_create). Todo lo creado se marca con '[DEMO HU-041]'.
"""
from apps.usuarios.seguridad_demo import agregar_argumento_forzar, exigir_entorno_de_desarrollo
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

PREFIJO = '[DEMO HU-041]'
CORREO_ESTUDIANTE_VERDE = 'estudiante.verde.hu041@ufps.edu.co'
CORREO_ESTUDIANTE_ROJO = 'estudiante.rojo.hu041@ufps.edu.co'
CORREO_DIRECTOR = 'director.hu041@ufps.edu.co'
PASSWORD = 'Test1234'


class Command(BaseCommand):
    help = 'Crea (o reutiliza) un estudiante en verde y un director demo para la prueba de aceptación de HU-041.'

    def add_arguments(self, parser):
        agregar_argumento_forzar(parser)

    @transaction.atomic
    def handle(self, *args, **options):
        exigir_entorno_de_desarrollo(options)
        from apps.configuracion.models import ParametroSistema, PeriodoAcademico
        from apps.cursos.models import Actividad, AvanceActividad, Curso, FaseProyecto, Proyecto
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

        director, creado_director = Usuario.objects.get_or_create(
            correo=CORREO_DIRECTOR,
            defaults={'nombre': 'Director', 'apellido': 'Demo HU-041',
                      'tipo_rol': Usuario.TipoRol.DIRECTOR},
        )
        director.set_password(PASSWORD)
        director.save(update_fields=['password'])

        estudiante, creado_est = Usuario.objects.get_or_create(
            correo=CORREO_ESTUDIANTE_VERDE,
            defaults={'nombre': 'Valeria', 'apellido': 'Estudiante Verde',
                      'tipo_rol': Usuario.TipoRol.ESTUDIANTE},
        )
        estudiante.set_password(PASSWORD)
        estudiante.save(update_fields=['password'])

        curso, _ = Curso.objects.get_or_create(
            codigo='DEMO041-OK', id_periodo_academico=periodo,
            defaults={'nombre': f'{PREFIJO} Curso al día', 'id_docente': docente,
                      'estado': Curso.Estado.ACTIVO},
        )
        proyecto, _ = Proyecto.objects.get_or_create(
            id_curso=curso, nombre=f'{PREFIJO} Proyecto al día',
            defaults={'fecha_inicio': hoy - timedelta(days=30),
                      'fecha_fin_estimada': hoy + timedelta(days=60),
                      'estado': Proyecto.Estado.EN_EJECUCION},
        )
        fase, _ = FaseProyecto.objects.get_or_create(
            id_proyecto=proyecto, orden=1,
            defaults={'nombre': 'Entrega 1', 'fecha_inicio': hoy - timedelta(days=10),
                      'fecha_fin': hoy + timedelta(days=30),
                      'estado': FaseProyecto.Estado.EN_PROGRESO},
        )
        equipo, _ = Equipo.objects.get_or_create(
            proyecto=proyecto, nombre=f'{PREFIJO} Equipo', defaults={'cupo_maximo': 6},
        )
        MiembroEquipo.objects.get_or_create(
            equipo=equipo, usuario=estudiante, defaults={'rol_interno': 'desarrollador'},
        )

        act, _ = Actividad.objects.get_or_create(
            id_fase=fase, nombre=f'{PREFIJO} Diseño de la base de datos',
            defaults={'fecha_limite': hoy - timedelta(days=2),
                      'id_equipo_asignado': equipo, 'id_responsable': estudiante,
                      'estado': Actividad.Estado.COMPLETADA},
        )
        AvanceActividad.objects.get_or_create(
            id_actividad=act, id_usuario=estudiante,
            defaults={'descripcion': 'Entregado a tiempo', 'porcentaje_completado': 100},
        )

        # Estudiante en rojo: 2 actividades vencidas sin completar (100 % incumplidas) y un
        # único avance del 20 % (nota 1.0). update_or_create fuerza el estado en cada ejecución.
        rojo, creado_rojo = Usuario.objects.get_or_create(
            correo=CORREO_ESTUDIANTE_ROJO,
            defaults={'nombre': 'Ramiro', 'apellido': 'Estudiante Rojo',
                      'tipo_rol': Usuario.TipoRol.ESTUDIANTE},
        )
        rojo.set_password(PASSWORD)
        rojo.save(update_fields=['password'])

        # Docente propio: si fuera demo.docente.hu040, el panel de HU-042 vería un proyecto más.
        docente_r, _ = Usuario.objects.get_or_create(
            correo='demo.docente.hu041@ufps.edu.co',
            defaults={'nombre': 'Docente', 'apellido': 'Demo HU-041',
                      'tipo_rol': Usuario.TipoRol.DOCENTE},
        )
        curso_r, _ = Curso.objects.update_or_create(
            codigo='DEMO041-RIESGO', id_periodo_academico=periodo,
            defaults={'nombre': f'{PREFIJO} Curso con atrasos', 'id_docente': docente_r,
                      'estado': Curso.Estado.ACTIVO},
        )
        proyecto_r, _ = Proyecto.objects.get_or_create(
            id_curso=curso_r, nombre=f'{PREFIJO} Proyecto con atrasos',
            defaults={'fecha_inicio': hoy - timedelta(days=30),
                      'fecha_fin_estimada': hoy + timedelta(days=60),
                      'estado': Proyecto.Estado.EN_EJECUCION},
        )
        fase_r, _ = FaseProyecto.objects.get_or_create(
            id_proyecto=proyecto_r, orden=1,
            defaults={'nombre': 'Entrega 1', 'fecha_inicio': hoy - timedelta(days=20),
                      'fecha_fin': hoy + timedelta(days=30),
                      'estado': FaseProyecto.Estado.EN_PROGRESO},
        )
        equipo_r, _ = Equipo.objects.get_or_create(
            proyecto=proyecto_r, nombre=f'{PREFIJO} Equipo con atrasos', defaults={'cupo_maximo': 6},
        )
        MiembroEquipo.objects.get_or_create(
            equipo=equipo_r, usuario=rojo, defaults={'rol_interno': 'desarrollador'},
        )
        for numero, dias_vencida, estado in ((1, 5, Actividad.Estado.PENDIENTE),
                                             (2, 2, Actividad.Estado.EN_PROGRESO)):
            act_r, _ = Actividad.objects.update_or_create(
                id_fase=fase_r, nombre=f'{PREFIJO} Informe actividad {numero}',
                defaults={'fecha_limite': hoy - timedelta(days=dias_vencida),
                          'id_equipo_asignado': equipo_r, 'id_responsable': rojo,
                          'estado': estado},
            )
            if numero == 2:
                AvanceActividad.objects.update_or_create(
                    id_actividad=act_r, id_usuario=rojo,
                    defaults={'descripcion': 'Avance parcial', 'porcentaje_completado': 20},
                )

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Estudiante verde: {CORREO_ESTUDIANTE_VERDE} / {PASSWORD} "
            f"({'creado' if creado_est else 'ya existía'}). "
            f"Estudiante rojo: {CORREO_ESTUDIANTE_ROJO} / {PASSWORD} "
            f"({'creado' if creado_rojo else 'ya existía'}). "
            f"Director: {CORREO_DIRECTOR} / {PASSWORD} "
            f"({'creado' if creado_director else 'ya existía'})."
        ))
