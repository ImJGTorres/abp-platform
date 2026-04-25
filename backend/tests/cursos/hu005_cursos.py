import pytest
from rest_framework.test import APIClient
from tests.factories import (
    DocenteFactory,
    CursoFactory,
    ProyectoFactory,
    PeriodoAcademicoFactory,
)

@pytest.mark.django_db
def test_crear_curso_exitoso(cliente_a, periodo_activo):
    data = {
        "nombre": "Ingeniería de Software I",
        "codigo": "IS-101",
        "id_periodo_academico": periodo_activo.id,
    }
    response = cliente_a.post("/api/cursos/", data)
    assert response.status_code == 201
    assert response.data["codigo"] == "IS-101"


@pytest.mark.django_db
def test_codigo_duplicado_mismo_periodo_retorna_400(cliente_a, docente_a, periodo_activo):
    CursoFactory(
        codigo="IS-101",
        id_periodo_academico=periodo_activo,
        id_docente=docente_a,
        usuario_creo=docente_a,
    )
    data = {
        "nombre": "Otro Curso",
        "codigo": "IS-101",
        "id_periodo_academico": periodo_activo.id,
    }
    response = cliente_a.post("/api/cursos/", data)
    assert response.status_code == 400


@pytest.mark.django_db
def test_docente_no_propietario_no_puede_editar_retorna_403(cliente_a, cliente_b, docente_a, periodo_activo):
    curso = CursoFactory(
        id_docente=docente_a,
        usuario_creo=docente_a,
        id_periodo_academico=periodo_activo,
    )
    url = f"/api/cursos/{curso.id}/"
    data = {"nombre": "Nombre Modificado"}
    response = cliente_b.put(url, data)
    print(response.data)
    assert response.status_code == 404


@pytest.mark.django_db
def test_eliminar_curso_con_proyecto_retorna_409(cliente_a, docente_a, periodo_activo):
    curso = CursoFactory(
        id_docente=docente_a,
        usuario_creo=docente_a,
        id_periodo_academico=periodo_activo,
    )
    ProyectoFactory(id_curso=curso)
    url = f"/api/cursos/{curso.id}/"
    response = cliente_a.delete(url)
    assert response.status_code == 409
