# backend/tests/test_hu011_miembros.py
#
# HU-011: Gestión de miembros de equipo
# Subtarea: BE-02 - Backend

import pytest
from rest_framework import status
from django.urls import reverse

from apps.usuarios.models import Usuario
from apps.cursos.models import Proyecto
from apps.equipos.models import Equipo, MiembroEquipo
from apps.configuracion.models import ParametroSistema
from apps.bitacora.models import BitacoraSistema


@pytest.fixture
def proyecto_activo(docente_user):
    """Crea un proyecto activo para testing"""
    return Proyecto.objects.create(
        nombre="Proyecto Test",
        codigo="PT001",
        id_curso_id=1,
        usuario_creo=docente_user,
        estado=Proyecto.Estado.ACTIVO
    )


@pytest.fixture
def equipo_con_capacidad(proyecto_activo, docente_user):
    """Crea un equipo con capacidad disponible"""
    return Equipo.objects.create(
        nombre="Equipo Test",
        proyecto=proyecto_activo,
        cupo_maximo=3,
        usuario_creo=docente_user
    )


@pytest.fixture
def estudiante_user():
    """Crea un usuario estudiante para testing"""
    from tests.factories import UsuarioFactory
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)


@pytest.mark.django_db
def test_cp01_asignar_estudiante_exitoso(cliente_a, equipo_con_capacidad, estudiante_user):
    """CP-01: POST /api/equipos/:id/miembros/ asigna estudiante → 201"""
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'id' in data
    assert data['equipo_id'] == equipo_con_capacidad.id
    assert data['estudiante_id'] == estudiante_user.id
    assert data['nombre_estudiante'] == f"{estudiante_user.nombre} {estudiante_user.apellido}".strip()


@pytest.mark.django_db
def test_cp02_equipo_lleno(cliente_a, equipo_con_capacidad, estudiante_user, db):
    """CP-02: Equipo lleno → 400"""
    # Llenar el equipo hasta su capacidad
    from tests.factories import UsuarioFactory
    for i in range(equipo_con_capacidad.cupo_maximo):
        estudiante = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
        MiembroEquipo.objects.create(equipo=equipo_con_capacidad, usuario=estudiante)
    
    # Intentar agregar un estudiante más
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in response.json()
    assert 'cupo mǭximo' in response.json()['detail']


@pytest.mark.django_db
def test_cp03_estudiante_ya_en_otro_equipo_mismo_proyecto(cliente_a, proyecto_activo, estudiante_user, db):
    """CP-03: Estudiante ya en otro equipo del mismo proyecto → 400"""
    from tests.factories import UsuarioFactory
    
    # Crear primer equipo y asignar estudiante
    equipo_a = Equipo.objects.create(
        nombre="Equipo A",
        proyecto=proyecto_activo,
        cupo_maximo=2,
        usuario_creo=cliente_a.handler._force_user  # Get the authenticated user
    )
    MiembroEquipo.objects.create(equipo=equipo_a, usuario=estudiante_user)
    
    # Crear segundo equipo en el mismo proyecto
    equipo_b = Equipo.objects.create(
        nombre="Equipo B",
        proyecto=proyecto_activo,
        cupo_maximo=2,
        usuario_creo=cliente_a.handler._force_user
    )
    
    # Intentar asignar el mismo estudiante al segundo equipo
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_b.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in response.json()
    assert 'otro equipo en este proyecto' in response.json()['detail']


@pytest.mark.django_db
def test_cp04_retirar_miembro_exitoso(cliente_a, equipo_con_capacidad, estudiante_user):
    """CP-04: DELETE /api/equipos/:id/miembros/:usuario_id/ retira estudiante → 204"""
    # Primero asignar un estudiante al equipo
    miembro = MiembroEquipo.objects.create(equipo=equipo_con_capacidad, usuario=estudiante_user)
    
    # Verificar que el equipo tiene un miembro
    assert MiembroEquipo.objects.filter(equipo=equipo_con_capacidad, estado='activo').count() == 1
    
    # Retirar el miembro
    url = reverse('miembro-retirar', kwargs={
        'equipo_id': equipo_con_capacidad.id,
        'usuario_id': estudiante_user.id
    })
    
    response = cliente_a.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verificar que el miembro fue marcado como retirado
    miembro.refresh_from_db()
    assert miembro.estado == 'retirado'
    
    # Verificar que el equipo ya no tiene miembros activos
    assert MiembroEquipo.objects.filter(equipo=equipo_con_capacidad, estado='activo').count() == 0


@pytest.mark.django_db
def test_cp05_sin_autenticacion(api_client, equipo_con_capacidad, estudiante_user):
    """CP-05: Sin autenticación → 401"""
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_cp06_rol_no_docente_intenta_asignar(cliente_b, equipo_con_capacidad, estudiante_user):
    """CP-06: Rol no-docente intenta asignar → 403"""
    # Usar un estudiante para intentar la asignación
    from tests.factories import UsuarioFactory
    estudiante_que_intenta = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
    cliente_estudiante = cliente_b.__class__()
    cliente_estudiante.force_authenticate(user=estudiante_que_intenta)
    
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = cliente_estudiante.post(url, payload, format='json')
    
    # Asumiendo que solo docentes pueden asignar miembros
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_cp07_asignacion_registrada_en_bitacora(cliente_a, equipo_con_capacidad, estudiante_user):
    """CP-07: Asignación queda registrada en BitacoraSistema"""
    url = reverse('miembro-list', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'estudiante_id': estudiante_user.id
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar que se creó un registro en la bitácora
    assert BitacoraSistema.objects.filter(
        accion=BitacoraSistema.Accion.CREATE,
        modulo='miembros_equipo',
        descripcion__contains=f'Estudiante {estudiante_user.id} asignado al equipo {equipo_con_capacidad.id}'
    ).exists()