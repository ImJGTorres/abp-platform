"""
HU-042 (corrección) — Un solo "avance real" en la tarjeta del panel de semáforos,
el "Progreso global" de Monitoreo y el "Resumen por equipo".

Regla: promedio por actividad; 100 si está completada, si no su último avance, 0 sin avance.
Requiere PostgreSQL (la vista vista_progreso_proyecto la crea la migración cursos 0028).
"""
import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad, Proyecto
from apps.reportes.semaforo import semaforos_docente
from tests.factories import (ActividadFactory, CursoFactory, DocenteFactory, EquipoFactory,
                             FaseProyectoFactory, MiembroEquipoFactory, ProyectoFactory, UsuarioFactory)

pytestmark = pytest.mark.skipif(connection.vendor == 'sqlite', reason='vista SQL de PostgreSQL')


@pytest.fixture
def proyecto(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})
    docente = DocenteFactory()
    proyecto = ProyectoFactory(id_curso=CursoFactory(id_docente=docente))
    # porcentaje_completado almacenado a propósito desactualizado: no debe influir
    fase = FaseProyectoFactory(id_proyecto=proyecto, porcentaje_completado=90)
    FaseProyectoFactory(id_proyecto=proyecto, porcentaje_completado=0)  # fase vacía: no cuenta
    equipo = EquipoFactory(proyecto=proyecto)
    est = UsuarioFactory()
    MiembroEquipoFactory(equipo=equipo, usuario=est)
    # completada por Kanban sin avance (100) · avance 30 y luego 50 (50) · sin avance (0) -> 50
    ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, estado=Actividad.Estado.COMPLETADA)
    parcial = ActividadFactory(id_fase=fase, id_equipo_asignado=equipo)
    for pct in (30, 50):
        AvanceActividad.objects.create(id_actividad=parcial, id_usuario=est, descripcion='a',
                                       porcentaje_completado=pct)
    ActividadFactory(id_fase=fase, id_equipo_asignado=equipo)
    return docente, proyecto


def test_tarjeta_progreso_global_y_equipo_dan_el_mismo_avance(proyecto):
    docente, p = proyecto

    tarjeta = semaforos_docente(docente.id)[0]['porcentaje_avance']

    c = APIClient()
    c.force_authenticate(user=docente)
    r = c.get(f'/api/proyectos/{p.id}/progreso/')
    assert r.status_code == 200

    lista = Proyecto.objects.filter(pk=p.pk).con_progreso().get().porcentaje_progreso

    assert tarjeta == r.data['porcentaje_progreso'] == r.data['equipos'][0]['porcentaje_progreso'] == lista == 50
    assert [f['porcentaje_completado'] for f in r.data['fases']] == [50, 0]
