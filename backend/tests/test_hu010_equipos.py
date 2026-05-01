# backend/tests/test_hu010_equipos.py
#
# HU-010: Creación de equipos en un proyecto
# Subtarea: BE-02 - Backend

import pytest
from rest_framework import status
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.usuarios.models import Usuario
from apps.cursos.models import Proyecto, Curso
from apps.configuracion.models import ParametroSistema
from apps.bitacora.models import BitacoraSistema


@pytest.fixture
def proyecto_activo(docente_a):
    """Crea un proyecto activo para testing"""
    # Primero crear un curso (requerido para Proyecto)
    curso = Curso.objects.create(
        nombre="Curso Test",
        codigo="CT001",
        id_docente=docente_a,
        id_periodo_academico_id=1,  # Asumimos que existe un período académico con ID 1
        usuario_creo=docente_a,
        estado=Curso.Estado.ACTIVO
    )
    
    # Luego crear el proyecto asociado al curso
    return Proyecto.objects.create(
        nombre="Proyecto Test",
        id_curso=curso,
        fecha_inicio=parse_date("2026-02-01"),
        fecha_fin_estimada=parse_date("2026-05-31"),
        estado=Proyecto.Estado.EN_EJECUCION  # Proyecto en ejecución
    )


@pytest.mark.django_db
def test_cp01_crear_equipo_exitoso(cliente_a, proyecto_activo):
    """CP-01: POST /api/proyectos/:id/equipos/ crea equipo → 201"""
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload = {
        'nombre': 'Equipo Alpha',
        'descripcion': 'Equipo de prueba',
        'cupo_maximo': 4
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'id' in data
    assert data['nombre'] == 'Equipo Alpha'
    assert data['cupo_maximo'] == 4
    assert data['proyecto'] == proyecto_activo.id


@pytest.mark.django_db
def test_cp02_nombre_duplicado_mismo_proyecto(cliente_a, proyecto_activo):
    """CP-02: Nombre duplicado en el mismo proyecto → 400"""
    # Crear primer equipo
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload1 = {
        'nombre': 'Equipo Alpha',
        'cupo_maximo': 4
    }
    cliente_a.post(url, payload1, format='json')
    
    # Intentar crear segundo equipo con mismo nombre
    payload2 = {
        'nombre': 'Equipo Alpha',  # Mismo nombre
        'cupo_maximo': 3
    }
    response = cliente_a.post(url, payload2, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'nombre' in response.json()


@pytest.mark.django_db
def test_cp03_capacidad_maxima_excede_parametro_sistema(cliente_a, proyecto_activo, db):
    """CP-03: capacidad_maxima excede parámetro del sistema → 400"""
    # Configurar parámetro del sistema
    ParametroSistema.objects.create(
        clave='max_estudiantes_por_equipo',
        valor='5',
        descripcion='Máximo número de estudiantes por equipo'
    )
    
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload = {
        'nombre': 'Equipo Grande',
        'cupo_maximo': 10  # Excede el límite de 5
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'cupo_maximo' in response.json()


@pytest.mark.django_db
def test_cp04_usuario_no_docente_intenta_crear_equipo(cliente_b, proyecto_activo):
    """CP-04: Usuario no-docente intenta crear equipo → 403"""
    # Usar estudiante para probar falta de permisos
    from tests.factories import UsuarioFactory
    estudiante = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
    cliente_estudiante = cliente_b.__class__()
    cliente_estudiante.force_authenticate(user=estudiante)
    
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload = {
        'nombre': 'Equipo Estudiante',
        'cupo_maximo': 4
    }
    
    response = cliente_estudiante.post(url, payload, format='json')
    
    # Asumiendo que solo docentes pueden crear equipos
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_cp05_sin_autenticacion(api_client, proyecto_activo):
    """CP-05: Sin autenticación → 401"""
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload = {
        'nombre': 'Equipo Sin Auth',
        'cupo_maximo': 4
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_cp06_creado_registrado_en_bitacora(cliente_a, proyecto_activo):
    """CP-06: Creación queda registrada en BitacoraSistema"""
    url = reverse('equipos-por-proyecto', kwargs={'proyecto_id': proyecto_activo.id})
    payload = {
        'nombre': 'Equipo Bitacora',
        'cupo_maximo': 4
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar que se creó un registro en la bitácora
    assert BitacoraSistema.objects.filter(
        accion=BitacoraSistema.Accion.CREATE,
        modulo='equipos',
        descripcion__contains='Equipo Bitacora'
    ).exists()