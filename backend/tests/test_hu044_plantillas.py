"""
HU-044 — SCRUM-567: Pruebas unitarias del backend del banco de rúbricas.

Cubre los cuatro servicios de la HU sobre la API real:
  - Guardar como plantilla   PATCH /api/rubricas/:id/guardar-plantilla/   (SCRUM-561)
  - Catálogo de plantillas   GET   /api/rubricas/plantillas/              (SCRUM-562)
  - Clonar plantilla         POST  /api/rubricas/plantillas/:id/clonar/   (SCRUM-563)
  - Ponderaciones = 100 %    validar_ponderaciones()                      (SCRUM-564)

Complementa a tests/test_hu044_banco_rubricas.py (pruebas de desarrollo de
SCRUM-561 a 564): aquí se prueban los criterios de aceptación de la tarjeta
de SCRUM-567 (guardar → 200, clonar con mismos criterios e ids distintos,
copia independiente, suma ≠ 100 → 400, estudiante → 403) y sus bordes.
"""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.evaluacion.models import CriterioRubrica, NivelDesempeno, Rubrica
from apps.evaluacion.services import clonar_rubrica, validar_ponderaciones
from apps.usuarios.models import Usuario
from tests.factories import AdminFactory, DocenteFactory, ProyectoFactory, UsuarioFactory


def _cliente(usuario=None):
    c = APIClient()
    if usuario is not None:
        c.force_authenticate(user=usuario)
    return c


def _rubrica(docente, pesos=(60, 40), **kwargs):
    """Rúbrica con un criterio por peso y dos niveles de desempeño por criterio."""
    rubrica = Rubrica.objects.create(id_docente=docente, nombre='Rúbrica de exposición',
                                     descripcion='Evalúa la exposición final', **kwargs)
    for i, peso in enumerate(pesos):
        criterio = CriterioRubrica.objects.create(id_rubrica=rubrica, nombre=f'Criterio {i}',
                                                  descripcion=f'Descripción {i}', peso_porcentual=peso)
        NivelDesempeno.objects.create(id_criterio=criterio, nivel=1, etiqueta='insuficiente',
                                      descripcion='No cumple', puntos=1)
        NivelDesempeno.objects.create(id_criterio=criterio, nivel=4, etiqueta='excelente',
                                      descripcion='Cumple totalmente', puntos=5)
    return rubrica


def _plantilla(docente=None, pesos=(60, 40), nombre='Plantilla base'):
    return _rubrica(docente or DocenteFactory(), pesos=pesos, es_plantilla=True, nombre_plantilla=nombre)


def _guardar(usuario, rubrica, nombre='Plantilla ABP'):
    return _cliente(usuario).patch(f'/api/rubricas/{rubrica.pk}/guardar-plantilla/',
                                   {'nombre_plantilla': nombre}, format='json')


def _clonar(usuario, plantilla, proyecto):
    return _cliente(usuario).post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                                  {'id_proyecto': proyecto.pk}, format='json')


def _estructura(rubrica):
    """Criterios y niveles comparables entre plantilla y copia (sin ids)."""
    return sorted(
        (c.nombre, c.descripcion, c.peso_porcentual,
         tuple(sorted(c.niveles.values_list('nivel', 'etiqueta', 'descripcion', 'puntos'))))
        for c in rubrica.criterios.all()
    )


# ── Guardar como plantilla (SCRUM-561) ───────────────────────────────────────

@pytest.mark.django_db
def test_guardar_plantilla_200_persiste_y_registra_bitacora():
    docente = DocenteFactory()
    rubrica = _rubrica(docente)

    resp = _guardar(docente, rubrica, nombre='  Plantilla exposición  ')

    assert resp.status_code == 200
    assert resp.data['es_plantilla'] is True
    assert resp.data['nombre_plantilla'] == 'Plantilla exposición'
    rubrica.refresh_from_db()
    assert rubrica.es_plantilla is True and rubrica.nombre_plantilla == 'Plantilla exposición'
    assert BitacoraSistema.objects.filter(modulo='rubricas', accion=BitacoraSistema.Accion.UPDATE,
                                          descripcion__contains=f'id={rubrica.pk}').exists()


@pytest.mark.django_db
def test_guardar_plantilla_sin_nombre_usa_nombre_de_la_rubrica():
    docente = DocenteFactory()
    rubrica = _rubrica(docente)
    resp = _guardar(docente, rubrica, nombre='')
    assert resp.status_code == 200
    assert resp.data['nombre_plantilla'] == 'Rúbrica de exposición'


@pytest.mark.django_db
def test_guardar_plantilla_nombre_mayor_200_caracteres_400():
    docente = DocenteFactory()
    rubrica = _rubrica(docente)
    resp = _guardar(docente, rubrica, nombre='x' * 201)
    assert resp.status_code == 400
    rubrica.refresh_from_db()
    assert rubrica.es_plantilla is False


@pytest.mark.django_db
def test_guardar_plantilla_rubrica_inexistente_404():
    resp = _cliente(DocenteFactory()).patch('/api/rubricas/999999/guardar-plantilla/',
                                            {'nombre_plantilla': 'X'}, format='json')
    assert resp.status_code == 404


# ── Validación de ponderaciones = 100 % (SCRUM-564) ──────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('pesos, suma', [((50, 40), '90'), ((60, 50), '110'), ((), '0')])
def test_guardar_plantilla_ponderaciones_distintas_de_100_400(pesos, suma):
    docente = DocenteFactory()
    rubrica = _rubrica(docente, pesos=pesos)

    resp = _guardar(docente, rubrica)

    assert resp.status_code == 400
    assert '100' in str(resp.data['detail']) and suma in str(resp.data['detail'])
    rubrica.refresh_from_db()
    assert rubrica.es_plantilla is False


@pytest.mark.django_db
def test_validar_ponderaciones_acepta_decimales_que_suman_100():
    rubrica = _rubrica(DocenteFactory(), pesos=(Decimal('33.33'), Decimal('33.33'), Decimal('33.34')))
    validar_ponderaciones(rubrica)  # no lanza


@pytest.mark.django_db
def test_validar_ponderaciones_99_99_lanza_validation_error():
    rubrica = _rubrica(DocenteFactory(), pesos=(Decimal('33.33'), Decimal('33.33'), Decimal('33.33')))
    with pytest.raises(ValidationError) as exc:
        validar_ponderaciones(rubrica)
    assert Decimal(str(exc.value.detail['suma_actual'])) == Decimal('99.99')


# ── Catálogo (SCRUM-562) ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_catalogo_lista_solo_plantillas_con_criterios_y_niveles():
    docente = DocenteFactory()
    p = _plantilla(docente, nombre='Exposición')
    _rubrica(docente)  # rúbrica normal: no debe aparecer

    resp = _cliente(AdminFactory()).get('/api/rubricas/plantillas/')

    assert resp.status_code == 200
    assert [r['id'] for r in resp.data] == [p.pk]
    criterios = resp.data[0]['criterios']
    assert sorted(Decimal(str(c['peso_porcentual'])) for c in criterios) == [Decimal('40'), Decimal('60')]
    assert all(len(c['niveles']) == 2 for c in criterios)


@pytest.mark.django_db
def test_catalogo_guardar_y_luego_aparece_en_el_listado():
    docente = DocenteFactory()
    rubrica = _rubrica(docente)
    assert _cliente(docente).get('/api/rubricas/plantillas/').data == []

    assert _guardar(docente, rubrica, nombre='Nueva').status_code == 200

    resp = _cliente(DocenteFactory()).get('/api/rubricas/plantillas/')  # otro docente también la ve
    assert [r['nombre_plantilla'] for r in resp.data] == ['Nueva']


# ── Clonar (SCRUM-563) ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_clonar_201_mismos_criterios_y_niveles_con_ids_distintos():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    docente_curso = proyecto.id_curso.id_docente

    resp = _clonar(docente_curso, plantilla, proyecto)

    assert resp.status_code == 201
    copia = Rubrica.objects.get(pk=resp.data['id'])
    assert copia.pk != plantilla.pk
    assert (copia.nombre, copia.descripcion) == (plantilla.nombre, plantilla.descripcion)
    assert _estructura(copia) == _estructura(plantilla)
    ids_plantilla = set(plantilla.criterios.values_list('id', flat=True))
    ids_copia = set(copia.criterios.values_list('id', flat=True))
    assert ids_copia and not ids_copia & ids_plantilla
    niveles_plantilla = set(NivelDesempeno.objects.filter(id_criterio__id_rubrica=plantilla).values_list('id', flat=True))
    niveles_copia = set(NivelDesempeno.objects.filter(id_criterio__id_rubrica=copia).values_list('id', flat=True))
    assert len(niveles_copia) == 4 and not niveles_copia & niveles_plantilla
    assert BitacoraSistema.objects.filter(modulo='rubricas', accion=BitacoraSistema.Accion.CREATE,
                                          descripcion__contains=f'rúbrica id={copia.pk}').exists()


@pytest.mark.django_db
def test_clonar_copia_queda_en_el_proyecto_y_no_es_plantilla():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    resp = _clonar(proyecto.id_curso.id_docente, plantilla, proyecto)
    assert resp.status_code == 201
    assert resp.data['es_plantilla'] is False and resp.data['nombre_plantilla'] is None
    assert resp.data['id_proyecto'] == proyecto.pk
    # La plantilla sigue en el catálogo una sola vez
    assert Rubrica.objects.filter(es_plantilla=True).count() == 1


@pytest.mark.django_db
def test_editar_la_copia_no_cambia_la_plantilla():
    plantilla = _plantilla()
    estructura_original = _estructura(plantilla)
    proyecto = ProyectoFactory()
    copia = Rubrica.objects.get(pk=_clonar(proyecto.id_curso.id_docente, plantilla, proyecto).data['id'])

    criterio = copia.criterios.first()
    criterio.nombre, criterio.peso_porcentual = 'Criterio editado', Decimal('70')
    criterio.save()
    NivelDesempeno.objects.filter(id_criterio=criterio).update(descripcion='Cambiado', puntos=3)
    CriterioRubrica.objects.create(id_rubrica=copia, nombre='Criterio extra', peso_porcentual=10)
    copia.nombre = 'Rúbrica editada'
    copia.save()

    plantilla.refresh_from_db()
    assert plantilla.nombre == 'Rúbrica de exposición'
    assert _estructura(plantilla) == estructura_original


@pytest.mark.django_db
def test_eliminar_la_copia_no_borra_la_plantilla():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    copia = Rubrica.objects.get(pk=_clonar(proyecto.id_curso.id_docente, plantilla, proyecto).data['id'])
    copia.delete()
    assert Rubrica.objects.filter(pk=plantilla.pk, es_plantilla=True).exists()
    assert plantilla.criterios.count() == 2


@pytest.mark.django_db
def test_clonar_dos_veces_genera_copias_independientes():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    docente = proyecto.id_curso.id_docente
    id1 = _clonar(docente, plantilla, proyecto).data['id']
    id2 = _clonar(docente, plantilla, proyecto).data['id']
    assert id1 != id2
    c1 = set(CriterioRubrica.objects.filter(id_rubrica_id=id1).values_list('id', flat=True))
    c2 = set(CriterioRubrica.objects.filter(id_rubrica_id=id2).values_list('id', flat=True))
    assert not c1 & c2


@pytest.mark.django_db
def test_clonar_como_admin_la_copia_pertenece_al_docente_del_curso():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    resp = _clonar(AdminFactory(), plantilla, proyecto)
    assert resp.status_code == 201
    assert resp.data['id_docente'] == proyecto.id_curso.id_docente_id


@pytest.mark.django_db
def test_clonar_plantilla_con_ponderaciones_invalidas_400_sin_crear_copia():
    plantilla = _plantilla(pesos=(50, 40))
    proyecto = ProyectoFactory()
    total_antes = Rubrica.objects.count()

    resp = _clonar(proyecto.id_curso.id_docente, plantilla, proyecto)

    assert resp.status_code == 400
    assert '90' in str(resp.data['detail'])
    assert Rubrica.objects.count() == total_antes


@pytest.mark.django_db
def test_servicio_clonar_rubrica_copia_campos_y_estructura():
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    docente = proyecto.id_curso.id_docente
    copia = clonar_rubrica(plantilla, proyecto.pk, docente)
    assert (copia.tipo, copia.peso_total) == (plantilla.tipo, plantilla.peso_total)
    assert (copia.id_proyecto_id, copia.id_docente_id) == (proyecto.pk, docente.pk)
    assert _estructura(copia) == _estructura(plantilla)


@pytest.mark.django_db
@pytest.mark.parametrize('id_proyecto', ['abc', -1, ''])
def test_clonar_id_proyecto_invalido_400(id_proyecto):
    plantilla = _plantilla()
    resp = _cliente(AdminFactory()).post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                                         {'id_proyecto': id_proyecto}, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_clonar_proyecto_inexistente_404():
    plantilla = _plantilla()
    resp = _cliente(AdminFactory()).post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                                         {'id_proyecto': 999999}, format='json')
    assert resp.status_code == 404


# ── Permisos ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('rol', [Usuario.TipoRol.ESTUDIANTE, Usuario.TipoRol.LIDER_EQUIPO,
                                 Usuario.TipoRol.DIRECTOR])
def test_roles_no_autorizados_403_en_los_tres_endpoints(rol):
    usuario = UsuarioFactory(tipo_rol=rol)
    rubrica = _rubrica(DocenteFactory())
    plantilla = _plantilla()
    proyecto = ProyectoFactory()

    assert _guardar(usuario, rubrica).status_code == 403
    assert _cliente(usuario).get('/api/rubricas/plantillas/').status_code == 403
    assert _clonar(usuario, plantilla, proyecto).status_code == 403
    rubrica.refresh_from_db()
    assert rubrica.es_plantilla is False
    assert not Rubrica.objects.filter(id_proyecto=proyecto).exists()


@pytest.mark.django_db
def test_sin_autenticacion_401_en_los_tres_endpoints():
    rubrica = _rubrica(DocenteFactory())
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    anonimo = _cliente()
    assert anonimo.patch(f'/api/rubricas/{rubrica.pk}/guardar-plantilla/', {}, format='json').status_code == 401
    assert anonimo.get('/api/rubricas/plantillas/').status_code == 401
    assert anonimo.post(f'/api/rubricas/plantillas/{plantilla.pk}/clonar/',
                        {'id_proyecto': proyecto.pk}, format='json').status_code == 401


@pytest.mark.django_db
def test_docente_no_dueno_no_puede_guardar_ni_clonar_en_curso_ajeno():
    rubrica = _rubrica(DocenteFactory())
    plantilla = _plantilla()
    proyecto = ProyectoFactory()
    intruso = DocenteFactory()
    assert _guardar(intruso, rubrica).status_code == 403
    assert _clonar(intruso, plantilla, proyecto).status_code == 403
    assert not Rubrica.objects.filter(id_proyecto=proyecto).exists()
