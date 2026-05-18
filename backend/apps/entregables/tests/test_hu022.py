import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from apps.entregables.models import Entregable
from apps.cursos.models import Actividad, FaseProyecto, Proyecto, Curso
from apps.equipos.models import Equipo, MiembroEquipo
from apps.usuarios.models import Usuario


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def docente(db):
    """Usuario con rol Docente."""
    return Usuario.objects.create(
        nombre='Docente Test',
        apellido='Test',
        correo='docente@test.com',
        password='pbkdf2_sha256$test',
        tipo_rol=Usuario.TipoRol.DOCENTE,
        estado=Usuario.Estado.ACTIVO,
        fecha_creacion=timezone.now(),
        fecha_actualizacion=timezone.now(),
    )


@pytest.fixture
def estudiante(db):
    """Usuario con rol Estudiante."""
    return Usuario.objects.create(
        nombre='Estudiante Test',
        apellido='Test',
        correo='estudiante@test.com',
        password='pbkdf2_sha256$test',
        tipo_rol=Usuario.TipoRol.ESTUDIANTE,
        estado=Usuario.Estado.ACTIVO,
        fecha_creacion=timezone.now(),
        fecha_actualizacion=timezone.now(),
    )


@pytest.fixture
def proyecto_con_curso_y_docente(docente):
    """Crea un Curso → Proyecto completo con docente asignado."""
    periodo = None
    # Buscar o crear período activo
    from apps.configuracion.models import PeriodoAcademico
    from datetime import date
    periodo = PeriodoAcademico.objects.create(
        nombre='Periodo 2026-1',
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 6, 30),
        estado=PeriodoAcademico.Estado.ACTIVO,
        usuario_creo=docente
    )
    curso = Curso.objects.create(
        nombre='Ingeniería de Software I',
        codigo='IS-101',
        id_docente=docente,
        id_periodo_academico=periodo,
        usuario_creo=docente,
        estado=Curso.Estado.ACTIVO,
        cantidad_max_estudiantes=30
    )
    proyecto = Proyecto.objects.create(
        id_curso=curso,
        nombre='Proyecto de Prueba',
        fecha_inicio=date(2026, 2, 1),
        fecha_fin_estimada=date(2026, 5, 31),
        estado=Proyecto.Estado.PLANIFICADO
    )
    return proyecto


@pytest.fixture
def fase_proyecto(proyecto_con_curso_y_docente):
    """Fase del proyecto."""
    from apps.cursos.models import FaseProyecto
    return FaseProyecto.objects.create(
        id_proyecto=proyecto_con_curso_y_docente,
        nombre='Fase 1',
        descripcion='Primera fase',
        orden=1,
        fecha_inicio=timezone.now().date(),
        fecha_fin=timezone.now().date(),
        estado=FaseProyecto.Estado.PENDIENTE,
        porcentaje_completado=0
    )


@pytest.fixture
def actividad(fase_proyecto):
    """Actividad vinculada a la fase."""
    return Actividad.objects.create(
        id_fase=fase_proyecto,
        nombre='Actividad de prueba',
        descripcion='Descripción de prueba',
        fecha_limite=timezone.now().date(),
        prioridad=Actividad.Prioridad.MEDIA,
        estado=Actividad.Estado.PENDIENTE
    )


@pytest.fixture
def equipo(proyecto_con_curso_y_docente):
    """Equipo de trabajo."""
    return Equipo.objects.create(
        proyecto=proyecto_con_curso_y_docente,
        nombre='Equipo de prueba',
        cupo_maximo=5,
        estado='activo'
    )


@pytest.fixture
def miembro_equipo(equipo, estudiante):
    """Vincula estudiante al equipo."""
    return MiembroEquipo.objects.create(
        equipo=equipo,
        usuario=estudiante,
        rol_interno='desarrollador',
        estado='activo'
    )


@pytest.fixture
def entregable_enviado(actividad, equipo):
    """Entregable en estado 'enviado' listo para validación."""
    return Entregable.objects.create(
        titulo='Entregable de prueba',
        descripcion='Descripción de prueba',
        tipo='documento',
        estado='enviado',
        fecha_envio=timezone.now(),
        fecha_creacion=timezone.now(),
        id_actividad=actividad,
        id_equipo=equipo,
        numero_version=1
    )


def _auth_header(user):
    """
    Genera el header Authorization con JWT para el usuario.
    Usa force_authenticate para simular autenticación en tests.
    """
    # En este proyecto las pruebas usan force_authenticate, no tokens reales.
    # Esta función solo existe para compatibilidad con el patrón del prompt.
    return f"Bearer dummy-token-{user.id}"


# ── CP-01: Docente aprueba entregable → 200 ──────────────────────────────────
@pytest.mark.django_db
def test_docente_aprueba_entregable(api_client, docente, entregable_enviado):
    api_client.force_authenticate(user=docente)
    url = f'/api/entregables/{entregable_enviado.id}/aprobar/'
    response = api_client.patch(url, {'retroalimentacion': 'Buen trabajo'}, format='json')

    assert response.status_code == 200
    entregable_enviado.refresh_from_db()
    assert entregable_enviado.estado == 'aprobado'
    assert entregable_enviado.fecha_validacion is not None
    assert entregable_enviado.retroalimentacion == 'Buen trabajo'
    assert entregable_enviado.id_docente_validador_id == docente.id


# ── CP-02: Docente rechaza con retroalimentación → 200 ───────────────────────
@pytest.mark.django_db
def test_docente_rechaza_entregable(api_client, docente, entregable_enviado):
    api_client.force_authenticate(user=docente)
    url = f'/api/entregables/{entregable_enviado.id}/rechazar/'
    response = api_client.patch(
        url,
        {'retroalimentacion': 'Falta profundidad en la sección 2'},
        format='json'
    )

    assert response.status_code == 200
    entregable_enviado.refresh_from_db()
    assert entregable_enviado.estado == 'rechazado'
    assert entregable_enviado.retroalimentacion == 'Falta profundidad en la sección 2'
    assert entregable_enviado.fecha_validacion is not None


# ── CP-03: No-docente intenta aprobar → 403 ──────────────────────────────────
@pytest.mark.django_db
def test_estudiante_no_puede_aprobar(api_client, estudiante, entregable_enviado):
    api_client.force_authenticate(user=estudiante)
    url = f'/api/entregables/{entregable_enviado.id}/aprobar/'
    response = api_client.patch(url, {'retroalimentacion': 'x'}, format='json')

    assert response.status_code == 403


# ── CP-04: Aprobar entregable no enviado → 400 ───────────────────────────────
@pytest.mark.django_db
def test_aprobar_entregable_no_enviado(api_client, docente, entregable_enviado):
    entregable_enviado.estado = 'borrador'
    entregable_enviado.save(update_fields=['estado'])

    api_client.force_authenticate(user=docente)
    url = f'/api/entregables/{entregable_enviado.id}/aprobar/'
    response = api_client.patch(url, {'retroalimentacion': 'x'}, format='json')

    assert response.status_code == 400


# ── CP-05: GET entregables-pendientes filtra solo estado 'enviado' → 200 ──────
@pytest.mark.django_db
def test_entregables_pendientes_filtra_por_estado(api_client, docente, entregable_enviado):
    api_client.force_authenticate(user=docente)
    proyecto_id = entregable_enviado.id_actividad.id_fase.id_proyecto_id
    url = f'/api/proyectos/{proyecto_id}/entregables-pendientes/'
    response = api_client.get(url)

    assert response.status_code == 200
    estados = [e['estado'] for e in response.data]
    assert all(e == 'enviado' for e in estados)


# ── CP-06: Validación queda en BitacoraSistema ────────────────────────────────
@pytest.mark.django_db
def test_aprobacion_registra_bitacora(api_client, docente, entregable_enviado):
    from apps.bitacora.models import BitacoraSistema

    api_client.force_authenticate(user=docente)
    url = f'/api/entregables/{entregable_enviado.id}/aprobar/'
    api_client.patch(url, {'retroalimentacion': 'OK'}, format='json')

    registro = BitacoraSistema.objects.filter(
        accion='UPDATE',
        modulo='entregables',
        id_usuario_id=docente.id
    ).first()
    assert registro is not None


# ── CP-07: Sin autenticación → 401 ───────────────────────────────────────────
@pytest.mark.django_db
def test_sin_autenticacion_retorna_401(api_client, entregable_enviado):
    url = f'/api/entregables/{entregable_enviado.id}/aprobar/'
    response = api_client.patch(url, {'retroalimentacion': 'x'}, format='json')

    assert response.status_code == 401


# ── CP-08: Rechazar sin retroalimentación → 400 ───────────────────────────────
@pytest.mark.django_db
def test_rechazar_sin_retroalimentacion(api_client, docente, entregable_enviado):
    api_client.force_authenticate(user=docente)
    url = f'/api/entregables/{entregable_enviado.id}/rechazar/'
    response = api_client.patch(url, {}, format='json')

    assert response.status_code == 400
    assert 'retroalimentación' in response.data['error'].lower()
