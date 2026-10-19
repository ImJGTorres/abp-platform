"""
HU-044 — SCRUM-568: Prueba de aceptación del banco de rúbricas.

Recorre el flujo completo de la tarjeta con las mismas llamadas que hará la
interfaz: un docente crea una rúbrica y la guarda en el banco, otro docente
la toma del catálogo, crea su rúbrica desde la plantilla, la edita y la
plantilla original no cambia. Guardar con ponderaciones al 90 % queda
bloqueado con el mensaje de la suma.

Nota de alcance: la tarjeta pide frontend/cypress/e2e/hu044-plantillas.cy.js,
pero el catálogo y la clonación en la interfaz (SCRUM-565 y SCRUM-566, de
Ovallos) todavía no están en develop ni en ninguna rama remota: no hay ningún
componente de plantillas bajo frontend/src. Por eso esta prueba cubre la
aceptación sobre la API (lo verificable hoy). La verificación visual queda
pendiente para cuando SCRUM-566 esté en develop.
"""
import pytest
from rest_framework.test import APIClient

from apps.evaluacion.models import Rubrica
from tests.factories import DocenteFactory, ProyectoFactory, UsuarioFactory


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _criterio(nombre, peso, desc_alto='Cumple totalmente'):
    return {
        'nombre': nombre,
        'descripcion': f'Evalúa {nombre.lower()}',
        'peso_porcentual': peso,
        'niveles': [
            {'nivel': 1, 'etiqueta': 'insuficiente', 'descripcion': 'No cumple', 'puntos': 1},
            {'nivel': 4, 'etiqueta': 'excelente', 'descripcion': desc_alto, 'puntos': 5},
        ],
    }


RUBRICA = {
    'nombre': 'Rúbrica sustentación final',
    'descripcion': 'Sustentación del proyecto integrador',
    'criterios': [_criterio('Dominio del tema', 50), _criterio('Claridad', 30), _criterio('Tiempo', 20)],
}


def _resumen(rubrica_json):
    return sorted(
        (c['nombre'], float(c['peso_porcentual']),
         tuple(sorted((n['nivel'], n['descripcion'], n['puntos']) for n in c['niveles'])))
        for c in rubrica_json['criterios']
    )


@pytest.mark.django_db
def test_ca01_crear_rubrica_desde_plantilla_editarla_y_la_original_no_cambia():
    autor = DocenteFactory()
    proyecto = ProyectoFactory()
    docente = proyecto.id_curso.id_docente  # otro docente, dueño del curso del proyecto
    c_autor, c_docente = _cliente(autor), _cliente(docente)

    # 1. El autor crea la rúbrica y la guarda en el banco
    resp = c_autor.post('/api/rubricas/', RUBRICA, format='json')
    assert resp.status_code == 201, resp.data
    id_original = Rubrica.objects.get(nombre=RUBRICA['nombre']).pk
    resp = c_autor.patch(f'/api/rubricas/{id_original}/guardar-plantilla/',
                         {'nombre_plantilla': 'Sustentación ABP'}, format='json')
    assert resp.status_code == 200

    # 2. Otro docente la ve en el catálogo con su estructura completa
    catalogo = c_docente.get('/api/rubricas/plantillas/')
    assert catalogo.status_code == 200
    plantilla = next(p for p in catalogo.data if p['id'] == id_original)
    assert plantilla['nombre_plantilla'] == 'Sustentación ABP'
    estructura_original = _resumen(plantilla)
    assert len(estructura_original) == 3

    # 3. Crea su rúbrica del proyecto desde la plantilla
    resp = c_docente.post(f'/api/rubricas/plantillas/{id_original}/clonar/',
                          {'id_proyecto': proyecto.pk}, format='json')
    assert resp.status_code == 201
    copia = resp.data
    assert copia['id'] != id_original
    assert copia['id_proyecto'] == proyecto.pk and copia['id_docente'] == docente.pk
    assert _resumen(copia) == estructura_original

    # 4. La edita: cambia nombre, pesos, descripciones y agrega un criterio
    edicion = {
        'nombre': 'Sustentación grupo B',
        'descripcion': 'Versión ajustada',
        'criterios': [_criterio('Dominio del tema', 40, desc_alto='Responde todo'),
                      _criterio('Claridad', 30), _criterio('Tiempo', 10), _criterio('Material de apoyo', 20)],
    }
    resp = c_docente.put(f'/api/rubricas/{copia["id"]}/', edicion, format='json')
    assert resp.status_code == 200, resp.data
    detalle_copia = c_docente.get(f'/api/rubricas/{copia["id"]}/').data
    assert detalle_copia['nombre'] == 'Sustentación grupo B' and len(detalle_copia['criterios']) == 4

    # 5. La plantilla original no cambió (ni para el autor ni en el catálogo)
    original = c_autor.get(f'/api/rubricas/{id_original}/').data
    assert original['nombre'] == RUBRICA['nombre']
    assert original['es_plantilla'] is True
    assert _resumen(original) == estructura_original
    catalogo = c_docente.get('/api/rubricas/plantillas/').data
    assert [p['id'] for p in catalogo] == [id_original]
    assert _resumen(catalogo[0]) == estructura_original


@pytest.mark.django_db
def test_ca02_guardar_con_ponderaciones_al_90_queda_bloqueado_con_mensaje_de_suma():
    docente = DocenteFactory()
    c = _cliente(docente)

    # Al crear con 90 % se bloquea con el mensaje de la suma
    al_90 = {**RUBRICA, 'criterios': [_criterio('Dominio del tema', 50), _criterio('Claridad', 40)]}
    resp = c.post('/api/rubricas/', al_90, format='json')
    assert resp.status_code == 400
    assert 'Suma actual: 90' in str(resp.data['criterios'])
    assert not Rubrica.objects.filter(id_docente=docente).exists()

    # Al editar la copia a 90 % también se bloquea y la copia conserva su 100 %
    assert c.post('/api/rubricas/', RUBRICA, format='json').status_code == 201
    plantilla_id = Rubrica.objects.get(id_docente=docente).pk
    assert c.patch(f'/api/rubricas/{plantilla_id}/guardar-plantilla/', {}, format='json').status_code == 200
    proyecto = ProyectoFactory(id_curso__id_docente=docente)
    copia_id = c.post(f'/api/rubricas/plantillas/{plantilla_id}/clonar/',
                      {'id_proyecto': proyecto.pk}, format='json').data['id']
    resp = c.put(f'/api/rubricas/{copia_id}/', al_90, format='json')
    assert resp.status_code == 400
    assert 'Suma actual: 90' in str(resp.data['criterios'])
    pesos = [float(cr['peso_porcentual']) for cr in c.get(f'/api/rubricas/{copia_id}/').data['criterios']]
    assert sum(pesos) == 100

    # Y guardar como plantilla una rúbrica que suma 90 % (datos heredados) se bloquea con la suma actual
    heredada = Rubrica.objects.get(pk=copia_id)
    criterio = heredada.criterios.get(nombre='Tiempo')
    criterio.peso_porcentual = 10
    criterio.save()
    resp = c.patch(f'/api/rubricas/{copia_id}/guardar-plantilla/', {'nombre_plantilla': 'Mala'}, format='json')
    assert resp.status_code == 400
    assert 'debe ser 100 %' in resp.data['detail'] and 'Suma actual: 90' in resp.data['detail']
    assert Rubrica.objects.filter(es_plantilla=True).count() == 1


@pytest.mark.django_db
def test_ca03_estudiante_no_accede_al_banco_de_plantillas():
    c = _cliente(UsuarioFactory())
    assert c.get('/api/rubricas/plantillas/').status_code == 403
