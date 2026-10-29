"""
Datos de demostración para la prueba de aceptación de HU-043 (SCRUM-543):
notificaciones automáticas por correo (anuncio y calificación publicada).

Crea (o reutiliza) un docente, dos estudiantes, un curso con proyecto y equipo, y un
entregable con una evaluación en borrador. Es un conjunto aislado ([DEMO HU-043]) para no
alterar los semáforos de HU-041/042. Se puede correr varias veces: deja la evaluación en
borrador y borra los anuncios y correos encolados de corridas anteriores.
Los correos usan example.com para que ningún envío real llegue a una persona.
"""
from datetime import date

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

PASSWORD = 'Test1234'
CORREO_DOCENTE = 'demo.docente.hu043@example.com'
CORREOS_ESTUDIANTES = ['demo.est1.hu043@example.com', 'demo.est2.hu043@example.com']
PREFIJO = '[DEMO HU-043]'


class Command(BaseCommand):
    help = 'Crea los datos de la prueba de aceptación de HU-043 y deja la evaluación en borrador.'

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.alertas.models import Alerta, ColaCorreo
        from apps.anuncios.models import Anuncio
        from apps.configuracion.models import PeriodoAcademico
        from apps.cursos.models import Actividad, Curso, FaseProyecto, Proyecto
        from apps.entregables.models import Entregable, Notificacion
        from apps.equipos.models import Equipo, MiembroEquipo
        from apps.evaluacion.models import Evaluacion, Rubrica
        from apps.usuarios.models import Usuario

        def usuario(correo, nombre, rol):
            u, _ = Usuario.objects.get_or_create(
                correo=correo,
                defaults={'nombre': nombre, 'apellido': PREFIJO, 'tipo_rol': rol,
                          'estado': Usuario.Estado.ACTIVO})
            u.password = make_password(PASSWORD)
            u.save(update_fields=['password'])
            return u

        docente = usuario(CORREO_DOCENTE, 'Docente', Usuario.TipoRol.DOCENTE)
        estudiantes = [usuario(c, f'Estudiante{i}', Usuario.TipoRol.ESTUDIANTE)
                       for i, c in enumerate(CORREOS_ESTUDIANTES, 1)]

        periodo = (PeriodoAcademico.objects.filter(estado=PeriodoAcademico.Estado.ACTIVO).first()
                   or PeriodoAcademico.objects.create(
                       nombre=f'{PREFIJO} Periodo', fecha_inicio=date(2026, 1, 1),
                       fecha_fin=date(2026, 12, 31), estado=PeriodoAcademico.Estado.ACTIVO,
                       usuario_creo=docente))
        curso, _ = Curso.objects.get_or_create(
            codigo='DEMO-043',
            defaults={'nombre': f'{PREFIJO} Curso', 'id_docente': docente,
                      'id_periodo_academico': periodo, 'usuario_creo': docente,
                      'estado': Curso.Estado.ACTIVO})
        proyecto, _ = Proyecto.objects.get_or_create(
            id_curso=curso, nombre=f'{PREFIJO} Proyecto',
            defaults={'fecha_inicio': date(2026, 2, 1), 'fecha_fin_estimada': date(2026, 12, 31),
                      'estado': Proyecto.Estado.EN_EJECUCION})
        fase, _ = FaseProyecto.objects.get_or_create(
            id_proyecto=proyecto, nombre=f'{PREFIJO} Fase',
            defaults={'descripcion': 'Fase de la prueba de aceptación', 'orden': 1,
                      'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 12, 31),
                      'estado': FaseProyecto.Estado.PENDIENTE})
        actividad, _ = Actividad.objects.get_or_create(
            id_fase=fase, nombre=f'{PREFIJO} Actividad',
            defaults={'descripcion': 'Actividad de la prueba', 'fecha_limite': date(2026, 12, 31),
                      'prioridad': Actividad.Prioridad.MEDIA, 'estado': Actividad.Estado.PENDIENTE})
        equipo, _ = Equipo.objects.get_or_create(
            nombre=f'{PREFIJO} Equipo', proyecto=proyecto, defaults={'cupo_maximo': 5})
        for est in estudiantes:
            MiembroEquipo.objects.get_or_create(
                equipo=equipo, usuario=est,
                defaults={'rol_interno': 'desarrollador', 'estado': 'activo'})

        entregable, _ = Entregable.objects.get_or_create(
            id_actividad=actividad, id_equipo=equipo, titulo=f'{PREFIJO} Informe final',
            defaults={'descripcion': 'Entregable de la prueba', 'tipo': 'documento',
                      'estado': 'enviado'})
        rubrica, _ = Rubrica.objects.get_or_create(nombre=f'{PREFIJO} Rúbrica', id_docente=docente)
        evaluacion = Evaluacion.objects.filter(id_entregable=entregable).first()
        if evaluacion is None:
            evaluacion = Evaluacion.objects.create(
                id_entregable=entregable, id_rubrica=rubrica, id_docente=docente,
                puntuacion_total='4.50', comentario_general='Buen trabajo, sigan así.')
        evaluacion.estado = Evaluacion.Estado.BORRADOR
        evaluacion.save(update_fields=['estado'])

        # Limpieza de corridas anteriores
        ids = [docente.id] + [e.id for e in estudiantes]
        Anuncio.objects.filter(id_autor=docente).delete()
        ColaCorreo.objects.filter(id_usuario_destino_id__in=ids).delete()
        Alerta.objects.filter(id_usuario_destino_id__in=ids).delete()
        Notificacion.objects.filter(id_usuario_destino_id__in=ids).delete()

        self.stdout.write(self.style.SUCCESS(
            f'Listo. Docente: {CORREO_DOCENTE} / {PASSWORD}. Estudiantes: '
            f'{", ".join(CORREOS_ESTUDIANTES)} / {PASSWORD}. Proyecto id={proyecto.id}, '
            f'evaluación id={evaluacion.id} (borrador).'))
