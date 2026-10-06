"""
HU-039 — Muro de anuncios: POST (SCRUM-519), GET (SCRUM-520) y permisos (SCRUM-521).
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.alertas.models import ColaCorreo
from apps.anuncios.models import Anuncio
from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import CursoEstudiante
from apps.usuarios.models import Usuario
from tests.factories import (CursoFactory, DocenteFactory, EquipoFactory, MiembroEquipoFactory,
                             ProyectoFactory, UsuarioFactory)

ANUNCIO = {'titulo': 'Cambio de fecha', 'mensaje': 'La entrega se mueve al viernes.'}


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def curso():
    return CursoFactory()


@pytest.fixture
def inscritos(curso):
    estudiantes = [UsuarioFactory() for _ in range(3)]
    for e in estudiantes:
        CursoEstudiante.objects.create(curso=curso, estudiante=e)
    return estudiantes


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _url_curso(curso):
    return f'/api/cursos/{curso.id}/anuncios/'


# ── SCRUM-519: POST ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_docente_publica_en_su_curso_201_y_encola_correos(curso, inscritos):
    r = _cliente(curso.id_docente).post(_url_curso(curso), ANUNCIO, format='json')

    assert r.status_code == 201
    assert r.data['titulo'] == ANUNCIO['titulo']
    assert r.data['id_curso'] == curso.id and r.data['id_proyecto'] is None
    assert r.data['autor']['id'] == curso.id_docente_id
    correos = ColaCorreo.objects.filter(plantilla='anuncio')
    assert sorted(correos.values_list('id_usuario_destino_id', flat=True)) == sorted(e.id for e in inscritos)
    assert BitacoraSistema.objects.filter(accion='CREATE', modulo='anuncios').exists()


@pytest.mark.django_db
def test_publicar_en_proyecto_encola_a_sus_miembros(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    miembro = UsuarioFactory()
    MiembroEquipoFactory(equipo=EquipoFactory(proyecto=proyecto), usuario=miembro, estado='activo')

    r = _cliente(curso.id_docente).post(f'/api/proyectos/{proyecto.id}/anuncios/', ANUNCIO, format='json')

    assert r.status_code == 201
    assert r.data['id_proyecto'] == proyecto.id
    assert list(ColaCorreo.objects.values_list('id_usuario_destino_id', flat=True)) == [miembro.id]


@pytest.mark.django_db
def test_curso_o_proyecto_inexistente_404():
    admin = UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR)
    assert _cliente(admin).post('/api/cursos/999999/anuncios/', ANUNCIO, format='json').status_code == 404
    assert _cliente(admin).post('/api/proyectos/999999/anuncios/', ANUNCIO, format='json').status_code == 404
    assert _cliente(admin).get('/api/cursos/999999/anuncios/').status_code == 404


@pytest.mark.django_db
def test_datos_invalidos_400(curso):
    r = _cliente(curso.id_docente).post(_url_curso(curso), {'titulo': 'Sin mensaje'}, format='json')
    assert r.status_code == 400
    assert 'mensaje' in r.data


@pytest.mark.django_db
def test_el_curso_sale_de_la_url_y_no_del_body(curso):
    otro = CursoFactory()
    r = _cliente(curso.id_docente).post(_url_curso(curso), {**ANUNCIO, 'id_curso': otro.id}, format='json')
    assert r.status_code == 201
    assert Anuncio.objects.get().id_curso_id == curso.id


# ── SCRUM-521: permisos de publicación ───────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('rol', [Usuario.TipoRol.ESTUDIANTE, Usuario.TipoRol.LIDER_EQUIPO])
def test_estudiante_y_lider_403_antes_de_validar(curso, rol):
    usuario = UsuarioFactory(tipo_rol=rol)
    CursoEstudiante.objects.create(curso=curso, estudiante=usuario)
    r = _cliente(usuario).post(_url_curso(curso), {}, format='json')  # datos vacíos: igual 403
    assert r.status_code == 403
    assert r.data['detail'] == 'No tienes permiso para publicar en este muro'
    assert not Anuncio.objects.exists()


@pytest.mark.django_db
def test_docente_de_otro_curso_403(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    otro_docente = DocenteFactory()
    assert _cliente(otro_docente).post(_url_curso(curso), ANUNCIO, format='json').status_code == 403
    assert _cliente(otro_docente).post(f'/api/proyectos/{proyecto.id}/anuncios/', ANUNCIO,
                                       format='json').status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('rol', [Usuario.TipoRol.DIRECTOR, Usuario.TipoRol.ADMINISTRADOR])
def test_director_y_admin_publican_en_cualquier_curso(curso, rol):
    r = _cliente(UsuarioFactory(tipo_rol=rol)).post(_url_curso(curso), ANUNCIO, format='json')
    assert r.status_code == 201


# ── SCRUM-520: GET ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_listado_mas_reciente_primero(curso, inscritos):
    viejo = Anuncio.objects.create(id_curso=curso, id_autor=curso.id_docente, titulo='Viejo', mensaje='x',
                                   fecha_publicacion=timezone.now() - timedelta(days=2))
    _cliente(curso.id_docente).post(_url_curso(curso), {**ANUNCIO, 'titulo': 'Nuevo'}, format='json')

    r = _cliente(inscritos[0]).get(_url_curso(curso))

    assert r.status_code == 200
    assert [a['titulo'] for a in r.data] == ['Nuevo', viejo.titulo]


@pytest.mark.django_db
def test_muro_de_curso_no_mezcla_anuncios_de_proyecto(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    Anuncio.objects.create(id_curso=curso, id_autor=curso.id_docente, titulo='Del curso', mensaje='x')
    Anuncio.objects.create(id_proyecto=proyecto, id_autor=curso.id_docente, titulo='Del proyecto', mensaje='x')
    docente = _cliente(curso.id_docente)
    assert [a['titulo'] for a in docente.get(_url_curso(curso)).data] == ['Del curso']
    assert [a['titulo'] for a in docente.get(f'/api/proyectos/{proyecto.id}/anuncios/').data] == ['Del proyecto']


@pytest.mark.django_db
def test_acceso_de_lectura_por_integrante(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    miembro = UsuarioFactory(tipo_rol=Usuario.TipoRol.LIDER_EQUIPO)  # no inscrito, solo miembro del proyecto
    MiembroEquipoFactory(equipo=EquipoFactory(proyecto=proyecto), usuario=miembro, estado='activo')
    url_proyecto = f'/api/proyectos/{proyecto.id}/anuncios/'

    assert _cliente(miembro).get(url_proyecto).status_code == 200
    assert _cliente(curso.id_docente).get(url_proyecto).status_code == 200
    assert _cliente(UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)).get(_url_curso(curso)).status_code == 200
    # Ajenos al curso → 403
    assert _cliente(UsuarioFactory()).get(_url_curso(curso)).status_code == 403
    assert _cliente(UsuarioFactory()).get(url_proyecto).status_code == 403
    assert _cliente(DocenteFactory()).get(_url_curso(curso)).status_code == 403


@pytest.mark.django_db
def test_sin_autenticar_401(curso):
    assert APIClient().get(_url_curso(curso)).status_code == 401
