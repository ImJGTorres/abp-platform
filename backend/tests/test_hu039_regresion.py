"""
HU-039 — Pruebas de regresión del muro de anuncios (SCRUM-524).

Complementa test_hu039_anuncios.py (Nicole, modelo/serializador/servicio con
mocks) y test_hu039_anuncios_endpoint.py (Gabriel, endpoint) con lo que pedía
la tarjeta y no estaba cubierto:
  - aislamiento: un estudiante retirado del curso no ve el muro ni recibe el
    correo; un miembro retirado del equipo tampoco recibe el correo;
  - un docente ajeno no puede leer el muro de un proyecto que no es suyo;
  - orden estable cuando dos anuncios comparten fecha_publicacion;
  - registro en bitácora al listar el muro (hallazgo si no existe).
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.alertas.models import ColaCorreo
from apps.anuncios.models import Anuncio
from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import CursoEstudiante
from apps.equipos.models import MiembroEquipo
from apps.usuarios.models import Usuario
from tests.factories import (
    CursoFactory, DocenteFactory, EquipoFactory, MiembroEquipoFactory, ProyectoFactory, UsuarioFactory,
)

ANUNCIO = {'titulo': 'Cambio de fecha', 'mensaje': 'La entrega se mueve al viernes.'}


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def curso():
    return CursoFactory()


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _url_curso(curso):
    return f'/api/cursos/{curso.id}/anuncios/'


# ── Aislamiento: estudiantes y miembros retirados ───────────────────────────

@pytest.mark.django_db
def test_estudiante_retirado_del_curso_no_ve_el_muro(curso):
    retirado = UsuarioFactory()
    CursoEstudiante.objects.create(curso=curso, estudiante=retirado, estado='inactivo')

    assert _cliente(retirado).get(_url_curso(curso)).status_code == 403


@pytest.mark.django_db
def test_estudiante_retirado_del_curso_no_recibe_el_correo(curso):
    retirado = UsuarioFactory()
    CursoEstudiante.objects.create(curso=curso, estudiante=retirado, estado='inactivo')
    activo = UsuarioFactory()
    CursoEstudiante.objects.create(curso=curso, estudiante=activo, estado='activo')

    r = _cliente(curso.id_docente).post(_url_curso(curso), ANUNCIO, format='json')

    assert r.status_code == 201
    destinatarios = set(ColaCorreo.objects.values_list('id_usuario_destino_id', flat=True))
    assert destinatarios == {activo.id}
    assert retirado.id not in destinatarios


@pytest.mark.django_db
def test_miembro_retirado_del_equipo_no_recibe_el_correo_de_anuncio_de_proyecto(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    equipo = EquipoFactory(proyecto=proyecto)
    activo = UsuarioFactory()
    retirado = UsuarioFactory()
    MiembroEquipoFactory(equipo=equipo, usuario=activo, estado='activo')
    MiembroEquipo.objects.create(equipo=equipo, usuario=retirado, estado='retirado')

    r = _cliente(curso.id_docente).post(f'/api/proyectos/{proyecto.id}/anuncios/', ANUNCIO, format='json')

    assert r.status_code == 201
    assert list(ColaCorreo.objects.values_list('id_usuario_destino_id', flat=True)) == [activo.id]


@pytest.mark.django_db
def test_miembro_retirado_del_equipo_no_ve_el_muro_del_proyecto(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    equipo = EquipoFactory(proyecto=proyecto)
    retirado = UsuarioFactory()
    MiembroEquipo.objects.create(equipo=equipo, usuario=retirado, estado='retirado')

    r = _cliente(retirado).get(f'/api/proyectos/{proyecto.id}/anuncios/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_docente_ajeno_no_lee_el_muro_de_un_proyecto_que_no_es_suyo(curso):
    proyecto = ProyectoFactory(id_curso=curso)
    ajeno = DocenteFactory()
    assert _cliente(ajeno).get(f'/api/proyectos/{proyecto.id}/anuncios/').status_code == 403


# ── Orden del muro ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_anuncios_con_la_misma_fecha_se_desempatan_por_id_mas_reciente_primero(curso):
    misma_fecha = timezone.now()
    primero = Anuncio.objects.create(id_curso=curso, id_autor=curso.id_docente, titulo='Primero',
                                     mensaje='x', fecha_publicacion=misma_fecha)
    segundo = Anuncio.objects.create(id_curso=curso, id_autor=curso.id_docente, titulo='Segundo',
                                     mensaje='x', fecha_publicacion=misma_fecha)

    r = _cliente(curso.id_docente).get(_url_curso(curso))

    assert r.status_code == 200
    assert [a['titulo'] for a in r.data] == [segundo.titulo, primero.titulo]


# ── Validación y permisos adicionales ───────────────────────────────────────

@pytest.mark.django_db
def test_titulo_vacio_retorna_400(curso):
    r = _cliente(curso.id_docente).post(_url_curso(curso), {'titulo': '', 'mensaje': 'm'}, format='json')
    assert r.status_code == 400
    assert 'titulo' in r.data


@pytest.mark.django_db
def test_proyecto_publicado_no_aparece_en_el_muro_del_curso(curso):
    """Regresión del filtro id_proyecto__isnull=True del GET de curso."""
    proyecto = ProyectoFactory(id_curso=curso)
    _cliente(curso.id_docente).post(f'/api/proyectos/{proyecto.id}/anuncios/', ANUNCIO, format='json')

    r = _cliente(curso.id_docente).get(_url_curso(curso))
    assert r.status_code == 200
    assert r.data == []


# ── Bitácora al listar el muro ───────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.xfail(
    strict=True,
    reason='Hallazgo PRB-10: GET del muro de anuncios no registra ACCESS en la bitácora',
)
def test_listar_el_muro_queda_en_bitacora(curso):
    _cliente(curso.id_docente).get(_url_curso(curso))
    assert BitacoraSistema.objects.filter(
        modulo='anuncios', accion=BitacoraSistema.Accion.ACCESS,
    ).exists()
