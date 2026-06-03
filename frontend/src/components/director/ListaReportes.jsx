import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { reportesApi } from '../../services/docenteApi'
import { periodosApi } from '../../services/api'

// Normaliza el resultado de indicadoresDashboard al shape que usa el componente
function normalizarProyecto(p) {
    return {
        ...p,
        aprobados: p.entregables_aprobados ?? p.aprobados ?? 0,
    }
}

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconSearch() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <circle cx="8.5" cy="8.5" r="5.5" /><path d="M15 15l3 3" />
        </svg>
    )
}

function IconArrow() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 3l5 5-5 5" />
        </svg>
    )
}

function IconFile() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 2h8l4 4v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z" />
            <path d="M12 2v4h4M7 10h6M7 13h4" />
        </svg>
    )
}

// ── Estado badge ──────────────────────────────────────────────────────────────

const ESTADO_CFG = {
    activo:     { bg: 'bg-blue-50',   text: 'text-blue-700',   label: 'Activo' },
    completado: { bg: 'bg-green-50',  text: 'text-green-700',  label: 'Completado' },
    pausado:    { bg: 'bg-orange-50', text: 'text-orange-700', label: 'Pausado' },
    cancelado:  { bg: 'bg-red-50',    text: 'text-[#d32f2f]',  label: 'Cancelado' },
    borrador:   { bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]', label: 'Borrador' },
}

function EstadoBadge({ estado }) {
    const cfg = ESTADO_CFG[estado] ?? { bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]', label: estado }
    return (
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg ${cfg.bg} ${cfg.text}`}>
            {cfg.label}
        </span>
    )
}

function ProgressBar({ value }) {
    const pct = Math.min(Math.max(value, 0), 100)
    const color = pct >= 60 ? '#4caf50' : pct >= 30 ? '#ffa726' : '#ef5350'
    return (
        <div className="relative h-1.5 bg-[#f0f2f3] rounded-full overflow-hidden">
            <div className="absolute left-0 top-0 h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
    )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function ListaReportes() {
    const navigate = useNavigate()
    const [periodos, setPeriodos] = useState([])
    const [periodoSel, setPeriodoSel] = useState('')
    const [reporte, setReporte] = useState(null)
    const [cargando, setCargando] = useState(false)
    const [error, setError] = useState(null)
    const [busqueda, setBusqueda] = useState('')

    useEffect(() => {
        periodosApi.listar().then(setPeriodos).catch(() => {})
    }, [])

    useEffect(() => {
        if (!periodoSel) { setReporte(null); return }
        async function cargar() {
            setCargando(true)
            setError(null)
            try {
                const res = await reportesApi.indicadoresDashboard({ periodoId: periodoSel })
                setReporte(res)
            } catch {
                setError('No se pudo cargar el reporte.')
            } finally {
                setCargando(false)
            }
        }
        cargar()
    }, [periodoSel])

    const periodoNombre = (() => {
        const raw = reporte?.resumen_periodo
        const r = Array.isArray(raw) ? raw[0] : raw
        return r?.periodo_nombre ?? ''
    })()

    const proyectosFiltrados = (reporte?.proyectos ?? [])
        .map(normalizarProyecto)
        .filter(p => p.nombre.toLowerCase().includes(busqueda.toLowerCase()))

    return (
        <div className="p-4 sm:p-6 flex flex-col gap-5">
            {/* Encabezado */}
            <div>
                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">Director</p>
                <h1 className="text-[22px] font-extrabold text-[#191c1d]">Reportes por proyecto</h1>
                <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                    Selecciona un curso para ver sus proyectos y generar reportes detallados.
                </p>
            </div>

            {/* Selector de curso/período */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                <p className="text-[13px] font-semibold text-[#191c1d] mb-3">Seleccionar período</p>
                <div className="flex gap-3 flex-wrap">
                    <select
                        value={periodoSel}
                        onChange={e => { setPeriodoSel(e.target.value); setBusqueda('') }}
                        className="flex-1 min-w-[200px] border border-[#e1e3e4] rounded-xl px-3 py-2 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/30"
                    >
                        <option value="">— Seleccionar período —</option>
                        {periodos.map(p => (
                            <option key={p.id} value={p.id}>{p.nombre ?? `Curso ${p.id}`}</option>
                        ))}
                    </select>
                    {periodoSel && (
                        <div className="relative flex-1 min-w-[180px]">
                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9ba7ae]">
                                <IconSearch />
                            </div>
                            <input
                                type="text"
                                placeholder="Buscar proyecto..."
                                value={busqueda}
                                onChange={e => setBusqueda(e.target.value)}
                                className="w-full border border-[#e1e3e4] rounded-xl pl-9 pr-3 py-2 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/30"
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* Contenido */}
            {!periodoSel && (
                <div className="flex flex-col items-center justify-center py-16 text-[#9ba7ae]">
                    <IconFile />
                    <p className="text-[14px] font-medium mt-3">Selecciona un curso para continuar</p>
                </div>
            )}

            {cargando && (
                <div className="flex justify-center py-10">
                    <div className="w-7 h-7 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                </div>
            )}

            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error}
                </div>
            )}

            {reporte && !cargando && (
                <>
                    <div className="flex items-center gap-2 -mb-2">
                        <h2 className="text-[15px] font-bold text-[#191c1d]">{periodoNombre}</h2>
                        <span className="text-[12px] text-[#9ba7ae]">· {proyectosFiltrados.length} proyecto(s)</span>
                    </div>

                    {proyectosFiltrados.length === 0 ? (
                        <div className="text-center py-10 text-[#9ba7ae] text-[13px]">
                            {busqueda ? 'Sin proyectos que coincidan con la búsqueda.' : 'Sin proyectos en este curso.'}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-3">
                            {proyectosFiltrados.map(p => (
                                <div
                                    key={p.id}
                                    className="bg-white rounded-2xl border border-[#e1e3e4] p-5 hover:border-[#d32f2f]/40 hover:shadow-sm transition-all cursor-pointer"
                                    onClick={() => navigate(`/director/reportes/proyecto/${p.id}`)}
                                >
                                    <div className="flex items-start justify-between gap-3 mb-3">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[14px] font-bold text-[#191c1d] truncate">{p.nombre}</p>
                                            <p className="text-[12px] text-[#9ba7ae] mt-0.5">
                                                {p.fecha_inicio} – {p.fecha_fin_estimada}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-2 flex-shrink-0">
                                            <EstadoBadge estado={p.estado} />
                                            <button className="text-[#d32f2f] hover:text-[#c62828] transition-colors">
                                                <IconArrow />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 mb-1.5">
                                        <span className="text-[12px] text-[#9ba7ae] w-14 flex-shrink-0">
                                            {Number(p.porcentaje_progreso ?? 0).toFixed(0)}%
                                        </span>
                                        <div className="flex-1">
                                            <ProgressBar value={Number(p.porcentaje_progreso ?? 0)} />
                                        </div>
                                    </div>

                                    <div className="flex gap-4 mt-3 text-[12px] text-[#9ba7ae]">
                                        <span>{p.actividades_completadas ?? 0}/{p.total_actividades ?? 0} actividades</span>
                                        <span>{p.aprobados ?? 0}/{p.total_entregables ?? 0} entregables aprobados</span>
                                        {p.nota_promedio_grupo != null && (
                                            <span className="font-semibold text-[#4c616c]">
                                                Nota prom: {Number(p.nota_promedio_grupo).toFixed(2)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
