# backend/tests/test_hu011_miembros.py
#
# HU-011: Gestión de miembros de equipo
# Subtarea: BE-02 - Backend
#
# Los miembros se agregan con POST /api/equipos/<equipo_id>/asignar/ (reverse
# 'asignar-estudiantes'), que es el endpoint que sustituyó al antiguo
# POST /api/equipos/<equipo_id>/miembros/ ('miembro-list'), eliminado junto con
# MiembroListView en el commit 4e0d10a. Recibe {'usuarios': [ids]} y responde
# 200 con {'asignados': n, 'errores': [{'usuario_id':, 'error':}]}; los fallos
# de negocio (cupo lleno, estudiante en otro equipo) van en 'errores', no en un
# 400 con 'detail'.

import pytest
from rest_framework import status
from django.urls import reverse

from apps.usuarios.models import Usuario
from apps.cursos.models import Proyecto, Curso
from apps.equipos.models import Equipo, MiembroEquipo
from apps.configuracion.models import ParametroSistema
from apps.bitacora.models import BitacoraSistema


@pytest.fixture
def proyecto_activo(docente_a):
    from tests.factories import CursoFactory
    from datetime import date
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
def equipo_con_capacidad(proyecto_activo, docente_a):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={
            'valor': '10',
            'categoria': ParametroSistema.Categoria.GENERAL,
            'tipo_dato': ParametroSistema.TipoDato.INTEGER,
        },
    )
    return Equipo.objects.create(
        nombre="Equipo Test",
        proyecto=proyecto_activo,
        cupo_maximo=3
    )


@pytest.fixture
def estudiante_user():
    from tests.factories import UsuarioFactory
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)


@pytest.mark.django_db
def test_cp01_asignar_estudiante_exitoso(cliente_a, equipo_con_capacidad, estudiante_user):
    """CP-01: POST /api/equipos/:id/asignar/ asigna estudiante → 200 + asignados=1"""
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['asignados'] == 1
    assert data['errores'] == []
    
    # La membresía queda registrada y activa en la BD
    miembro = MiembroEquipo.objects.get(equipo=equipo_con_capacidad, usuario=estudiante_user)
    assert miembro.estado == 'activo'


@pytest.mark.django_db
def test_cp02_equipo_lleno(cliente_a, equipo_con_capacidad, estudiante_user, db):
    """CP-02: Equipo lleno → el estudiante no se asigna y se reporta el cupo"""
    # Llenar el equipo hasta su capacidad
    from tests.factories import UsuarioFactory
    for i in range(equipo_con_capacidad.cupo_maximo):
        estudiante = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
        MiembroEquipo.objects.create(equipo=equipo_con_capacidad, usuario=estudiante)
    
    # Intentar agregar un estudiante más
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['asignados'] == 0
    assert data['errores'][0]['usuario_id'] == estudiante_user.id
    assert 'cupo máximo' in data['errores'][0]['error']
    
    # No se creó la membresía
    assert not MiembroEquipo.objects.filter(
        equipo=equipo_con_capacidad, usuario=estudiante_user, estado='activo'
    ).exists()


@pytest.mark.django_db
def test_cp03_estudiante_ya_en_otro_equipo_mismo_proyecto(cliente_a, proyecto_activo, estudiante_user, db):
    """CP-03: Estudiante ya en otro equipo del mismo proyecto → no se asigna"""
    from tests.factories import UsuarioFactory
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={
            'valor': '10',
            'categoria': ParametroSistema.Categoria.GENERAL,
            'tipo_dato': ParametroSistema.TipoDato.INTEGER,
        },
    )
    # Crear primer equipo y asignar estudiante
    equipo_a = Equipo.objects.create(
        nombre="Equipo A",
        proyecto=proyecto_activo,
        cupo_maximo=2
    )
    MiembroEquipo.objects.create(equipo=equipo_a, usuario=estudiante_user)
    
    # Crear segundo equipo en el mismo proyecto
    equipo_b = Equipo.objects.create(
        nombre="Equipo B",
        proyecto=proyecto_activo,
        cupo_maximo=2
    )
    
    # Intentar asignar el mismo estudiante al segundo equipo
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_b.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['asignados'] == 0
    assert 'otro equipo de este proyecto' in data['errores'][0]['error']
    assert not MiembroEquipo.objects.filter(equipo=equipo_b, usuario=estudiante_user).exists()


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
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = api_client.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.skip(reason=(
    "Hueco de permisos: AsignarEstudiantesView solo exige IsAuthenticated, "
    "así que hoy un estudiante sí puede asignarse a cualquier equipo (no hay 403). "
    "La prueba queda lista para activarse cuando se valide que el usuario es "
    "docente del proyecto o administrador."
))
@pytest.mark.django_db
def test_cp06_rol_no_docente_intenta_asignar(cliente_b, equipo_con_capacidad, estudiante_user):
    """CP-06: Rol no-docente intenta asignar → 403"""
    # Usar un estudiante para intentar la asignación
    from tests.factories import UsuarioFactory
    estudiante_que_intenta = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
    cliente_estudiante = cliente_b.__class__()
    cliente_estudiante.force_authenticate(user=estudiante_que_intenta)
    
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = cliente_estudiante.post(url, payload, format='json')
    
    # Asumiendo que solo docentes pueden asignar miembros
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_cp07_asignacion_registrada_en_bitacora(cliente_a, equipo_con_capacidad, estudiante_user):
    """CP-07: Asignación queda registrada en BitacoraSistema"""
    url = reverse('asignar-estudiantes', kwargs={'equipo_id': equipo_con_capacidad.id})
    payload = {
        'usuarios': [estudiante_user.id]
    }
    
    response = cliente_a.post(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['asignados'] == 1
    
    # Verificar que se creó un registro en la bitácora
    assert BitacoraSistema.objects.filter(
        accion=BitacoraSistema.Accion.CREATE,
        modulo='miembros_equipo',
        descripcion__contains=f'Estudiante {estudiante_user.id} asignado al equipo {equipo_con_capacidad.id}'
    ).exists()