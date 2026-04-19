# backend/tests/bitacora/test_hu037_auditoria.py
#
# HU-037 — Bitácora de auditoría del sistema
# Subtarea: SCRUM-165 — PR 01 Pruebas unitarias del backend
#
# Estado: ENDPOINT IMPLEMENTADO (/api/bitacora/)
# ─────────────────────────────────────────────────────────────────

import pytest
from rest_framework.test import APIClient
from rest_framework import status


# -------------------------------------------------------
# FIXTURES
# -------------------------------------------------------
@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def admin_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    usuario = Usuario.objects.create(
        nombre="Admin",
        apellido="Test",
        correo="admin@test.com",
        contrasena_hash=make_password("admin123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    usuario.is_staff = True
    usuario.save()
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def docente_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    usuario = Usuario.objects.create(
        nombre="Docente",
        apellido="Test",
        correo="docente@test.com",
        contrasena_hash=make_password("doc123"),
        tipo_rol=Usuario.TipoRol.DOCENTE,
        estado=Usuario.Estado.ACTIVO
    )
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def estudiante_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    usuario = Usuario.objects.create(
        nombre="Estudiante",
        apellido="Test",
        correo="estudiante@test.com",
        contrasena_hash=make_password("est123"),
        tipo_rol=Usuario.TipoRol.ESTUDIANTE,
        estado=Usuario.Estado.ACTIVO
    )
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def evento_base(db):
    """Crea un evento de prueba en la bitácora"""
    from apps.bitacora.utils import registrar_evento
    from apps.bitacora.models import BitacoraSistema
    from django.test import RequestFactory
    factory = RequestFactory()
    request = factory.get('/test')
    request.usuario = None
    registrar_evento(
        request,
        accion=BitacoraSistema.Accion.ACCESS,
        modulo='configuracion',
        descripcion='Test de acceso'
    )


# -------------------------------------------------------
# Tests del Modelo - BitácoraSistema
# -------------------------------------------------------
@pytest.mark.django_db
def test_registrar_evento_crea_registro(evento_base):
    """Verifica que registrar_evento() guarda en la BD"""
    from apps.bitacora.models import BitacoraSistema
    assert BitacoraSistema.objects.exists()
    evento = BitacoraSistema.objects.first()
    assert evento.accion == 'ACCESS'
    assert evento.modulo == 'configuracion'


@pytest.mark.django_db
def test_bitacora_rechaza_update(evento_base):
    """Verifica que el modelo rechaza UPDATE (append-only)"""
    from apps.bitacora.models import BitacoraSistema
    evento = BitacoraSistema.objects.first()
    with pytest.raises(TypeError, match=".*no se permite modificar.*"):
        evento.descripcion = "Intento de cambio"
        evento.save()


@pytest.mark.django_db
def test_bitacora_rechaza_delete(evento_base):
    """Verifica que el modelo rechaza DELETE (append-only)"""
    from apps.bitacora.models import BitacoraSistema
    evento = BitacoraSistema.objects.first()
    with pytest.raises(TypeError, match=".*no se permite DELETE.*"):
        evento.delete()


# -------------------------------------------------------
# Tests de API - Endpoint /api/bitacora/
# -------------------------------------------------------
@pytest.mark.django_db
def test_listar_eventos_como_admin(admin_autenticado, evento_base):
    """GET /api/bitacora/ retorna lista de eventos"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    assert 'results' in respuesta.data or len(respuesta.data) >= 1


@pytest.mark.django_db
def test_listar_eventos_como_docente(docente_autenticado):
    """GET /api/bitacora/ como docente retorna 403"""
    respuesta = docente_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_listar_eventos_como_estudiante(estudiante_autenticado):
    """GET /api/bitacora/ como estudiante retorna 403"""
    respuesta = estudiante_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_listar_eventos_sin_autenticacion(cliente):
    """GET /api/bitacora/ sin autenticacion retorna 401"""
    respuesta = cliente.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_filtrar_eventos_por_modulo(admin_autenticado, evento_base):
    """Filtrar eventos por modulo"""
    respuesta = admin_autenticado.get("/api/bitacora/?modulo=configuracion")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_filtrar_eventos_por_accion(admin_autenticado, evento_base):
    """Filtrar eventos por accion"""
    respuesta = admin_autenticado.get("/api/bitacora/?accion=ACCESS")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_filtrar_eventos_por_fecha_desde(admin_autenticado, evento_base):
    """Filtrar eventos por fecha desde"""
    respuesta = admin_autenticado.get("/api/bitacora/?fecha_desde=2026-01-01")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_registro_contiene_campos_minimos(admin_autenticado, evento_base):
    """Cada registro contiene campos mínimos requeridos"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    data = respuesta.data.get('results', respuesta.data)
    registro = data[0]
    assert 'nombre_usuario' in registro
    assert 'accion' in registro
    assert 'modulo' in registro
    assert 'fecha_hora' in registro


# ================================================================
# FILTROS Y PAGINACIÓN - HU-037 PR 02
# ================================================================

@pytest.fixture
def registros_bitacora(db):
    """Crea múltiples registros de bitácora para tests de filtros y paginación"""
    from apps.bitacora.models import BitacoraSistema
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    
    # Crear dos usuarios
    usuario1 = Usuario.objects.create(
        nombre="Usuario1",
        apellido="Test",
        correo="user1@test.com",
        contrasena_hash=make_password("test123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    
    usuario2 = Usuario.objects.create(
        nombre="Usuario2",
        apellido="Test",
        correo="user2@test.com",
        contrasena_hash=make_password("test123"),
        tipo_rol=Usuario.TipoRol.DOCENTE,
        estado=Usuario.Estado.ACTIVO
    )
    
    # Crear registros de bitácora para usuario1 - módulo usuarios
    BitacoraSistema.objects.create(
        id_usuario=usuario1,
        nombre_usuario="Usuario1 Test",
        accion=BitacoraSistema.Accion.CREATE,
        modulo="usuarios",
        descripcion="Crear usuario",
        ip_origen="192.168.1.1"
    )
    BitacoraSistema.objects.create(
        id_usuario=usuario1,
        nombre_usuario="Usuario1 Test",
        accion=BitacoraSistema.Accion.UPDATE,
        modulo="usuarios",
        descripcion="Actualizar usuario",
        ip_origen="192.168.1.1"
    )
    
    # Crear registros de bitácora para usuario2 - módulo config
    BitacoraSistema.objects.create(
        id_usuario=usuario2,
        nombre_usuario="Usuario2 Test",
        accion=BitacoraSistema.Accion.DELETE,
        modulo="configuracion",
        descripcion="Eliminar configuración",
        ip_origen="192.168.1.2"
    )
    BitacoraSistema.objects.create(
        id_usuario=usuario2,
        nombre_usuario="Usuario2 Test",
        accion=BitacoraSistema.Accion.ACCESS,
        modulo="configuracion",
        descripcion="Ver configuración",
        ip_origen="192.168.1.2"
    )
    
    # Crear registros adicionales para paginación
    for i in range(25):
        BitacoraSistema.objects.create(
            id_usuario=usuario1,
            nombre_usuario="Usuario1 Test",
            accion=BitacoraSistema.Accion.ACCESS,
            modulo="cursos",
            descripcion=f"Acceso curso {i}",
            ip_origen="192.168.1.1"
        )
    
    return {
        'usuario1': usuario1,
        'usuario2': usuario2,
    }


@pytest.mark.django_db
def test_filtro_por_modulo_retorna_solo_ese_modulo(admin_autenticado, registros_bitacora):
    """CF-01: Filtrar por módulo retorna solo registros de ese módulo"""
    respuesta = admin_autenticado.get("/api/bitacora/?modulo=usuarios")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    # Solo debe haber registros del módulo "usuarios"
    for registro in data:
        assert registro['modulo'] == 'usuarios', f"Registro con módulo incorrecto: {registro['modulo']}"


@pytest.mark.django_db
def test_filtro_por_accion_retorna_solo_esa_accion(admin_autenticado, registros_bitacora):
    """CF-02: Filtrar por acción retorna solo registros de esa acción"""
    respuesta = admin_autenticado.get("/api/bitacora/?accion=CREATE")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    # Solo debe haber registros con accion="CREATE"
    for registro in data:
        assert registro['accion'] == 'CREATE', f"Registro con acción incorrecta: {registro['accion']}"


@pytest.mark.django_db
def test_filtro_por_usuario_retorna_solo_sus_registros(admin_autenticado, registros_bitacora):
    """CF-03: Filtrar por usuario retorna solo sus registros"""
    usuario1 = registros_bitacora['usuario1']
    respuesta = admin_autenticado.get(f"/api/bitacora/?usuario={usuario1.id}")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    # Solo debe haber registros del usuario1
    for registro in data:
        if registro['id_usuario']:
            assert registro['id_usuario']['id'] == usuario1.id


@pytest.mark.django_db
def test_filtro_por_fecha_retorna_rango_correcto(admin_autenticado, registros_bitacora):
    """CF-04: Filtrar por rango de fechas retorna solo registros del rango"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Obtener fecha de hoy y hace 30 días
    hoy = timezone.now()
    fecha_inicio = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_fin = hoy.strftime('%Y-%m-%d')
    
    respuesta = admin_autenticado.get(f"/api/bitacora/?fecha_desde={fecha_inicio}&fecha_hasta={fecha_fin}")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    # Verificar que las fechas están dentro del rango
    for registro in data:
        fecha_registro = datetime.fromisoformat(registro['fecha_hora'].replace('Z', '+00:00')).date()
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        assert fecha_inicio_dt <= fecha_registro <= fecha_fin_dt


@pytest.mark.django_db
def test_paginacion_retorna_numero_correcto_por_pagina(admin_autenticado, registros_bitacora):
    """CF-05: Paginación retorna el número correcto de registros por página"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    
    # Verificar estructura de paginación
    assert 'results' in respuesta.data, "Respuesta debe tener 'results' para paginación"
    assert 'count' in respuesta.data, "Respuesta debe tener 'count' para paginación"
    assert 'next' in respuesta.data, "Respuesta debe tener 'next' para paginación"
    assert 'previous' in respuesta.data, "Respuesta debe tener 'previous' para paginación"
    
    # Verificar page_size (50 por defecto)
    resultados = respuesta.data['results']
    assert len(resultados) <= 50, "Debe retornar máximo 50 registros por página"


@pytest.mark.django_db
def test_paginacion_siguiente_pagina(admin_autenticado, registros_bitacora):
    """CF-05b: La paginación permite navegar a la siguiente página"""
    respuesta = admin_autenticado.get("/api/bitacora/?page=1")
    assert respuesta.status_code == status.HTTP_200_OK
    
    # Si hay más páginas, debe haber next
    if respuesta.data.get('next'):
        respuesta_page2 = admin_autenticado.get("/api/bitacora/?page=2")
        assert respuesta_page2.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_endpoint_no_permite_post(cliente, admin_autenticado):
    """CF-06: Endpoint no permite POST → 405"""
    respuesta = cliente.post("/api/bitacora/", {'accion': 'CREATE', 'modulo': 'test'})
    # http_method_names = ['get', 'head', 'options'] en la vista
    assert respuesta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_endpoint_no_permite_delete(cliente, admin_autenticado):
    """CF-07: Endpoint no permite DELETE → 405"""
    respuesta = cliente.delete("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_endpoint_sin_autenticacion_retorna_401(cliente):
    """CF-08: Sin autenticación → 401"""
    respuesta = cliente.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_filtros_combinados_modulo_y_accion(admin_autenticado, registros_bitacora):
    """Filtros combinados: modulo + accion"""
    respuesta = admin_autenticado.get("/api/bitacora/?modulo=usuarios&accion=CREATE")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    for registro in data:
        assert registro['modulo'] == 'usuarios'
        assert registro['accion'] == 'CREATE'


@pytest.mark.django_db
def test_orden_por_fecha_descendente(admin_autenticado, registros_bitacora):
    """Verifica que los registros se retornan ordenados por fecha descendente"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    
    data = respuesta.data.get('results', respuesta.data)
    fechas = [registro['fecha_hora'] for registro in data]
    
    # Verificar que están ordenados descendentemente
    for i in range(len(fechas) - 1):
        assert fechas[i] >= fechas[i + 1], "Los registros deben estar ordenados por fecha descendente"