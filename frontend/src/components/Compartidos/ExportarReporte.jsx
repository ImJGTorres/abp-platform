import { useState } from 'react'
import { exportacionesApi, session } from '../../services/api'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconDownload() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 3v10M6 9l4 4 4-4" />
            <path d="M3 17h14" />
        </svg>
    )
}

function IconSpinner() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4 animate-spin" stroke="currentColor" strokeWidth="2">
            <circle cx="10" cy="10" r="7" strokeOpacity="0.25" />
            <path d="M10 3a7 7 0 017 7" strokeLinecap="round" />
        </svg>
    )
}

function IconCheck() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10l4 4 8-8" />
        </svg>
    )
}

function IconError() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 7v3M10 13h.01" />
        </svg>
    )
}

// ── Componente ────────────────────────────────────────────────────────────────

/**
 * Botón de exportación con selector de formato.
 *
 * Props:
 *   tipo_reporte  — 'proyecto' | 'estudiante' | 'equipo' | 'indicadores' | 'tendencia'
 *   parametros    — objeto con los parámetros requeridos según el tipo
 *   className     — clases CSS adicionales para el contenedor
 */
export default function ExportarReporte({ tipo_reporte, parametros = {}, className = '' }) {
    const [formato, setFormato] = useState('pdf')
    const [estado, setEstado] = useState('idle') // idle | generando | listo | error
    const [exportId, setExportId] = useState(null)
    const [errorMsg, setErrorMsg] = useState(null)

    async function handleExportar() {
        setEstado('generando')
        setErrorMsg(null)

        try {
            const res = await exportacionesApi.solicitar(tipo_reporte, formato, parametros)

            if (res.estado === 'listo') {
                setExportId(res.id)
                setEstado('listo')
                triggerDescarga(res.id)
            } else if (res.estado === 'error') {
                setEstado('error')
                setErrorMsg(res.mensaje_error ?? 'Error al generar el archivo.')
            } else {
                // estado: generando → polling
                const id = res.id
                setExportId(id)
                pollEstado(id)
            }
        } catch (err) {
            setEstado('error')
            setErrorMsg(err?.data?.error ?? 'Error al solicitar la exportación.')
        }
    }

    async function pollEstado(id) {
        const MAX = 20
        let intento = 0
        while (intento < MAX) {
            await new Promise(r => setTimeout(r, 1500))
            intento++
            try {
                const res = await exportacionesApi.estado(id)
                if (res.estado === 'listo') {
                    setEstado('listo')
                    triggerDescarga(id)
                    return
                }
                if (res.estado === 'error') {
                    setEstado('error')
                    setErrorMsg(res.mensaje_error ?? 'Error al generar el archivo.')
                    return
                }
            } catch {
                // continuar intentando
            }
        }
        setEstado('error')
        setErrorMsg('Tiempo de espera agotado. Intenta de nuevo.')
    }

    async function triggerDescarga(id) {
        const token = session.getAccess()
        const url = exportacionesApi.descargarUrl(id)
        try {
            const response = await fetch(url, {
                headers: { Authorization: `Bearer ${token}` },
            })
            if (!response.ok) {
                setEstado('error')
                setErrorMsg('No se pudo descargar el archivo.')
                return
            }
            const blob = await response.blob()
            const objUrl = URL.createObjectURL(blob)
            const disposition = response.headers.get('content-disposition')
            let filename = `reporte.${formato}`
            if (disposition) {
                const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
                if (match?.[1]) filename = match[1].replace(/['"]/g, '')
            }
            const a = document.createElement('a')
            a.href = objUrl
            a.download = filename
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(objUrl)
        } catch {
            setEstado('error')
            setErrorMsg('Error al descargar el archivo.')
        }
    }

    function reset() {
        setEstado('idle')
        setExportId(null)
        setErrorMsg(null)
    }

    const isGenerando = estado === 'generando'

    return (
        <div className={`flex items-center gap-2 flex-wrap ${className}`}>
            {/* Selector de formato */}
            <div className="flex rounded-xl border border-[#e1e3e4] overflow-hidden text-[12px] font-semibold">
                {['pdf', 'excel'].map(f => (
                    <button
                        key={f}
                        disabled={isGenerando}
                        onClick={() => { setFormato(f); reset() }}
                        className={`px-3 py-1.5 transition-colors ${
                            formato === f
                                ? 'bg-[#d32f2f] text-white'
                                : 'bg-white text-[#4c616c] hover:bg-[#f0f2f3]'
                        } disabled:opacity-50`}
                    >
                        {f.toUpperCase()}
                    </button>
                ))}
            </div>

            {/* Botón principal */}
            {estado === 'idle' && (
                <button
                    onClick={handleExportar}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#d32f2f] text-white text-[12px] font-semibold rounded-xl hover:bg-[#c62828] transition-colors"
                >
                    <IconDownload />
                    Exportar
                </button>
            )}

            {estado === 'generando' && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#ffebee] text-[#d32f2f] text-[12px] font-semibold rounded-xl">
                    <IconSpinner />
                    Generando...
                </div>
            )}

            {estado === 'listo' && (
                <div className="flex items-center gap-1.5">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 text-[12px] font-semibold rounded-xl border border-green-200">
                        <IconCheck />
                        Descargado
                    </div>
                    <button
                        onClick={reset}
                        className="px-3 py-1.5 text-[12px] font-semibold text-[#4c616c] hover:bg-[#f0f2f3] rounded-xl transition-colors"
                    >
                        Nuevo
                    </button>
                </div>
            )}

            {estado === 'error' && (
                <div className="flex items-center gap-1.5">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-[#d32f2f] text-[12px] font-semibold rounded-xl border border-red-200" title={errorMsg}>
                        <IconError />
                        Error
                    </div>
                    <button
                        onClick={reset}
                        className="px-3 py-1.5 text-[12px] font-semibold text-[#4c616c] hover:bg-[#f0f2f3] rounded-xl transition-colors"
                    >
                        Reintentar
                    </button>
                </div>
            )}

            {errorMsg && estado === 'error' && (
                <p className="w-full text-[11px] text-[#d32f2f] mt-0.5">{errorMsg}</p>
            )}
        </div>
    )
}
