"""HU-045 (SCRUM-570) — Búsqueda global en cursos, proyectos, usuarios y entregables."""
from django.db.models import Q

from apps.cursos.models import Curso, Proyecto
from apps.entregables.models import Entregable
from apps.usuarios.models import Usuario

LIMITE_POR_TIPO = 10
MIN_CARACTERES = 2


def _item(id_, titulo, subtitulo, enlace):
    return {'id': id_, 'titulo': titulo, 'subtitulo': subtitulo, 'enlace': enlace}


def buscar_global(q, tipo_rol):
    """Devuelve hasta LIMITE_POR_TIPO resultados por tipo con {id, titulo, subtitulo, enlace}."""
    es_admin = tipo_rol == 'administrador'

    cursos = (
        Curso.objects
        .filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
        .order_by('nombre')
        .values('id', 'nombre', 'codigo')[:LIMITE_POR_TIPO]
    )
    proyectos = (
        Proyecto.objects
        .filter(nombre__icontains=q)
        .order_by('nombre')
        .values('id', 'nombre', 'id_curso__nombre')[:LIMITE_POR_TIPO]
    )
    usuarios = (
        Usuario.objects
        .filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q)
            | Q(codigo__icontains=q) | Q(correo__icontains=q)
        )
        .order_by('nombre', 'apellido')
        .values('id', 'nombre', 'apellido', 'correo', 'tipo_rol')[:LIMITE_POR_TIPO]
    )
    entregables = (
        Entregable.objects
        .filter(titulo__icontains=q)
        .order_by('titulo')
        .values('id', 'titulo', 'id_actividad__id_fase__id_proyecto_id',
                'id_actividad__id_fase__id_proyecto__nombre')[:LIMITE_POR_TIPO]
    )

    return {
        'cursos': [
            _item(c['id'], c['nombre'], c['codigo'],
                  f"/admin/cursos/{c['id']}" if es_admin else f"/director/reportes?curso_id={c['id']}")
            for c in cursos
        ],
        'proyectos': [
            _item(p['id'], p['nombre'], p['id_curso__nombre'], f"/director/reportes/proyecto/{p['id']}")
            for p in proyectos
        ],
        'usuarios': [
            _item(u['id'], f"{u['nombre']} {u['apellido']}", f"{u['correo']} · {u['tipo_rol']}",
                  f"/admin/registro?usuario_id={u['id']}" if es_admin else f"/director/riesgo?estudiante_id={u['id']}")
            for u in usuarios
        ],
        'entregables': [
            _item(e['id'], e['titulo'], e['id_actividad__id_fase__id_proyecto__nombre'],
                  f"/director/reportes/proyecto/{e['id_actividad__id_fase__id_proyecto_id']}")
            for e in entregables
        ],
    }
