"""Regresión de los hallazgos de las pruebas del Sprint 7 (HAL-S7-01, 02, 03 y 07).

HAL-S7-04 (IP real en la bitácora de adjuntos) está en test_hu020_archivos_adjuntos.py,
HAL-S7-08 en config/settings_test.py y HAL-S7-09 en test_auditoria_sesion.py.
"""
import re
from datetime import date
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import CursoEstudiante, Proyecto
from apps.equipos.models import MiembroEquipo
from apps.usuarios.models import Usuario
from tests.factories import (
    AdminFactory, CursoFactory, DocenteFactory, EquipoFactory, MiembroEquipoFactory, UsuarioFactory,
)


def cli(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


@pytest.fixture
def esc(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '10', 'categoria': ParametroSistema.Categoria.GENERAL,
                  'tipo_dato': ParametroSistema.TipoDato.INTEGER})
    dueno = DocenteFactory()
    curso = CursoFactory(id_docente=dueno, usuario_creo=dueno)
    proyecto = Proyecto.objects.create(
        nombre='P', id_curso=curso, fecha_inicio=date(2026, 2, 1),
        fecha_fin_estimada=date(2026, 5, 31), estado=Proyecto.Estado.EN_EJECUCION)
    equipo = EquipoFactory(proyecto=proyecto, cupo_maximo=4)
    miembro = UsuarioFactory()
    membresia = MiembroEquipoFactory(equipo=equipo, usuario=miembro)
    inscrito = UsuarioFactory()
    CursoEstudiante.objects.create(curso=curso, estudiante=inscrito)
    return dict(dueno=dueno, proyecto=proyecto, equipo=equipo, miembro=miembro, membresia=membresia,
                inscrito=inscrito, docente_ajeno=DocenteFactory(), estudiante_ajeno=UsuarioFactory(),
                admin=AdminFactory(),
                director=UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR, correo=f'dir.hal.{dueno.pk}@ufps.edu.co'))


# --- HAL-S7-01: el rol de líder solo lo asigna el gestor -------------------------------

def _ruta_rol(esc, usuario):
    return reverse('miembro-rol', kwargs={'equipo_id': esc['equipo'].id, 'usuario_id': usuario.id})


def test_hal01_estudiante_no_se_asigna_lider(esc):
    r = cli(esc['miembro']).patch(_ruta_rol(esc, esc['miembro']), {'rol_interno': 'lider'}, format='json')
    assert r.status_code == 403
    assert MiembroEquipo.objects.get(pk=esc['membresia'].pk).rol_interno != 'lider'
    assert Usuario.objects.get(pk=esc['miembro'].pk).tipo_rol == Usuario.TipoRol.ESTUDIANTE


def test_hal01_estudiante_si_elige_un_rol_que_no_es_lider(esc):
    r = cli(esc['miembro']).patch(_ruta_rol(esc, esc['miembro']),
                                  {'rol_interno': 'analista', 'descripcion_responsabilidades': 'Requisitos'},
                                  format='json')
    assert r.status_code == 200
    assert MiembroEquipo.objects.get(pk=esc['membresia'].pk).rol_interno == 'analista'


def test_hal01_lider_no_se_quita_el_rol_por_su_cuenta(esc):
    url_gestor = reverse('miembro-actualizar-rol', kwargs={'miembro_id': esc['membresia'].id})
    assert cli(esc['dueno']).patch(url_gestor, {'rol_interno': 'lider'}, format='json').status_code == 200
    lider = Usuario.objects.get(pk=esc['miembro'].pk)
    r = cli(lider).patch(_ruta_rol(esc, lider), {'rol_interno': 'tester'}, format='json')
    assert r.status_code == 403
    assert MiembroEquipo.objects.get(pk=esc['membresia'].pk).rol_interno == 'lider'
    # pero sí puede actualizar su descripción sin tocar el rol
    r = cli(lider).patch(_ruta_rol(esc, lider), {'descripcion_responsabilidades': 'Coordina'}, format='json')
    assert r.status_code == 200


# --- HAL-S7-02: equipos de un proyecto solo para participantes -------------------------

@pytest.mark.parametrize('actor,codigo', [
    ('dueno', 200), ('admin', 200), ('director', 200), ('miembro', 200), ('inscrito', 200),
    ('docente_ajeno', 403), ('estudiante_ajeno', 403),
])
def test_hal02_quien_ve_los_equipos_del_proyecto(esc, actor, codigo):
    r = cli(esc[actor]).get(reverse('equipos-por-proyecto', kwargs={'proyecto_id': esc['proyecto'].id}))
    assert r.status_code == codigo, r.content
    if codigo == 403:
        assert 'correo' not in r.content.decode()


# --- HAL-S7-03: estudiantes disponibles solo para el gestor ----------------------------

@pytest.mark.parametrize('actor,codigo', [
    ('dueno', 200), ('admin', 200), ('director', 200),
    ('miembro', 403), ('inscrito', 403), ('docente_ajeno', 403), ('estudiante_ajeno', 403),
])
def test_hal03_quien_ve_los_estudiantes_disponibles(esc, actor, codigo):
    r = cli(esc[actor]).get(reverse('estudiantes-equipo', kwargs={'equipo_id': esc['equipo'].id}))
    assert r.status_code == codigo, r.content


# --- HAL-S7-07: requirements de producción con versiones fijas -------------------------

def test_hal07_requirements_con_versiones_fijas_y_sin_duplicados():
    lineas = [l.split('#')[0].strip()
              for l in (Path(settings.BASE_DIR) / 'requirements.txt').read_text(encoding='utf-8').splitlines()]
    reqs = [l for l in lineas if l and not l.startswith('-r')]
    nombres = [re.split(r'[=<>~!\[]', r)[0].lower() for r in reqs]
    assert len(nombres) == len(set(nombres))
    assert [r for r in reqs if '==' not in r] == []
