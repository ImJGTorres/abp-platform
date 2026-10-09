"""
HU-044 — Banco de rúbricas: guardar-plantilla (SCRUM-561), catálogo (SCRUM-562),
clonar (SCRUM-563) y validación de ponderaciones al 100 % (SCRUM-564).
"""
import pytest
from rest_framework.test import APIClient

from apps.evaluacion.models import CriterioRubrica, NivelDesempeno, Rubrica
from tests.factories import AdminFactory, CursoFactory, DocenteFactory, ProyectoFactory, UsuarioFactory


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _rubrica(docente, pesos=(60, 40), **kwargs):
    rubrica = Rubrica.objects.create(id_docente=docente, nombre='Rúbrica base', **kwargs)
    for i, peso in enumerate(pesos):
        criterio = CriterioRubrica.objects.create(id_rubrica=rubrica, nombre=f'C{i}', peso_porcentual=peso)
        NivelDesempeno.objects.create(id_criterio=criterio, nivel=1, etiqueta='insuficiente',
                                      descripcion='Bajo', puntos=1)
        NivelDesempeno.objects.create(id_criterio=criterio, nivel=4, etiqueta='excelente',
                                      descripcion='Alto', puntos=5)
    return rubrica


def _guardar(usuario, rubrica, nombre='Plantilla ABP'):
    return _cliente(usuario).patch(f'/api/rubricas/{rubrica.pk}/guardar-plantilla/',
                                   {'nombre_plantilla': nombre}, format='json')


# ── SCRUM-561 / 564: guardar como plantilla ──────────────────────────────────

@pytest.mark.django_db
def test_guardar_plantilla_dueno_200():
    docente = DocenteFactory()
    rubrica = _rubrica(docente)
    resp = _guardar(docente, rubrica)
    assert resp.status_code == 200
    assert resp.data['es_plantilla'] is True and resp.data['nombre_plantilla'] == 'Plantilla ABP'


@pytest.mark.django_db
def test_guardar_plantilla_docente_ajeno_403_y_admin_200():
    rubrica = _rubrica(DocenteFactory())
    assert _guardar(DocenteFactory(), rubrica).status_code == 403
    assert _guardar(AdminFactory(), rubrica).status_code == 200


@pytest.mark.django_db
def test_guardar_plantilla_ponderaciones_90_400_con_suma_actual():
    docente = DocenteFactory()
    rubrica = _rubrica(docente, pesos=(50, 40))
    resp = _guardar(docente, rubrica)
    assert resp.status_code == 400
    assert '90' in str(resp.data['detail'])
    rubrica.refresh_from_db()
    assert rubrica.es_plantilla is False


# ── SCRUM-562: catálogo ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_catalogo_solo_plantillas_ordenadas_con_criterios_y_niveles():
    docente = DocenteFactory()
    _rubrica(docente, es_plantilla=True, nombre_plantilla='Zeta')
    _rubrica(docente, es_plantilla=True, nombre_plantilla='Alfa')
    _rubrica(docente)  # no es plantilla
    resp = _cliente(DocenteFactory()).get('/api/rubricas/plantillas/')
    assert resp.status_code == 200
    assert [p['nombre_plantilla'] for p in resp.data] == ['Alfa', 'Zeta']
    assert len(resp.data[0]['criterios']) == 2 and len(resp.data[0]['criterios'][0]['niveles']) == 2


@pytest.mark.django_db
def test_catalogo_estudiante_403():
    assert _cliente(UsuarioFactory()).get('/api/rubricas/plantillas/').status_code == 403


# ── SCRUM-563: clonar ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_clonar_201_copia_independiente():
    plantilla = _rubrica(DocenteFactory(), es_plantilla=True, nombre_plantilla='Base')
    proyecto = ProyectoFactory()
    docente_curso = proyecto.id_curso.id_docente

    resp = _cliente(docente_curso).post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                                        {'id_proyecto': proyecto.pk}, format='json')
    assert resp.status_code == 201
    copia = Rubrica.objects.get(pk=resp.data['id'])
    assert copia.pk != plantilla.pk
    assert (copia.es_plantilla, copia.nombre_plantilla) == (False, None)
    assert (copia.id_proyecto_id, copia.id_docente_id) == (proyecto.pk, docente_curso.pk)
    assert NivelDesempeno.objects.filter(id_criterio__id_rubrica=copia).count() == 4

    # Editar la copia no cambia la plantilla
    criterio_copia = copia.criterios.first()
    criterio_copia.nombre = 'Editado'
    criterio_copia.save()
    assert not plantilla.criterios.filter(nombre='Editado').exists()
    assert not set(copia.criterios.values_list('id', flat=True)) & set(plantilla.criterios.values_list('id', flat=True))


@pytest.mark.django_db
def test_clonar_docente_de_otro_curso_403():
    plantilla = _rubrica(DocenteFactory(), es_plantilla=True, nombre_plantilla='Base')
    proyecto = ProyectoFactory(id_curso=CursoFactory())
    resp = _cliente(DocenteFactory()).post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                                           {'id_proyecto': proyecto.pk}, format='json')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_clonar_sin_proyecto_400_y_no_plantilla_404():
    docente = DocenteFactory()
    plantilla = _rubrica(docente, es_plantilla=True, nombre_plantilla='Base')
    no_plantilla = _rubrica(docente)
    c = _cliente(docente)
    assert c.post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/', {}, format='json').status_code == 400
    assert c.post(f'/api/rubricas/plantillas/{no_plantilla.pk}/clonar/',
                  {'id_proyecto': ProyectoFactory().pk}, format='json').status_code == 404
