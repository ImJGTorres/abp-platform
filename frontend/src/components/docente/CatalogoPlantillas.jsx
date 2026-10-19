import { useState, useEffect, useMemo } from 'react'
import toast from 'react-hot-toast'
import { rubricasApi } from '../../services/docenteApi'

const ETIQUETAS_NIVEL = {
    excelente:     { label: 'Excelente',     color: '#2e7d32', bg: '#f1f8e9' },
    satisfactorio: { label: 'Satisfactorio', color: '#1565c0', bg: '#e3f2fd' },
    basico:        { label: 'Básico',        color: '#e65100', bg: '#fff3e0' },
    insuficiente:  { label: 'Insuficiente',  color: '#c62828', bg: '#ffebee' },
}
const ORDEN_NIVELES = ['excelente', 'satisfactorio', 'basico', 'insuficiente']

function nombreDe(p) {
    return p.nombre_plantilla || p.nombre || 'Sin nombre'
}

// Solo los 400/403/404 traen un mensaje pensado para el usuario
function mensajeError(err, porDefecto) {
    if (err?.type === 'network') return 'No hay conexión con el servidor. Revisa tu conexión e intenta de nuevo.'
    const data = err?.data
    if (data && typeof data.detail === 'string') return data.detail
    if (data && typeof data.error === 'string') return data.error
    return porDefecto
}

function IconSearch() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="9" r="5.5" /><path d="M13.5 13.5L17 17" />
        </svg>
    )
}

function IconX() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M4 4l12 12M16 4L4 16" />
        </svg>
    )
}

function VistaPrevia({ plantilla }) {
    const criterios = plantilla.criterios ?? []
    return (
        <div className="flex flex-col gap-3">
            <div>
                <p className="text-[16px] font-extrabold text-[#191c1d] leading-tight">{nombreDe(plantilla)}</p>
                {plantilla.descripcion && (
                    <p className="text-[12px] text-[#6b7b83] mt-1">{plantilla.descripcion}</p>
                )}
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className="text-[11px] font-semibold text-[#9ba7ae] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                        {criterios.length} criterio{criterios.length !== 1 ? 's' : ''}
                    </span>
                    {plantilla.docente_nombre && (
                        <span className="text-[11px] font-semibold text-[#4c616c] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                            {plantilla.docente_nombre}
                        </span>
                    )}
                </div>
            </div>

            {criterios.length === 0 ? (
                <p className="text-[12px] text-[#9ba7ae]">Esta plantilla no tiene criterios.</p>
            ) : criterios.map((c, idx) => (
                <div key={c.id ?? idx} className="border border-[#e1e3e4] rounded-xl overflow-hidden">
                    <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-[#fafafa] border-b border-[#f0f2f3]">
                        <p className="text-[13px] font-bold text-[#191c1d]">{c.nombre}</p>
                        <span className="text-[11px] font-bold text-[#d32f2f] bg-[#fce4e4] px-2 py-0.5 rounded-lg flex-shrink-0">
                            {parseFloat(c.peso_porcentual) || 0} %
                        </span>
                    </div>
                    <div className="px-3.5 py-2.5 flex flex-col gap-1.5">
                        {ORDEN_NIVELES.map(key => {
                            const nv = (c.niveles ?? []).find(v => v.etiqueta === key)
                            const est = ETIQUETAS_NIVEL[key]
                            return (
                                <div key={key} className="flex items-start gap-2">
                                    <span
                                        className="text-[10px] font-bold px-1.5 py-0.5 rounded-md flex-shrink-0 w-[84px] text-center"
                                        style={{ color: est.color, backgroundColor: est.bg }}
                                    >
                                        {est.label}
                                    </span>
                                    <p className="text-[12px] text-[#4c616c] leading-snug flex-1">
                                        {nv?.descripcion || <span className="text-[#c4cdd2] italic">Sin descriptor</span>}
                                    </p>
                                    <span className="text-[11px] font-bold text-[#6b7b83] flex-shrink-0">{parseFloat(nv?.puntos) || 0} pts</span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            ))}
        </div>
    )
}

/**
 * Modal con el banco de plantillas de rúbricas (HU-044).
 *
 * @param onSeleccionar  recibe la plantilla elegida (objeto completo de la API)
 * @param onCerrar       cierra el modal
 * @param procesando     true mientras el padre clona la plantilla elegida
 */
export default function CatalogoPlantillas({ onSeleccionar, onCerrar, procesando = false }) {
    const [plantillas, setPlantillas] = useState([])
    const [cargando,   setCargando]   = useState(true)
    const [error,      setError]      = useState(null)
    const [busqueda,   setBusqueda]   = useState('')
    const [seleccionId, setSeleccionId] = useState(null)
    const [intento,    setIntento]    = useState(0)

    useEffect(() => {
        let activo = true
        rubricasApi.listarPlantillas()
            .then(data => {
                if (!activo) return
                const lista = Array.isArray(data) ? data : (data.results ?? [])
                setPlantillas(lista)
                setSeleccionId(lista[0]?.id ?? null)
                setError(null)
            })
            .catch(err => {
                if (!activo) return
                const msg = mensajeError(err, 'No se pudo cargar el catálogo de plantillas.')
                setError(msg)
                toast.error(msg)
            })
            .finally(() => { if (activo) setCargando(false) })
        return () => { activo = false }
    }, [intento])

    // Esc cierra el modal (salvo mientras se está clonando)
    useEffect(() => {
        function alTeclear(e) {
            if (e.key === 'Escape' && !procesando) onCerrar()
        }
        document.addEventListener('keydown', alTeclear)
        return () => document.removeEventListener('keydown', alTeclear)
    }, [onCerrar, procesando])

    function reintentar() {
        setCargando(true)
        setError(null)
        setIntento(n => n + 1)
    }

    const filtradas = useMemo(() => {
        const q = busqueda.trim().toLowerCase()
        if (!q) return plantillas
        return plantillas.filter(p =>
            nombreDe(p).toLowerCase().includes(q) ||
            (p.nombre ?? '').toLowerCase().includes(q) ||
            (p.docente_nombre ?? '').toLowerCase().includes(q)
        )
    }, [plantillas, busqueda])

    const seleccionada = filtradas.find(p => p.id === seleccionId) ?? null

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => { if (!procesando) onCerrar() }}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-label="Catálogo de plantillas de rúbricas"
                className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col"
                style={{ fontFamily: "'Manrope', sans-serif" }}
                onClick={e => e.stopPropagation()}
            >
                {/* Cabecera */}
                <div className="flex items-center justify-between gap-3 px-6 py-4 border-b border-[#e1e3e4]">
                    <div>
                        <h2 className="text-[18px] font-extrabold text-[#191c1d] tracking-tight">Catálogo de plantillas</h2>
                        <p className="text-[12px] text-[#6b7b83] mt-0.5">Elige una plantilla para crear una rúbrica nueva a partir de ella.</p>
                    </div>
                    <button
                        onClick={onCerrar}
                        disabled={procesando}
                        aria-label="Cerrar"
                        className="w-9 h-9 flex items-center justify-center rounded-xl text-[#4c616c] hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                    >
                        <IconX />
                    </button>
                </div>

                {/* Buscador */}
                <div className="px-6 py-3 border-b border-[#f0f2f3]">
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9ba7ae]"><IconSearch /></span>
                        <input
                            type="text"
                            value={busqueda}
                            onChange={e => setBusqueda(e.target.value)}
                            placeholder="Buscar plantilla por nombre..."
                            className="w-full pl-9 pr-3.5 py-2.5 text-[13px] text-[#191c1d] bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors placeholder-[#c4cdd2]"
                        />
                    </div>
                </div>

                {/* Cuerpo */}
                {cargando ? (
                    <div className="flex-1 p-6 grid md:grid-cols-[260px_1fr] gap-4" aria-busy="true">
                        <div className="flex flex-col gap-2">
                            {[0, 1, 2, 3].map(i => <div key={i} className="h-14 bg-[#f0f2f3] rounded-xl animate-pulse" />)}
                        </div>
                        <div className="hidden md:block h-48 bg-[#f0f2f3] rounded-xl animate-pulse" />
                    </div>
                ) : error ? (
                    <div className="flex-1 flex flex-col items-center justify-center gap-3 py-12 text-center px-6">
                        <p className="text-[13px] text-[#c62828]">{error}</p>
                        <button
                            onClick={reintentar}
                            className="px-4 py-2 text-[13px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors"
                        >
                            Reintentar
                        </button>
                    </div>
                ) : plantillas.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center gap-2 py-14 text-center px-6">
                        <div className="w-14 h-14 bg-[#fce4e4] rounded-2xl flex items-center justify-center">
                            <svg viewBox="0 0 24 24" className="w-7 h-7 text-[#d32f2f]" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="3" /><path d="M9 9h6M9 12h6M9 15h4" />
                            </svg>
                        </div>
                        <p className="text-[14px] font-semibold text-[#191c1d]">Aún no hay plantillas</p>
                        <p className="text-[12px] text-[#9ba7ae]">Guarda una rúbrica como plantilla para reutilizarla en otros proyectos.</p>
                    </div>
                ) : (
                    <div className="flex-1 min-h-0 grid md:grid-cols-[280px_1fr]">
                        {/* Lista */}
                        <div className="overflow-y-auto border-b md:border-b-0 md:border-r border-[#f0f2f3] p-3 flex flex-col gap-2 max-h-[30vh] md:max-h-none">
                            {filtradas.length === 0 ? (
                                <p className="text-[12px] text-[#9ba7ae] text-center py-6">Ninguna plantilla coincide con “{busqueda.trim()}”.</p>
                            ) : filtradas.map(p => (
                                <button
                                    key={p.id}
                                    onClick={() => setSeleccionId(p.id)}
                                    className={`text-left px-3.5 py-2.5 rounded-xl border transition-colors ${
                                        p.id === seleccionId
                                            ? 'border-[#d32f2f] bg-[#fff5f5]'
                                            : 'border-[#e1e3e4] hover:border-[#d32f2f]/40 hover:bg-[#fafafa]'
                                    }`}
                                >
                                    <p className="text-[13px] font-bold text-[#191c1d] truncate">{nombreDe(p)}</p>
                                    <p className="text-[11px] text-[#9ba7ae] mt-0.5">
                                        {(p.criterios ?? []).length} criterio{(p.criterios ?? []).length !== 1 ? 's' : ''}
                                        {p.docente_nombre ? ` · ${p.docente_nombre}` : ''}
                                    </p>
                                </button>
                            ))}
                        </div>

                        {/* Vista previa */}
                        <div className="overflow-y-auto p-5">
                            {seleccionada
                                ? <VistaPrevia plantilla={seleccionada} />
                                : <p className="text-[12px] text-[#9ba7ae] text-center py-10">Selecciona una plantilla para ver su vista previa.</p>
                            }
                        </div>
                    </div>
                )}

                {/* Pie */}
                <div className="flex justify-end gap-2 px-6 py-4 border-t border-[#e1e3e4]">
                    <button
                        onClick={onCerrar}
                        disabled={procesando}
                        className="h-11 px-5 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={() => seleccionada && onSeleccionar(seleccionada)}
                        disabled={!seleccionada || procesando}
                        className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-bold text-[13px] hover:bg-[#b71c1c] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {procesando ? 'Creando rúbrica...' : 'Usar esta plantilla'}
                    </button>
                </div>
            </div>
        </div>
    )
}
