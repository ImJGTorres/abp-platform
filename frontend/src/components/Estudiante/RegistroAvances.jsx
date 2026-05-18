import { useState, useEffect } from 'react'
import { avancesApi } from '../../services/estudianteApi'
import LineaTiempoAvances from './LineaTiempoAvances'

function IconChevronDown({ open }) {
    return (
        <svg viewBox="0 0 16 16" fill="none" className={`w-4 h-4 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
            stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M3 6l5 5 5-5" />
        </svg>
    )
}

function IconPlus() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M10 4v12M4 10h12" />
        </svg>
    )
}

export default function RegistroAvance({
    actividadId,
    actividadNombre,
    onSuccess,
    open,
    onClose,
    modoLectura = false,
}) {
    const [lastPorcentaje, setLastPorcentaje] = useState(0)
    const [refreshKey, setRefreshKey] = useState(0)

    const [mostrarFormulario, setMostrarFormulario] = useState(false)
    const [form, setForm] = useState({ descripcion: '', porcentaje_completado: 0, url_referencia: '' })
    const [guardando, setGuardando] = useState(false)
    const [errorMsg, setErrorMsg] = useState('')
    const [exito, setExito] = useState(false)

    useEffect(() => {
        if (open && actividadId) {
            cargarUltimoPorcentaje()
            setMostrarFormulario(false)
            setForm({ descripcion: '', porcentaje_completado: 0, url_referencia: '' })
            setErrorMsg('')
            setExito(false)
        }
    }, [open, actividadId])

    async function cargarUltimoPorcentaje() {
        try {
            const data = await avancesApi.listarPorActividad(actividadId)
            const ordenados = data.sort((a, b) => new Date(b.fecha_registro) - new Date(a.fecha_registro))
            const ultimo = ordenados[0]?.porcentaje_completado ?? 0
            setLastPorcentaje(ultimo)
            setForm(f => ({ ...f, porcentaje_completado: ultimo }))
        } catch {
            // silencioso
        }
    }

    async function guardar() {
        if (!form.descripcion.trim()) {
            setErrorMsg('La descripción es requerida.')
            return
        }
        if (form.porcentaje_completado < lastPorcentaje) {
            setErrorMsg(`El porcentaje no puede ser menor al último avance registrado (${lastPorcentaje}%).`)
            return
        }
        setErrorMsg('')
        setGuardando(true)
        try {
            await avancesApi.crear(actividadId, form)
            setForm({ descripcion: '', porcentaje_completado: 0, url_referencia: '' })
            setMostrarFormulario(false)
            setLastPorcentaje(form.porcentaje_completado)
            setExito(true)
            setRefreshKey(k => k + 1)
            onSuccess?.()
            setTimeout(() => setExito(false), 3000)
        } catch (err) {
            setErrorMsg(err.data?.detail || err.data?.non_field_errors?.[0] || 'Error al registrar avance.')
        } finally {
            setGuardando(false)
        }
    }

    if (!open) return null

    const barraAncho = Math.min(lastPorcentaje, 100)
    const barraColor = lastPorcentaje >= 100 ? 'bg-green-500' : lastPorcentaje >= 60 ? 'bg-[#d32f2f]' : 'bg-amber-500'

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]"
                onClick={e => e.stopPropagation()} style={{ fontFamily: "'Manrope', sans-serif" }}>

                {/* Header */}
                <div className="px-6 py-4 border-b border-[#e1e3e4] flex-shrink-0">
                    <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex-1 min-w-0">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">Progreso</p>
                            <h3 className="text-[16px] font-extrabold text-[#191c1d] leading-tight line-clamp-2">{actividadNombre}</h3>
                        </div>
                        <button onClick={onClose}
                            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#191c1d] transition-colors">
                            <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                <path d="M4 4l12 12M16 4L4 16" />
                            </svg>
                        </button>
                    </div>

                    {/* Barra de progreso */}
                    <div>
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-[11px] font-semibold text-[#9ba7ae]">Último avance registrado</span>
                            <span className="text-[13px] font-extrabold text-[#191c1d]">{lastPorcentaje}%</span>
                        </div>
                        <div className="w-full bg-[#e1e3e4] rounded-full h-2.5 overflow-hidden">
                            <div className={`h-full rounded-full transition-all duration-500 ${barraColor}`}
                                style={{ width: `${barraAncho}%` }} />
                        </div>
                    </div>
                </div>

                {/* Historial de avances — scrollable */}
                <div className="flex-1 overflow-y-auto px-6 py-4 min-h-0">
                    <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide mb-3">Historial de avances</p>

                    {exito && (
                        <div className="mb-3 px-3 py-2.5 bg-green-50 border border-green-200 rounded-xl text-[13px] text-green-700 font-semibold">
                            ¡Avance registrado correctamente!
                        </div>
                    )}

                    <LineaTiempoAvances actividadId={actividadId} refreshKey={refreshKey} />
                </div>

                {/* Sección de registro — oculta en modoLectura */}
                {!modoLectura && (
                    <div className="border-t border-[#e1e3e4] flex-shrink-0">
                        <button
                            onClick={() => { setMostrarFormulario(f => !f); setErrorMsg('') }}
                            className="w-full flex items-center justify-between px-6 py-3 text-[13px] font-semibold text-[#4c616c] hover:bg-[#f8f9fa] transition-colors">
                            <div className="flex items-center gap-2">
                                <IconPlus />
                                Registrar nuevo avance
                            </div>
                            <IconChevronDown open={mostrarFormulario} />
                        </button>

                        {mostrarFormulario && (
                            <div className="px-6 pb-5 space-y-4 border-t border-[#f0f2f3]">
                                {errorMsg && (
                                    <div className="pt-3 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                                        {errorMsg}
                                    </div>
                                )}

                                <div className="pt-4">
                                    <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Descripción *</label>
                                    <textarea
                                        value={form.descripcion}
                                        onChange={e => { setForm({ ...form, descripcion: e.target.value }); setErrorMsg('') }}
                                        rows={3}
                                        autoFocus
                                        placeholder="Describe el trabajo realizado, resultados obtenidos, obstáculos..."
                                        className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                                    />
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-[13px] font-semibold text-[#191c1d]">Porcentaje de avance</label>
                                        <span className="text-[20px] font-extrabold text-[#d32f2f]">{form.porcentaje_completado}%</span>
                                    </div>
                                    <input type="range" min={lastPorcentaje} max="100" step="5"
                                        value={form.porcentaje_completado}
                                        onChange={e => setForm({ ...form, porcentaje_completado: +e.target.value })}
                                        className="w-full h-2 bg-[#e1e3e4] rounded-full appearance-none cursor-pointer
                                            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                                            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#d32f2f]
                                            [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:cursor-pointer
                                            [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
                                            [&::-moz-range-thumb]:bg-[#d32f2f] [&::-moz-range-thumb]:border-0" />
                                    <div className="flex justify-between text-[10px] text-[#9ba7ae] mt-1">
                                        <span>{lastPorcentaje}%</span><span>100%</span>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">URL de referencia (opcional)</label>
                                    <input type="url"
                                        value={form.url_referencia}
                                        onChange={e => setForm({ ...form, url_referencia: e.target.value })}
                                        placeholder="https://github.com/usuario/repo/pull/123"
                                        className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]" />
                                    <p className="text-[11px] text-[#9ba7ae] mt-1">Enlace a commit, PR, documento, etc.</p>
                                </div>

                                <div className="flex gap-2">
                                    <button onClick={() => { setMostrarFormulario(false); setErrorMsg('') }}
                                        disabled={guardando}
                                        className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                                        Cancelar
                                    </button>
                                    <button onClick={guardar}
                                        disabled={guardando || !form.descripcion.trim()}
                                        className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                                        {guardando ? 'Guardando...' : 'Registrar avance'}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {modoLectura && (
                    <div className="px-6 py-4 border-t border-[#e1e3e4] flex-shrink-0">
                        <button onClick={onClose}
                            className="w-full px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold">
                            Cerrar
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
