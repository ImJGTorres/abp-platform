import { request } from './api'

// ─── Parse helper (opcional si no lo exportas desde api.js) ───
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
//Endpoints: GET /api/cursos/ (listar),
// POST /api/cursos/ (crear),
// PUT/PATCH /api/cursos/:id/ (editar),
// DELETE /api/cursos/:id/ (eliminar)

// Para proyectos dentro de un curso:
// GET /api/cursos/:cursoId/proyectos/ (listar),
// POST /api/cursos/:cursoId/proyectos/ (crear), PUT/PATCH /api/cursos/:cursoId/proyectos/:proyectoId/ (editar)
export const cursosApi = {

    async listar() {
        const response = await request('/api/cursos/')
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear({ nombre, codigo, descripcion, periodo_id }) {
        const response = await request('/api/cursos/', {
            method: 'POST',
            body: JSON.stringify({ nombre, codigo, descripcion, periodo_id }),
        })

        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editar(id, campos) {
        const response = await request(`/api/cursos/${id}/`, {
            method: 'PUT', // usa PATCH si tu backend es parcial
            body: JSON.stringify(campos),
        })

        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async eliminar(id) {
        const response = await request(`/api/cursos/${id}/`, {
            method: 'DELETE',
        })

        if (!response.ok) {
            const data = await parseJSON(response)
            throw { status: response.status, data }
        }
    },

    // ─── Proyectos dentro de un curso ───
    async obtenerProyectos(cursoId) {
        const response = await request(`/api/cursos/${cursoId}/proyectos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crearProyecto(cursoId, { nombre, descripcion, fecha_inicio, fecha_fin }) {
        const response = await request(`/api/cursos/${cursoId}/proyectos/`, {
            method: 'POST',
            body: JSON.stringify({ nombre, descripcion, fecha_inicio, fecha_fin }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async editarProyecto(cursoId, proyectoId, campos) {
        const response = await request(`/api/cursos/${cursoId}/proyectos/${proyectoId}/`, {
            method: 'PUT',
            body: JSON.stringify(campos),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

}