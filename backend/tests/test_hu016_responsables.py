import pytest
from rest_framework import status
from django.urls import reverse
from datetime import date
from apps.bitacora.models import BitacoraSistema
from apps.usuarios.models import Usuario
from apps.cursos.models import Proyecto, Curso, FaseProyecto, Actividad
from apps.equipos.models import Equipo, MiembroEquipo
from apps.configuracion.models import ParametroSistema
from tests.factories import UsuarioFactory, ProyectoFactory, FaseProyectoFactory, EquipoFactory, MiembroEquipoFactory, ActividadFactory


@pytest.fixture
def setup_hu016():
    """Setup común para todos los tests de HU-016."""
    ParametroSistema.objects.create(
        clave='max_estudiantes_por_equipo',
        valor='10',
        categoria=ParametroSistema.Categoria.GENERAL,
        tipo_dato=ParametroSistema.TipoDato.INTEGER
    )


@pytest.fixture
def proyecto_con_fase(setup_hu016):
    proyecto = ProyectoFactory(
        estado=Proyecto.Estado.EN_EJECUCION
    )

    fase = FaseProyectoFactory(
        id_proyecto=proyecto,
        orden=1
    )

    return proyecto, fase

@pytest.fixture
def equipo_con_lider_y_miembros(proyecto_con_fase):
    proyecto, fase = proyecto_con_fase

    lider = UsuarioFactory(
        tipo_rol=Usuario.TipoRol.LIDER_EQUIPO
    )

    equipo = EquipoFactory(
        proyecto=proyecto,
        cupo_maximo=4
    )

    MiembroEquipoFactory(
        equipo=equipo,
        usuario=lider,
        rol_interno='lider'
    )

    miembros = MiembroEquipoFactory.create_batch(
        3,
        equipo=equipo,
        estado='activo'
    )

    usuarios_miembros = [m.usuario for m in miembros]

    actividad = ActividadFactory(
        id_fase=fase,
        id_equipo_asignado=equipo
    )

    return {
        'proyecto': proyecto,
        'fase': fase,
        'equipo': equipo,
        'lider': lider,
        'miembros': usuarios_miembros,
        'actividad': actividad
    }

@pytest.fixture
def cliente_lider(api_client, equipo_con_lider_y_miembros):
    """Cliente autenticado como líder de equipo."""
    api_client.force_authenticate(user=equipo_con_lider_y_miembros['lider'])
    return api_client


@pytest.fixture
def cliente_no_lider(api_client):
    """Cliente autenticado como usuario que NO es líder."""
    usuario = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.fixture
def usuario_externo():
    """Usuario que no pertenece al equipo."""
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)


# ==============================================================================
# CASOS DE PRUEBA
# ==============================================================================

@pytest.mark.django_db
def test_cp01_lider_asigna_responsable_exitosamente(
    cliente_lider, equipo_con_lider_y_miembros
):
    """CP-01: Líder asigna responsable → 200"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [miembro.id]}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    actividad.refresh_from_db()
    assert actividad.responsables.filter(id=miembro.id).exists()


@pytest.mark.django_db
def test_cp02_lider_asigna_multiples_responsables(
    cliente_lider, equipo_con_lider_y_miembros
):
    """CP-02: Líder asigna múltiples responsables → 200"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembros = equipo_con_lider_y_miembros['miembros']
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [m.id for m in miembros[:2]]}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert actividad.responsables.count() == 2


@pytest.mark.django_db
def test_cp03_no_lider_intenta_asignar_responsable(
    cliente_no_lider, equipo_con_lider_y_miembros
):
    """CP-03: No líder intenta asignar → 403"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [miembro.id]}
    
    response = cliente_no_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_cp04_responsable_no_pertenece_al_equipo(
    cliente_lider, equipo_con_lider_y_miembros, usuario_externo
):
    """CP-04: Responsable no pertenece al equipo → 400"""
    actividad = equipo_con_lider_y_miembros['actividad']
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [usuario_externo.id]}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'responsables' in response.json()


@pytest.mark.django_db
def test_cp05_responsable_retirado_equipo(
    cliente_lider, equipo_con_lider_y_miembros
):
    """CP-05: Miembro retirado no puede ser asignado → 400"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]
    
    membresia = MiembroEquipo.objects.get(equipo=actividad.id_equipo_asignado, usuario=miembro)
    membresia.estado = 'retirado'
    membresia.save()
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [miembro.id]}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_cp06_asignar_lista_vacia(cliente_lider, equipo_con_lider_y_miembros):
    """CP-06: Lista vacía de responsables → 200"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]
    
    actividad.responsables.add(miembro)
    assert actividad.responsables.count() == 1
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': []}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    actividad.refresh_from_db()
    assert actividad.responsables.count() == 0


@pytest.mark.django_db
def test_cp07_responsables_visualizan_actividades_asignadas(
    equipo_con_lider_y_miembros, api_client
):
    """CP-07: Responsables visualizan actividades asignadas → 200"""
    equipo = equipo_con_lider_y_miembros['equipo']
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]
    
    actividad.responsables.add(miembro)
    
    api_client.force_authenticate(user=miembro)
    url = reverse('actividades-por-equipo', kwargs={'equipo_id': equipo.id})
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    actividad_data = next((a for a in data if a['id'] == actividad.id), None)
    assert actividad_data is not None
    assert actividad_data['es_responsable'] is True


@pytest.mark.django_db
def test_cp08_actividad_sin_equipo_asignado(cliente_lider, proyecto_con_fase):
    """CP-08: Actividad sin equipo → 404 (get_object_or_404)"""
    _, fase = proyecto_con_fase
    
    actividad = Actividad.objects.create(
        id_fase=fase,
        nombre="Actividad sin equipo",
        fecha_limite=date(2026, 3, 15),
        prioridad='media',
        estado='pendiente'
    )
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': []}
    
    response = cliente_lider.patch(url, payload, format='json')
    
    # 404 porque get_object_or_404 no encuentra la actividad con el filtro del equipo
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cp09_sobrescribir_responsables(
    cliente_lider, equipo_con_lider_y_miembros
):
    """CP-09: Reasignar responsables → 200"""
    actividad = equipo_con_lider_y_miembros['actividad']
    miembros = equipo_con_lider_y_miembros['miembros']
    
    url = reverse('actividad-asignar', kwargs={'pk': actividad.id})
    payload = {'responsables': [miembros[0].id, miembros[1].id]}
    response = cliente_lider.patch(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert actividad.responsables.count() == 2
    
    payload = {'responsables': [miembros[2].id]}
    response = cliente_lider.patch(url, payload, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    actividad.refresh_from_db()
    assert actividad.responsables.count() == 1
    assert actividad.responsables.filter(id=miembros[2].id).exists()


@pytest.mark.django_db
def test_cp10_notificacion_actividad_sin_responsable_al_eliminar_miembro(
    equipo_con_lider_y_miembros
):
    equipo = equipo_con_lider_y_miembros['equipo']
    actividad = equipo_con_lider_y_miembros['actividad']
    miembro = equipo_con_lider_y_miembros['miembros'][0]

    actividad.id_responsable = miembro
    actividad.save()

    membresia = MiembroEquipo.objects.get(equipo=equipo, usuario=miembro)
    membresia.estado = 'retirado'
    membresia.save()  # ← dispara post_save → signal

    actividad.refresh_from_db()
    assert actividad.id_responsable is None

    assert BitacoraSistema.objects.filter(
        accion='actividad_sin_responsable',
        modulo='equipos',
    ).exists()


@pytest.mark.django_db
def test_cp11_save_sin_retiro_no_genera_notificacion(equipo_con_lider_y_miembros):
    equipo = equipo_con_lider_y_miembros['equipo']
    miembro = equipo_con_lider_y_miembros['miembros'][0]

    membresia = MiembroEquipo.objects.get(equipo=equipo, usuario=miembro)
    membresia.descripcion_responsabilidades = 'actualizado'
    membresia.save()

    assert not BitacoraSistema.objects.filter(accion='actividad_sin_responsable').exists()