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

export const distribucionApi = {

    async obtenerPorEquipo(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/distribucion/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },

    async asignarResponsable(actividadId, responsableId) {
        const response = await request(`/api/actividades/${actividadId}/asignar/`, {
            method: 'PATCH',
            body: JSON.stringify({ responsable_id: responsableId }),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}