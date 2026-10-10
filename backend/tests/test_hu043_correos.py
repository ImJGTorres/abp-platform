"""
HU-043 — Notificaciones por correo: proveedor (SCRUM-538), plantillas con membrete (SCRUM-539),
despacho de la cola (SCRUM-540) y eventos que encolan (SCRUM-541).
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.alertas.models import ColaCorreo
from apps.alertas.services import (_crear_alerta, despachar_cola, encolar_correo,
                                   generar_recordatorios_48h, renderizar_correo)
from apps.anuncios.services import publicar_anuncio
from apps.configuracion.models import ParametroSistema
from apps.entregables.models import Entregable
from apps.evaluacion.models import Evaluacion, Rubrica
from tests.factories import (ActividadFactory, EquipoFactory, FaseProyectoFactory,
                             MiembroEquipoFactory, UsuarioFactory)

CONSOLA = 'django.core.mail.backends.console.EmailBackend'

IDENTIDAD_CON_LOGO = {'nombre_institucion': 'Universidad Francisco de Paula Santander',
                      'programa_academico': 'Ingeniería de Sistemas',
                      'logotipo_path': None, 'logotipo_url': '/media/identidad/logo.png'}
IDENTIDAD_SIN_LOGO = {**IDENTIDAD_CON_LOGO, 'logotipo_url': None}

CONTEXTOS = {
    'alerta': {'mensaje': 'La actividad X venció hace 2 día(s).', 'proyecto_id': 1},
    'recordatorio': {'mensaje': "La actividad 'Informe' vence en 1 día(s).", 'proyecto_id': 1},
    'anuncio': {'anuncio_id': 1, 'titulo': 'Cambio de fecha', 'mensaje': 'La entrega pasa al viernes.',
                'curso_id': 1, 'proyecto_id': None, 'autor': 'Docente Uno'},
    'calificacion': {'evaluacion_id': 1, 'entregable': 'Informe final', 'proyecto_id': 3,
                     'proyecto_nombre': 'Inventario', 'puntuacion_total': '4.50',
                     'comentario_general': 'Buen trabajo.', 'enlace': '/estudiante/proyectos/3/historial'},
}
TEXTO_ESPERADO = {
    'alerta': 'venció hace 2 día(s)',
    'recordatorio': 'Recordatorio de vencimiento',
    'anuncio': 'Cambio de fecha',
    'calificacion': '4.50',
}


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


def _sin_guardar(plantilla, usuario=None):
    usuario = usuario or UsuarioFactory.build(nombre='Ana', apellido='Rojas', correo='ana@ufps.edu.co')
    return ColaCorreo(id_usuario_destino=usuario, asunto='Asunto', plantilla=plantilla,
                      contexto=CONTEXTOS[plantilla])


# ── SCRUM-538: proveedor ─────────────────────────────────────────────────────

def test_anymail_instalado_y_frontend_url_configurada():
    assert 'anymail' in settings.INSTALLED_APPS
    assert settings.FRONTEND_URL and not settings.FRONTEND_URL.endswith('/')


@override_settings(EMAIL_BACKEND=CONSOLA)
def test_backend_de_consola_imprime_el_correo(capsys):
    mail.send_mail('Prueba ABP', 'Cuerpo de prueba', None, ['destino@ufps.edu.co'])
    salida = capsys.readouterr().out
    assert 'Subject: Prueba ABP' in salida and 'destino@ufps.edu.co' in salida


# ── SCRUM-539: plantillas ────────────────────────────────────────────────────

@pytest.mark.parametrize('plantilla', list(CONTEXTOS))
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_CON_LOGO)
def test_las_4_plantillas_renderizan_con_membrete(_identidad, plantilla):
    html = renderizar_correo(_sin_guardar(plantilla))

    assert 'Universidad Francisco de Paula Santander' in html
    assert 'Ingeniería de Sistemas' in html
    assert f'src="{settings.FRONTEND_URL}/media/identidad/logo.png"' in html
    assert '#d32f2f' in html and 'width="600"' in html
    assert 'Este es un mensaje automático de la Plataforma ABP' in html
    assert 'Hola, Ana Rojas' in html
    assert TEXTO_ESPERADO[plantilla] in html
    assert '<link' not in html and '<style' not in html  # sin CSS externo ni en bloque


@pytest.mark.parametrize('plantilla', list(CONTEXTOS))
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_sin_logo_muestra_solo_el_nombre(_identidad, plantilla):
    html = renderizar_correo(_sin_guardar(plantilla))
    assert '<img' not in html
    assert 'Universidad Francisco de Paula Santander' in html


@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_calificacion_enlaza_al_historial(_identidad):
    html = renderizar_correo(_sin_guardar('calificacion'))
    assert f'href="{settings.FRONTEND_URL}/estudiante/proyectos/3/historial"' in html


# ── SCRUM-540: despacho de la cola ───────────────────────────────────────────

@pytest.mark.django_db
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_despachar_envia_html_y_texto_y_marca_enviado(_identidad):
    usuario = UsuarioFactory(correo='ana@ufps.edu.co')
    correo = encolar_correo(usuario.id, 'Nueva alerta', 'alerta', CONTEXTOS['alerta'])

    assert despachar_cola() == {'enviados': 1, 'fallidos': 0}

    correo.refresh_from_db()
    assert correo.estado == 'enviado' and correo.fecha_envio is not None
    enviado = mail.outbox[0]
    assert enviado.to == ['ana@ufps.edu.co'] and enviado.subject == 'Nueva alerta'
    html, tipo = enviado.alternatives[0]
    assert tipo == 'text/html' and 'Universidad Francisco de Paula Santander' in html
    assert '<table' not in enviado.body  # el cuerpo es texto plano (strip_tags)
    assert 'venció hace 2 día(s)' in enviado.body


@pytest.mark.django_db
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_destinatario_invalido_queda_en_error_tras_3_ciclos(_identidad):
    sin_correo = UsuarioFactory(correo='no-es-un-correo')
    correo = encolar_correo(sin_correo.id, 'Asunto', 'alerta', CONTEXTOS['alerta'])

    for intento in (1, 2):
        despachar_cola()
        correo.refresh_from_db()
        assert (correo.estado, correo.intentos) == ('pendiente', intento)
    despachar_cola()
    correo.refresh_from_db()

    assert correo.estado == 'error' and correo.intentos == 3
    assert 'Destinatario sin correo válido' in correo.error
    assert mail.outbox == []
    despachar_cola()  # ya no se reintenta
    correo.refresh_from_db()
    assert correo.intentos == 3


@pytest.mark.django_db
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_un_correo_fallido_no_detiene_los_demas_y_respeta_el_limite(_identidad):
    malo = encolar_correo(UsuarioFactory(correo='malo').id, 'A', 'alerta', CONTEXTOS['alerta'])
    buenos = [encolar_correo(UsuarioFactory().id, f'B{i}', 'alerta', CONTEXTOS['alerta']) for i in range(3)]

    assert despachar_cola(limite=3) == {'enviados': 2, 'fallidos': 1}

    estados = dict(ColaCorreo.objects.values_list('id', 'estado'))
    assert estados[buenos[0].id] == estados[buenos[1].id] == 'enviado'
    assert estados[buenos[2].id] == 'pendiente'  # fuera del límite, sale en el siguiente ciclo
    assert estados[malo.id] == 'pendiente'


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=CONSOLA)
@patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_SIN_LOGO)
def test_run_scheduler_once_imprime_html_con_membrete_y_marca_enviado(_identidad, capsys):
    encolar_correo(UsuarioFactory().id, 'Nuevo anuncio: Cambio de fecha', 'anuncio', CONTEXTOS['anuncio'])

    call_command('run_scheduler', '--once')

    salida = capsys.readouterr().out
    assert 'Content-Type: text/html' in salida
    assert 'Universidad Francisco de Paula Santander' in salida
    assert set(ColaCorreo.objects.values_list('estado', flat=True)) == {'enviado'}


# ── SCRUM-541: eventos que encolan, una sola vez ─────────────────────────────

@pytest.fixture
def evaluacion_borrador():
    fase = FaseProyectoFactory()
    docente = fase.id_proyecto.id_curso.id_docente
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    activos = [MiembroEquipoFactory(equipo=equipo).usuario for _ in range(2)]
    MiembroEquipoFactory(equipo=equipo, estado='retirado')
    act = ActividadFactory(id_fase=fase)
    entregable = Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Informe final',
                                           descripcion='x', tipo='documento', estado='enviado')
    rubrica = Rubrica.objects.create(nombre='R', id_docente=docente)
    evaluacion = Evaluacion.objects.create(id_entregable=entregable, id_rubrica=rubrica, id_docente=docente,
                                           puntuacion_total='4.50', comentario_general='Buen trabajo.')
    return evaluacion, docente, activos


@pytest.mark.django_db
def test_publicar_calificacion_encola_un_correo_por_miembro_activo_una_sola_vez(evaluacion_borrador):
    evaluacion, docente, activos = evaluacion_borrador
    cliente = APIClient()
    cliente.force_authenticate(user=docente)
    url = f'/api/evaluaciones/{evaluacion.id}/publicar/'

    assert cliente.patch(url).status_code == 200
    assert cliente.patch(url).status_code == 400  # ya publicada: no vuelve a encolar

    correos = ColaCorreo.objects.filter(plantilla='calificacion')
    assert sorted(correos.values_list('id_usuario_destino_id', flat=True)) == sorted(u.id for u in activos)
    contexto = correos.first().contexto
    proyecto_id = evaluacion.id_entregable.id_actividad.id_fase.id_proyecto_id
    assert contexto['puntuacion_total'] == '4.50'
    assert contexto['comentario_general'] == 'Buen trabajo.'
    assert contexto['enlace'] == f'/estudiante/proyectos/{proyecto_id}/historial'


@pytest.mark.django_db
def test_alerta_recordatorio_y_anuncio_encolan_una_sola_vez():
    est = UsuarioFactory()
    fase = FaseProyectoFactory()
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=equipo, usuario=est)
    ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=date.today() + timedelta(days=1))

    for _ in range(2):
        _crear_alerta('actividad_vencida', est.id, 'Vencida', proyecto_id=fase.id_proyecto_id, referencia_id=99)
        generar_recordatorios_48h()
    publicar_anuncio(fase.id_proyecto.id_curso.id_docente,
                     {'id_proyecto': fase.id_proyecto, 'titulo': 'Aviso', 'mensaje': 'Hola'}, None)

    por_plantilla = sorted(ColaCorreo.objects.values_list('plantilla', flat=True))
    assert por_plantilla == ['alerta', 'anuncio', 'recordatorio']
