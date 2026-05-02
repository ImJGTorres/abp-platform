# backend/tests/test_hu012_roles.py
#
# HU-012: Roles de equipo
# Subtarea: BE-02 - Backend

import pytest
from rest_framework import status
from django.urls import reverse
from datetime import date

from apps.usuarios.models import Usuario
from apps.cursos.models import Proyecto, Curso
from apps.equipos.models import Equipo, MiembroEquipo


@pytest.fixture
def proyecto_activo(docente_a):
    """Crea un proyecto activo para testing"""
    from tests.factories import CursoFactory
    curso = CursoFactory(
        nombre="Curso Test",
        codigo="PT001",
        id_docente=docente_a,
        usuario_creo=docente_a
    )
    return Proyecto.objects.create(
        nombre="Proyecto Test",
        id_curso=curso,
        fecha_inicio=date(2026, 2, 1),
        fecha_fin_estimada=date(2026, 5, 31),
        estado=Proyecto.Estado.EN_EJECUCION
    )


@pytest.fixture
def equipo_con_estudiantes(proyecto_activo, docente_a):
    """Crea un equipo con estudiantes asignados"""
    from tests.factories import UsuarioFactory
    equipo = Equipo.objects.create(
        nombre="Equipo Test",
        proyecto=proyecto_activo,
        cupo_maximo=3
    )
    
    estudiantes = [UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE) for _ in range(2)]
    miembros = []
    for estudiante in estudiantes:
        miembro = MiembroEquipo.objects.create(equipo=equipo, usuario=estudiante)
        miembros.append(miembro)
    
    return equipo, estudiantes, miembros


@pytest.mark.django_db
def test_cp01_estudiante_define_propio_rol(cliente_a, equipo_con_estudiantes):
    """CP-01: PATCH miembros/:id_usuario/ — estudiante define su propio rol → 200"""
    equipo, estudiantes, miembros = equipo_con_estudiantes
    estudiante, _ = estudiantes
    
    # Autenticar como el estudiante
    from rest_framework.test import APIClient
    cliente_estudiante = APIClient()
    cliente_estudiante.force_authenticate(user=estudiante)
    
    url = reverse('miembro-rol', kwargs={
        'equipo_id': equipo.id,
        'usuario_id': estudiante.id
    })
    payload = {
        'rol_interno': 'lider'
    }
    
    response = cliente_estudiante.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['rol_interno'] == 'lider'


@pytest.mark.django_db
def test_cp02_dos_estudiantes_intentan_ser_lider(cliente_a, equipo_con_estudiantes):
    """CP-02: PATCH — dos estudiantes intentan ser Líder → 400 (ya hay un Líder en el equipo)"""
    equipo, estudiantes, miembros = equipo_con_estudiantes
    estudiante1, estudiante2 = estudiantes
    
    # Primer estudiante se hace líder
    from rest_framework.test import APIClient
    cliente_estudiante1 = APIClient()
    cliente_estudiante1.force_authenticate(user=estudiante1)
    
    url1 = reverse('miembro-rol', kwargs={
        'equipo_id': equipo.id,
        'usuario_id': estudiante1.id
    })
    cliente_estudiante1.patch(url1, {'rol_interno': 'lider'}, format='json')
    
    # Segundo estudiante intenta hacerse líder - debería fallar
    cliente_estudiante2 = APIClient()
    cliente_estudiante2.force_authenticate(user=estudiante2)
    
    url2 = reverse('miembro-rol', kwargs={
        'equipo_id': equipo.id,
        'usuario_id': estudiante2.id
    })
    response = cliente_estudiante2.patch(url2, {'rol_interno': 'lider'}, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'lider' in response.json()['detail'].lower() or 'rol' in response.json()['detail'].lower()


@pytest.mark.django_db
def test_cp03_estudiante_cambia_rol_compañero(cliente_a, equipo_con_estudiantes):
    """CP-03: PATCH — estudiante intenta cambiar rol de otro compañero → 403"""
    equipo, estudiantes, miembros = equipo_con_estudiantes
    estudiante1, estudiante2 = estudiantes
    
    # Estudiante 1 intenta cambiar el rol del estudiante 2
    from rest_framework.test import APIClient
    cliente_estudiante1 = APIClient()
    cliente_estudiante1.force_authenticate(user=estudiante1)
    
    url = reverse('miembro-rol', kwargs={
        'equipo_id': equipo.id,
        'usuario_id': estudiante2.id
    })
    response = cliente_estudiante1.patch(url, {'rol_interno': 'desarrollador'}, format='json')
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_cp04_docente_ve_roles(cliente_a, equipo_con_estudiantes):
    """CP-04: GET miembros/ — docente puede ver todos los roles → 200"""
    equipo, estudiantes, miembros = equipo_con_estudiantes
    
    url = reverse('estudiantes-equipo', kwargs={'equipo_id': equipo.id})
    response = cliente_a.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['ya_en_equipo']  # Al menos 2 estudiantes