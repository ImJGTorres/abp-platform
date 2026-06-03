import { useState, useEffect } from 'react'
import { useParams, useNavigate, useOutletContext } from 'react-router-dom'
import { fasesApi, actividadesApi } from '../../services/docenteApi'

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatFecha(f) {
    if (!f) return null
    return new Date(f + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Estado badges ──────────────────────────────────────────────────────────────

const ESTADO_CFG = {
    pendiente:   { label: 'Pendiente',   cls: 'bg-[#f0f2f3] text-[#4c616c]' },
    en_progreso: { label: 'En progreso', cls: 'bg-[#e3f2fd] text-[#1565c0]' },
    completada:  { label: 'Completada',  cls: 'bg-[#e8f5e9] text-[#2e7d32]' },
    bloqueada:   { label: 'Bloqueada',   cls: 'bg-[#ffebee] text-[#c62828]' },
}

const PRIORIDAD_CFG = {
    alta:  { label: 'Alta',  cls: 'bg-[#ffebee] text-[#c62828]' },
    media: { label: 'Media', cls: 'bg-[#fff8e1] text-[#e65100]' },
    baja:  { label: 'Baja',  cls: 'bg-[#e3f2fd] text-[#1565c0]' },
}

// ── Icons ──────────────────────────────────────────────────────────────────────

function IconArrow() {
    return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 8h10M9 4l4 4-4 4" /></svg>
}
function IconCalendar() {
    return <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="1" y="2" width="14" height="12" rx="1.5" /><path d="M1 6h14M5 1v2M11 1v2" /></svg>
}
function IconEmpty() {
    return <svg viewBox="0 0 48 48" fill="none" className="w-14 h-14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="10" width="36" height="30" rx="3" /><path d="M15 10V7a2 2 0 012-2h14a2 2 0 012 2v3" /><path d="M24 22v8M20 26h8" /></svg>
}

// ── Componente principal ───────────────────────────────────────────────────────

export default function DetalleProyectoEstudiante() {
    const { proyectoId } = useParams()
    const navigate = useNavigate()
    const ctx = useOutletContext() ?? {}
    const { proyecto } = ctx

    const [fases,   setFases]   = useState([])
    const [loading, setLoading] = useState(true)
    const [error,   setError]   = useState('')

    useEffect(() => {
        if (proyectoId) cargar()
    }, [proyectoId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const fasesData = await fasesApi.listarPorProyecto(proyectoId)
            const fasesArr  = Array.isArray(fasesData) ? fasesData : (fasesData.results ?? [])

            const actsPorFase = await Promise.all(
                fasesArr.map(f => actividadesApi.listarPorFase(f.id).catch(() => []))
            )

            const fasesConActs = fasesArr.map((f, i) => ({
                ...f,
                actividades: Array.isArray(actsPorFase[i]) ? actsPorFase[i] : (actsPorFase[i]?.results ?? []),
            })).filter(f => f.actividades.length > 0)

            setFases(fasesConActs)
        } catch {
            setError('No se pudieron cargar las actividades.')
        } finally {
            setLoading(false)
        }
    }

    const totalActividades = fases.reduce((s, f) => s + f.actividades.length, 0)

    // ── Loading ──────────────────────────────────────────────────────────────

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center text-[#9ba7ae] text-[14px]"
                style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="flex flex-col items-center gap-3">
                    <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Cargando actividades...</span>
                </div>
            </div>
        )
    }

    // ── Vista ────────────────────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight leading-tight mb-1">
                    Actividades
                </h1>
                <p className="text-[13px] text-[#9ba7ae]">
                    {proyecto?.nombre
                        ? `${proyecto.nombre} · `
                        : ''}
                    {totalActividades} actividad{totalActividades !== 1 ? 'es' : ''} en {fases.length} fase{fases.length !== 1 ? 's' : ''}
                </p>
            </div>

            {error && (
                <div className="mb-4 bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl px-4 py-3">
                    {error}
                </div>
            )}

            {fases.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center gap-4 py-20 text-[#9ba7ae]">
                    <IconEmpty />
                    <div className="text-center">
                        <p className="text-[15px] font-bold text-[#191c1d] mb-1">Sin actividades aún</p>
                        <p className="text-[13px]">El docente aún no ha asignado actividades a tu equipo.</p>
                    </div>
                </div>
            )}

            {/* Fases y actividades */}
            <div className="flex flex-col gap-6">
                {fases.map(fase => (
                    <div key={fase.id}>
                        {/* Cabecera de fase */}
                        <div className="flex items-center gap-3 mb-3">
                            <div className="h-px flex-1 bg-[#e1e3e4]" />
                            <span className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.8px] whitespace-nowrap">
                                {fase.nombre}
                            </span>
                            <div className="h-px flex-1 bg-[#e1e3e4]" />
                        </div>

                        {/* Actividades de la fase */}
                        <div className="flex flex-col gap-2">
                            {fase.actividades.map(a => {
                                const estadoCfg    = ESTADO_CFG[a.estado]    ?? ESTADO_CFG.pendiente
                                const prioridadCfg = PRIORIDAD_CFG[a.prioridad] ?? PRIORIDAD_CFG.media
                                const vencida = a.fecha_limite && new Date(a.fecha_limite) < new Date() && a.estado !== 'completada'

                                return (
                                    <div
                                        key={a.id}
                                        className="bg-white border border-[#e1e3e4] rounded-2xl p-4 hover:border-[#c8cdd0] transition-colors"
                                    >
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="min-w-0 flex-1">
                                                {/* Nombre + badges */}
                                                <div className="flex items-center gap-2 flex-wrap mb-1">
                                                    <p className="text-[14px] font-bold text-[#191c1d]">{a.nombre}</p>
                                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${estadoCfg.cls}`}>
                                                        {estadoCfg.label}
                                                    </span>
                                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${prioridadCfg.cls}`}>
                                                        {prioridadCfg.label}
                                                    </span>
                                                </div>

                                                {/* Descripción */}
                                                {a.descripcion && (
                                                    <p className="text-[12px] text-[#4c616c] mb-1.5 line-clamp-2">{a.descripcion}</p>
                                                )}

                                                {/* Fecha límite */}
                                                {a.fecha_limite && (
                                                    <div className={`flex items-center gap-1 text-[11px] ${vencida ? 'text-[#c62828] font-semibold' : 'text-[#9ba7ae]'}`}>
                                                        <IconCalendar />
                                                        <span>{vencida ? '⚠ Venció' : 'Límite'}: {formatFecha(a.fecha_limite)}</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Botón Entregables */}
                                            <button
                                                onClick={() => navigate(
                                                    `/estudiante/proyectos/${proyectoId}/actividades/${a.id}/entregables`,
                                                    { state: { actividadNombre: a.nombre } }
                                                )}
                                                className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 bg-[#d32f2f] text-white text-[12px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors"
                                            >
                                                <span className="hidden sm:inline">Entregables</span>
                                                <IconArrow />
                                            </button>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}