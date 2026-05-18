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

export async function getMiEquipo() {
    const response = await request('/api/mis-equipos/')
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    // Devuelve el primer equipo donde el usuario es miembro activo
    return data?.[0] ?? null
}

export const distribucionApi = {
    // GET /api/equipos/:id/progreso/ — resumen con miembros y conteos
    async obtenerPorEquipo(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/progreso/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    // GET /api/equipos/:id/actividades/ — lista completa de actividades del equipo
    async obtenerActividades(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/actividades/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    // PATCH /api/actividades/:id/asignar/ — asigna responsables (array de ids)
    async asignarResponsable(actividadId, responsables) {
        const ids = Array.isArray(responsables) ? responsables : [responsables]
        const response = await request(`/api/actividades/${actividadId}/asignar/`, {
            method: 'PATCH',
            body: JSON.stringify({ responsables: ids }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    // GET /api/equipos/:id/progreso/ — reutilizado para carga de trabajo (miembros con conteos)
    async obtenerCargaMiembros(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/progreso/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

export const avancesApi = {
    async listarPorActividad(actividadId) {
        const response = await request(`/api/actividades/${actividadId}/avances/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

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