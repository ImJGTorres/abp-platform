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

// ─── Equipos y proyectos del estudiante / líder ───────────────
// GET /api/mis-equipos/ → [{ equipo, proyecto, curso, fases: [{ actividades: [...] }] }]
export const misEquiposApi = {
    async listar() {
        const response = await request('/api/mis-equipos/')
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Semáforo de rendimiento personal (HU-041) ────────────────
// GET /api/reportes/semaforos/estudiante/?proyecto_id=<opcional>   (solo estudiante y líder, datos propios)
// 200 {
//   nivel: 'verde' | 'amarillo' | 'rojo',
//   nota_promedio: 3.4,                        // escala 0-5
//   porcentaje_actividades_incumplidas: 22.0,
//   entregables_criticos: [{ titulo, fecha: 'AAAA-MM-DD', estado: 'vencida' | 'por_vencer' | 'rechazado', enlace }],
//   recomendaciones: ['...'],
// }
// 403 si el proyecto_id no es de un equipo del usuario.
export const semaforoApi = {
    async personal(proyectoId) {
        const qs = proyectoId ? `?proyecto_id=${encodeURIComponent(proyectoId)}` : ''
        const response = await request(`/api/reportes/semaforos/estudiante/${qs}`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
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

// ─── Equipo del estudiante en un proyecto ─────────────────────
export const miEquipoApi = {
    async obtenerPorProyecto(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/equipos/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
    async obtenerMiembros(equipoId) {
        const response = await request(`/api/equipos/${equipoId}/estudiantes/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Autoevaluacion ───────────────────────────────────────────
export const autoevaluacionApi = {
    async mia(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/autoevaluaciones/mia/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
    async puedeAutoevaluar(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/puede-autoevaluar/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
    async crear(proyectoId, payload) {
        const response = await request(`/api/proyectos/${proyectoId}/autoevaluaciones/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}

// ─── Coevaluacion ─────────────────────────────────────────────
export const coevaluacionApi = {
    async listar(proyectoId) {
        const response = await request(`/api/proyectos/${proyectoId}/coevaluaciones/`)
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
    async crear(proyectoId, payload) {
        const response = await request(`/api/proyectos/${proyectoId}/coevaluaciones/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(response)
        if (!response.ok) throw { status: response.status, data }
        return data
    },
}