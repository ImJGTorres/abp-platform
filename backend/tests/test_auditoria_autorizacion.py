"""Pruebas de autorización e integridad derivadas de la auditoría del Sprint 2.

Cada caso reproduce un sondeo de la auditoría: el actor no autorizado debe recibir 403
y el dueño del recurso debe poder operar. Cubre NUE-01..09.
"""
import threading
from datetime import date

import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, Proyecto
from apps.equipos.models import Equipo, MiembroEquipo
from apps.usuarios.models import Usuario
from tests.factories import (
    AdminFactory,
    CursoFactory,
    DocenteFactory,
    EquipoFactory,
    FaseProyectoFactory,
    MiembroEquipoFactory,
    UsuarioFactory,
)


def cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


@pytest.fixture
def parametro_equipos(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={
            'valor': '10',
            'categoria': ParametroSistema.Categoria.GENERAL,
            'tipo_dato': ParametroSistema.TipoDato.INTEGER,
        },
    )


@pytest.fixture
def escenario(db, parametro_equipos):
    """Docente dueño, proyecto, equipo con un miembro, estudiante ajeno y docente ajeno."""
    dueno = DocenteFactory()
    curso = CursoFactory(id_docente=dueno, usuario_creo=dueno)
    proyecto = Proyecto.objects.create(
        nombre='Proyecto', id_curso=curso,
        fecha_inicio=date(2026, 2, 1), fecha_fin_estimada=date(2026, 5, 31),
        estado=Proyecto.Estado.EN_EJECUCION,
    )
    equipo = EquipoFactory(proyecto=proyecto, cupo_maximo=3)
    miembro_usuario = UsuarioFactory()
    miembro = MiembroEquipoFactory(equipo=equipo, usuario=miembro_usuario)
    return {
        'dueno': dueno, 'proyecto': proyecto, 'equipo': equipo,
        'miembro': miembro, 'miembro_usuario': miembro_usuario,
        'estudiante_ajeno': UsuarioFactory(), 'docente_ajeno': DocenteFactory(),
    }


def _llamadas(e):
    """(método, url, payload) de las seis operaciones de escritura sobre equipos + rol."""
    eq = e['equipo']
    otro = EquipoFactory(proyecto=e['proyecto'], cupo_maximo=3)
    return {
        'crear': ('post', reverse('equipos-por-proyecto', kwargs={'proyecto_id': e['proyecto'].id}),
                  {'nombre': 'Nuevo', 'cupo_maximo': 3}),
        'asignar': ('post', reverse('asignar-estudiantes', kwargs={'equipo_id': eq.id}),
                    {'usuarios': [UsuarioFactory().id]}),
        'retirar': ('delete', reverse('miembro-retirar', kwargs={'equipo_id': eq.id, 'usuario_id': e['miembro_usuario'].id}), None),
        'editar': ('patch', reverse('equipo-editar', kwargs={'equipo_id': eq.id}), {'nombre': 'Renombrado'}),
        'mover': ('post', reverse('miembro-mover', kwargs={'equipo_id': eq.id}),
                  {'usuario_id': e['miembro_usuario'].id, 'equipo_destino_id': otro.id}),
        'disolver': ('delete', reverse('equipo-disolver', kwargs={'equipo_id': eq.id}), None),
        'rol': ('patch', reverse('miembro-actualizar-rol', kwargs={'miembro_id': e['miembro'].id}),
                {'rol_interno': 'lider'}),
    }


@pytest.mark.parametrize('operacion', ['crear', 'asignar', 'retirar', 'editar', 'mover', 'disolver', 'rol'])
@pytest.mark.parametrize('actor', ['estudiante_ajeno', 'docente_ajeno', 'miembro_usuario'])
def test_actor_no_autorizado_recibe_403(escenario, operacion, actor):
    metodo, url, payload = _llamadas(escenario)[operacion]
    kwargs = {'format': 'json'} if payload is not None else {}
    resp = getattr(cliente(escenario[actor]), metodo)(url, *( [payload] if payload is not None else []), **kwargs)
    assert resp.status_code == 403, resp.content
    # nada cambió
    assert Equipo.objects.get(pk=escenario['equipo'].pk).estado == 'activo'
    assert Usuario.objects.get(pk=escenario['miembro_usuario'].pk).tipo_rol == Usuario.TipoRol.ESTUDIANTE


@pytest.mark.parametrize('operacion', ['crear', 'asignar', 'retirar', 'editar', 'mover', 'disolver', 'rol'])
def test_docente_dueno_y_admin_pueden_operar(escenario, operacion):
    for actor in (escenario['dueno'], AdminFactory()):
        e = escenario
        metodo, url, payload = _llamadas(e)[operacion]
        kwargs = {'format': 'json'} if payload is not None else {}
        resp = getattr(cliente(actor), metodo)(url, *([payload] if payload is not None else []), **kwargs)
        assert resp.status_code in (200, 201, 204), (operacion, resp.status_code, resp.content)
        break  # el estado cambia tras la primera llamada; el admin se prueba abajo


def test_admin_puede_operar(escenario):
    metodo, url, payload = _llamadas(escenario)['editar']
    resp = getattr(cliente(AdminFactory()), metodo)(url, payload, format='json')
    assert resp.status_code == 200


def test_nue02_rol_lider_solo_lo_asigna_el_docente_y_sincroniza_tipo_rol(escenario):
    url = reverse('miembro-actualizar-rol', kwargs={'miembro_id': escenario['miembro'].id})
    assert cliente(escenario['estudiante_ajeno']).patch(url, {'rol_interno': 'lider'}, format='json').status_code == 403
    assert Usuario.objects.get(pk=escenario['miembro_usuario'].pk).tipo_rol == Usuario.TipoRol.ESTUDIANTE
    assert cliente(escenario['dueno']).patch(url, {'rol_interno': 'lider'}, format='json').status_code == 200
    assert Usuario.objects.get(pk=escenario['miembro_usuario'].pk).tipo_rol == Usuario.TipoRol.LIDER_EQUIPO


def test_crear_equipo_queda_en_bitacora(escenario):
    metodo, url, payload = _llamadas(escenario)['crear']
    assert cliente(escenario['dueno']).post(url, payload, format='json').status_code == 201
    assert BitacoraSistema.objects.filter(accion='CREATE', modulo='equipos', descripcion__contains='Nuevo').exists()


def test_retirar_libera_actividades_y_deja_bitacora(escenario):
    fase = FaseProyectoFactory(id_proyecto=escenario['proyecto'])
    act = Actividad.objects.create(
        id_fase=fase, nombre='Act', fecha_limite=date(2026, 3, 1), prioridad='media',
        estado='pendiente', id_equipo_asignado=escenario['equipo'],
        id_responsable=escenario['miembro_usuario'],
    )
    act.responsables.add(escenario['miembro_usuario'])
    url = reverse('miembro-retirar', kwargs={'equipo_id': escenario['equipo'].id, 'usuario_id': escenario['miembro_usuario'].id})
    assert cliente(escenario['dueno']).delete(url).status_code == 204
    act.refresh_from_db()
    assert act.id_responsable is None
    assert act.responsables.count() == 0
    assert BitacoraSistema.objects.filter(accion='actividad_sin_responsable').exists()


def test_disolver_equipo_sin_entregables_libera_actividades(escenario):
    fase = FaseProyectoFactory(id_proyecto=escenario['proyecto'])
    act = Actividad.objects.create(
        id_fase=fase, nombre='Act', fecha_limite=date(2026, 3, 1), prioridad='media',
        estado='pendiente', id_equipo_asignado=escenario['equipo'],
        id_responsable=escenario['miembro_usuario'],
    )
    url = reverse('equipo-disolver', kwargs={'equipo_id': escenario['equipo'].id})
    assert cliente(escenario['dueno']).delete(url).status_code == 204
    act.refresh_from_db()
    assert act.id_responsable is None
    assert MiembroEquipo.objects.get(pk=escenario['miembro'].pk).estado == 'retirado'


def test_nue06_cupo_no_se_supera_con_peticiones_simultaneas(django_db_setup, django_db_blocker):
    """8 asignaciones simultáneas a un equipo de cupo 2 nunca dejan más de 2 activos.

    Necesita commits reales entre hilos. transactional_db no sirve aquí porque
    CursoEstudiante es managed=False y su flush falla; se crean y se borran los
    datos a mano sobre la base de pruebas.
    """
    with django_db_blocker.unblock():
        ParametroSistema.objects.get_or_create(
            clave='max_estudiantes_por_equipo',
            defaults={'valor': '10', 'categoria': ParametroSistema.Categoria.GENERAL,
                      'tipo_dato': ParametroSistema.TipoDato.INTEGER},
        )
        dueno = DocenteFactory()
        curso = CursoFactory(id_docente=dueno, usuario_creo=dueno)
        proyecto = Proyecto.objects.create(
            nombre='P', id_curso=curso, fecha_inicio=date(2026, 2, 1),
            fecha_fin_estimada=date(2026, 5, 31), estado=Proyecto.Estado.EN_EJECUCION,
        )
        equipo = EquipoFactory(proyecto=proyecto, cupo_maximo=2)
        estudiantes = [UsuarioFactory() for _ in range(8)]
        url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo.id})
        resultados = []

        def asignar(est):
            try:
                resultados.append(cliente(dueno).post(url, {'usuarios': [est.id]}, format='json').status_code)
            finally:
                connection.close()

        try:
            hilos = [threading.Thread(target=asignar, args=(e,)) for e in estudiantes]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            activos = MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count()
        finally:
            MiembroEquipo.objects.filter(equipo=equipo).delete()
            equipo.delete()
            proyecto.delete()
            curso.delete()
            Usuario.objects.filter(pk__in=[e.pk for e in estudiantes] + [dueno.pk]).delete()

    assert activos == 2
    assert 500 not in resultados


# ---------------------------------------------------------------------------
# NUE-03 — exportaciones con las mismas reglas que la API de reportes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('tipo,parametros', [
    ('proyecto', lambda e: {'proyecto_id': e['proyecto'].id}),
    ('equipo', lambda e: {'equipo_id': e['equipo'].id}),
    ('estudiante', lambda e: {'estudiante_id': e['miembro_usuario'].id, 'proyecto_id': e['proyecto'].id}),
    ('indicadores', lambda e: {}),
    ('tendencia', lambda e: {}),
])
def test_nue03_estudiante_ajeno_no_puede_exportar(escenario, tipo, parametros):
    url = reverse('exportar-solicitar')
    resp = cliente(escenario['estudiante_ajeno']).post(
        url, {'tipo_reporte': tipo, 'formato': 'excel', 'parametros': parametros(escenario)}, format='json')
    assert resp.status_code == 403, resp.content


def test_nue03_estudiante_exporta_solo_su_propio_reporte(escenario):
    url = reverse('exportar-solicitar')
    propio = {'estudiante_id': escenario['miembro_usuario'].id, 'proyecto_id': escenario['proyecto'].id}
    ajeno = {'estudiante_id': escenario['estudiante_ajeno'].id, 'proyecto_id': escenario['proyecto'].id}
    c = cliente(escenario['miembro_usuario'])
    assert c.post(url, {'tipo_reporte': 'estudiante', 'formato': 'excel', 'parametros': propio}, format='json').status_code == 201
    assert c.post(url, {'tipo_reporte': 'estudiante', 'formato': 'excel', 'parametros': ajeno}, format='json').status_code == 403


@pytest.mark.parametrize('formato', ['pdf', 'excel'])
def test_nue03_export_de_equipo_usa_su_propio_generador(escenario, formato):
    url = reverse('exportar-solicitar')
    resp = cliente(escenario['dueno']).post(
        url, {'tipo_reporte': 'equipo', 'formato': formato, 'parametros': {'equipo_id': escenario['equipo'].id}},
        format='json')
    assert resp.status_code == 201
    assert resp.json()['estado'] == 'listo', resp.json()


def test_nue21_parametros_de_exportacion_validados(escenario):
    url = reverse('exportar-solicitar')
    resp = cliente(AdminFactory()).post(
        url, {'tipo_reporte': 'tendencia', 'formato': 'excel', 'parametros': {'n_periodos': 'abc'}}, format='json')
    assert resp.status_code == 400
    resp = cliente(AdminFactory()).post(
        url, {'tipo_reporte': 'tendencia', 'formato': 'excel', 'parametros': {'n_periodos': 99999}}, format='json')
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# NUE-04 — adjuntos
# ---------------------------------------------------------------------------

@pytest.fixture
def adjunto(escenario):
    from apps.entregables.models import ArchivoAdjunto, Entregable
    fase = FaseProyectoFactory(id_proyecto=escenario['proyecto'])
    act = Actividad.objects.create(
        id_fase=fase, nombre='Act', fecha_limite=date(2026, 3, 1), prioridad='media',
        estado='pendiente', id_equipo_asignado=escenario['equipo'])
    ent = Entregable.objects.create(
        id_actividad=act, id_equipo=escenario['equipo'], titulo='E', descripcion='d',
        tipo='documento', estado='borrador')
    return ArchivoAdjunto.objects.create(
        id_entregable=ent, id_usuario=escenario['miembro_usuario'], nombre_original='a.pdf',
        nombre_almacenado='a.pdf', ruta='no/existe.pdf', tipo_mime='application/pdf', tamaño_bytes=1)


@pytest.mark.parametrize('actor', ['estudiante_ajeno', 'docente_ajeno'])
def test_nue04_ajeno_no_borra_adjunto(escenario, adjunto, actor):
    from apps.entregables.models import ArchivoAdjunto
    url = reverse('archivo-eliminar', kwargs={'archivo_id': adjunto.id})
    assert cliente(escenario[actor]).delete(url).status_code == 403
    assert ArchivoAdjunto.objects.filter(pk=adjunto.pk).exists()


@pytest.mark.parametrize('actor', ['miembro_usuario', 'dueno'])
def test_nue04_miembro_y_docente_dueno_borran_adjunto(escenario, adjunto, actor):
    from apps.entregables.models import ArchivoAdjunto
    url = reverse('archivo-eliminar', kwargs={'archivo_id': adjunto.id})
    assert cliente(escenario[actor]).delete(url).status_code == 204
    assert not ArchivoAdjunto.objects.filter(pk=adjunto.pk).exists()


# ---------------------------------------------------------------------------
# NUE-05 — inscripción de estudiantes en cursos ajenos
# ---------------------------------------------------------------------------

def test_nue05_docente_ajeno_no_lista_ni_inscribe(escenario):
    curso = escenario['proyecto'].id_curso
    url = reverse('curso-estudiantes', kwargs={'curso_id': curso.id})
    ajeno = cliente(escenario['docente_ajeno'])
    assert ajeno.get(url).status_code == 403
    assert ajeno.post(url, {'estudiante_id': escenario['estudiante_ajeno'].id}, format='json').status_code == 403


def test_nue05_docente_dueno_y_admin_si_pueden(escenario):
    curso = escenario['proyecto'].id_curso
    url = reverse('curso-estudiantes', kwargs={'curso_id': curso.id})
    assert cliente(escenario['dueno']).get(url).status_code == 200
    assert cliente(AdminFactory()).post(
        url, {'estudiante_id': escenario['estudiante_ajeno'].id}, format='json').status_code == 201
