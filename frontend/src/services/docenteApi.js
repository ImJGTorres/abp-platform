import { request } from './api'

// ── Parse helper (opcional si no lo exportas desde api.js) ───
async function parseJSON(response) {
    const text = await response.text()
    if (!text) return {}
    try {
        return JSON.parse(text)
    } catch {
        return { detail: `Error del servidor (${response.status})` }
    }
}

// ─── Cursos (Docente) ─────────────────────────────────────────
export const cursosApi = {
    async listar() {
        const response = await request('/api/cursos/')
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async obtener(id) {
        const response = await request(`/api/cursos/${id}/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async obtenerProyectos(cursoId) {
        const response = await request(`/api/cursos/${cursoId}/proyectos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearProyecto(cursoId, { nombre, descripcion, fecha_inicio, fecha_fin_estimada }) {
        const response = await request(`/api/cursos/${cursoId}/proyectos/`, {
            method: 'POST',
            body: JSON.stringify({ nombre, descripcion, fecha_inicio, fecha_fin_estimada }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editarProyecto(_cursoId, proyectoId, campos) {
        const response = await request(`/api/proyectos/${proyectoId}/`, {
            method: 'PUT',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminarProyecto(cursoId, proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/`, {
            method: 'DELETE',
        })
        if (!response.ok) {
            const data = await parseJSON(response)
            throw { status: response.status, data }
        }
    },
}

// ─── Proyectos (Objetivos, RAPs, Hitos) ────────────────────────
export const proyectosApi = {
    async obtener(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    // ── Objetivos ──
    async listarObjetivos(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/objetivos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearObjetivo(proyectoId, { descripcion, tipo, orden }) {
        const response = await request(`/api/proyectos/${proyectoId}/objetivos/`, {
            method: 'POST',
            body: JSON.stringify({ descripcion, tipo, orden }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editarObjetivo(_proyectoId, objetivoId, campos) {
        const response = await request(`/api/objetivos/${objetivoId}/`, {
            method: 'PUT',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminarObjetivo(_proyectoId, objetivoId) {
        const response = await request(`/api/objetivos/${objetivoId}/`, {
            method: 'DELETE',
        })
        if (!response.ok) {
            const data = await parseJSON(response)
            throw { status: response.status, data }
        }
    },

    // ── RAPs ──
    async listarRAPs(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/raps/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearRAP(proyectoId, { nombre, descripcion, competencia_asociada, porcentaje_evaluacion, orden }) {
        const response = await request(`/api/proyectos/${proyectoId}/raps/`, {
            method: 'POST',
            body: JSON.stringify({ nombre, descripcion, competencia_asociada, porcentaje_evaluacion, orden }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editarRAP(_proyectoId, rapId, campos) {
        const response = await request(`/api/raps/${rapId}/`, {
            method: 'PUT',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminarRAP(_proyectoId, rapId) {
        const response = await request(`/api/raps/${rapId}/`, {
            method: 'DELETE',
        })
        if (!response.ok) {
            const data = await parseJSON(response)
            throw { status: response.status, data }
        }
    },

    // ── Hitos (Cronograma) ──
    async listarHitos(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/hitos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearHito(proyectoId, { nombre, descripcion, fecha_inicio, fecha_fin, responsable, estado }) {
        const body = { nombre, descripcion, fecha_inicio, fecha_fin, responsable, estado }
        const response = await request(`/api/proyectos/${proyectoId}/hitos/`, {
            method: 'POST',
            body: JSON.stringify(body),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async actualizarHito(hitoId, campos) {
        const response = await request(`/api/hitos/${hitoId}/`, {
            method: 'PUT',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminarHito(hitoId) {
        const response = await request(`/api/hitos/${hitoId}/`, {
            method: 'DELETE',
        })
        if (response.status === 204) return
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
    },
}

//Fases del proyecto
export const fasesApi = {

    async listarPorProyecto(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/fases/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear(proyectoId, { nombre, descripcion, fecha_inicio, fecha_fin, orden }) {
        const response = await request(`/api/proyectos/${proyectoId}/fases/`, {
            method: 'POST',
            body: JSON.stringify({
                nombre,
                descripcion,
                fecha_inicio,
                fecha_fin,
                orden,
                estado: 'pendiente',
            }),
        })

        const data = await parseJSON(response)

        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editar(faseId, campos) {
        const response = await request(`/api/fases/${faseId}/`, {
            method: 'PATCH',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminar(faseId) {
        const response = await request(`/api/fases/${faseId}/`, {
            method: 'DELETE',
        })
        if (response.status === 204) return
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
    },

    async reordenar(faseId, nuevoOrden) {
        const response = await request(`/api/fases/${faseId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ orden: nuevoOrden }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}


// Actividades dentro de las fases
export const actividadesApi = {

    async obtener(actividadId) {
        const response = await request(`/api/actividades/${actividadId}/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async listarPorFase(faseId) {
        const response = await request(`/api/fases/${faseId}/actividades/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async listarPorEquipo(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/actividades/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear(faseId, payload) {
        const response = await request(`/api/fases/${faseId}/actividades/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editar(actividadId, campos) {
        const response = await request(`/api/actividades/${actividadId}/`, {
            method: 'PATCH',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminar(actividadId) {
        const response = await request(`/api/actividades/${actividadId}/`, {
            method: 'DELETE',
        })
        if (response.status === 204) return
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
    },
}


// ─── Equipos ───────────────────────────────────────────────────
export const equiposApi = {
    async obtenerPorProyecto(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/equipos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearEquipo(proyectoId, { nombre, descripcion, cupo_maximo }) {
        const response = await request(`/api/proyectos/${proyectoId}/equipos/`, {
            method: 'POST',
            body: JSON.stringify({ nombre, descripcion, cupo_maximo }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async obtenerEstudiantes(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/estudiantes/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async asignarEstudiantes(equipoId, usuarios) {
        const response = await request(`/api/equipos/${equipoId}/asignar/`, {
            method: 'POST',
            body: JSON.stringify({ usuarios }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async actualizarRolMiembro(miembroId, rolInterno) {
        const response = await request(`/api/miembros/${miembroId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ rol_interno: rolInterno }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async moverMiembro(equipoOrigenId, estudianteId, equipoDestinoId) {
        const payload = { usuario_id: estudianteId, equipo_destino_id: equipoDestinoId }
        const response = await request(`/api/equipos/${equipoOrigenId}/miembros/mover/`, {
            method: 'POST',
            body: JSON.stringify(payload),
            headers: { 'Content-Type': 'application/json' },
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async retirarMiembro(equipoId, usuarioId) {
        const response = await request(`/api/equipos/${equipoId}/miembros/${usuarioId}/`, {
            method: 'DELETE',
        })
        if (response.status === 204) return
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
    },

    async agregarMiembro(equipoId, estudianteId) {
        const response = await request(`/api/equipos/${equipoId}/miembros/`, {
            method: 'POST',
            body: JSON.stringify({ estudiante_id: estudianteId }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Estudiantes del curso ─────────────────────────────────────
export const estudiantesApi = {
    async listarPorCurso(cursoId) {
        const response = await request(`/api/cursos/${cursoId}/estudiantes/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async sinEquipoEnProyecto(cursoId, proyectoId) {
        const response = await request(`/api/cursos/${cursoId}/estudiantes/?proyecto_id=${proyectoId}`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}


export const evaluacionesApi = {
    async listar(entregableId) {
        const response = await request(`/api/entregables/${entregableId}/evaluaciones/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear(entregableId, payload) {
        const response = await request(`/api/entregables/${entregableId}/evaluaciones/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

export const retroalimentacionesApi = {
    async crear(proyectoId, payload) {
        const response = await request(`/api/proyectos/${proyectoId}/retroalimentaciones/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async listarPorEquipo(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/retroalimentaciones/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async listarPorUsuario(usuarioId) {
        const response = await request(`/api/usuarios/${usuarioId}/retroalimentaciones/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

export const rubricasApi = {
    async listar(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/rubricas/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear(proyectoId, payload) {
        const response = await request(`/api/proyectos/${proyectoId}/rubricas/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async actualizar(rubricaId, payload) {
        const response = await request(`/api/rubricas/${rubricaId}/`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminar(rubricaId) {
        const response = await request(`/api/rubricas/${rubricaId}/`, {
            method: 'DELETE',
        })
        if (response.status === 204) return
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
    },
}