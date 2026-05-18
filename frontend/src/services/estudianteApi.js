import { request } from './api'

async function parseJSON(response) {
    const text = await response.text()
    if (!text) return {}
    try {
        return JSON.parse(text)
    } catch {
        return { detail: `Error del servidor (${response.status})` }
    }
}

// ─── Avances ──────────────────────────────────────────────────
export const avancesApi = {
    async listarPorActividad(actividadId) {
        const response = await request(`/api/actividades/${actividadId}/avances/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async crear(actividadId, { descripcion, porcentaje_completado, url_referencia }) {
        const body = { descripcion, porcentaje_completado }
        if (url_referencia) body.url_referencia = url_referencia
        const response = await request(`/api/actividades/${actividadId}/avances/`, {
            method: 'POST',
            body: JSON.stringify(body),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Progreso ─────────────────────────────────────────────────
export const progresoApi = {
    async obtenerProyecto(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/progreso/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async obtenerEquipo(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/progreso/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Proyectos del estudiante ─────────────────────────────────
export const estudianteProyectosApi = {
    async obtener(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}