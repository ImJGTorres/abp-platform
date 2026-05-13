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

export const entregablesApi = {
    async listar(actividadId) {
        const res = await request(`/api/actividades/${actividadId}/entregables/`)
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async crear(actividadId, payload) {
        const res = await request(`/api/actividades/${actividadId}/entregables/`, {
            method: 'POST',
            body: JSON.stringify(payload),
        })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async enviar(entregableId) {
        const res = await request(`/api/entregables/${entregableId}/enviar/`, { method: 'PATCH' })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async validar(entregableId, accion, retroalimentacion = '') {
        const res = await request(`/api/entregables/${entregableId}/validar/`, {
            method: 'PATCH',
            body: JSON.stringify({ accion, retroalimentacion }),
        })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async listarArchivos(entregableId) {
        const res = await request(`/api/entregables/${entregableId}/archivos/`)
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async subirArchivo(entregableId, archivo, onProgress) {
        const token = localStorage.getItem('access_token')
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            const formData = new FormData()
            formData.append('archivo', archivo)

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress(Math.round((e.loaded / e.total) * 100))
                }
            }

            xhr.onload = () => {
                let data
                try { data = JSON.parse(xhr.responseText) } catch { data = {} }
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(data)
                } else {
                    reject({ status: xhr.status, data })
                }
            }

            xhr.onerror = () => reject({ status: 0, data: { detail: 'Error de conexión.' } })

            const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
            xhr.open('POST', `${baseUrl}/api/entregables/${entregableId}/archivos/`)
            if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
            xhr.send(formData)
        })
    },

    async eliminarArchivo(archivoId) {
        const res = await request(`/api/archivos/${archivoId}/`, { method: 'DELETE' })
        if (res.status === 204) return
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async obtenerVersiones(entregableId) {
        const res = await request(`/api/entregables/${entregableId}/versiones/`)
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async crearNuevaVersion(entregableId, motivo = '') {
        const res = await request(`/api/entregables/${entregableId}/nueva-version/`, {
            method: 'POST',
            body: JSON.stringify({ motivo_revision: motivo }),
        })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },
}

export const notificacionesApi = {
    async listar() {
        const res = await request('/api/notificaciones/')
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async marcarLeida(id) {
        const res = await request(`/api/notificaciones/${id}/leer/`, { method: 'PATCH' })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },

    async marcarTodasLeidas() {
        const res = await request('/api/notificaciones/leer-todas/', { method: 'PATCH' })
        const data = await parseJSON(res)
        if (!res.ok) throw { status: res.status, data }
        return data
    },
}
