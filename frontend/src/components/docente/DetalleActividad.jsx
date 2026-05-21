import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom'
import { actividadesApi } from '../../services/docenteApi'

// ── Constantes ────────────────────────────────────────────────────────────────

const PRIORIDAD_CONFIG = {
    alta:  { label: 'PRIORIDAD ALTA',   color: 'bg-[#d32f2f] text-white',           icon: '!' },
    media: { label: 'PRIORIDAD MEDIA',  color: 'bg-[#f57c00] text-white',           icon: '~' },
    baja:  { label: 'PRIORIDAD BAJA',   color: 'bg-[#1565c0] text-white',           icon: '↓' },
}

const ESTADO_CONFIG = {
    pendiente:   { label: 'PENDIENTE',    color: 'bg-[#e8f4fd] text-[#1565c0] border border-[#90caf9]' },
    en_progreso: { label: 'EN PROGRESO',  color: 'bg-[#e8f4fd] text-[#1565c0] border border-[#90caf9]' },
    completada:  { label: 'COMPLETADA',   color: 'bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7]' },
    bloqueada:   { label: 'BLOQUEADA',    color: 'bg-[#ffebee] text-[#c62828] border border-[#ef9a9a]' },
}

const AVANCE_PCT = {
    pendiente:   0,
    en_progreso: 50,
    completada:  100,
    bloqueada:   0,
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatFecha(fecha) {
    if (!fecha) return null
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-CO', {
        day: '2-digit', month: 'short', year: 'numeric',
    })
}

function IconCalendar() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M2 7h16M6 2v3M14 2v3" />
        </svg>
    )
}

function IconClock() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 6v4l3 2" />
        </svg>
    )
}

function IconChevron() {
    return (
        <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 3l5 5-5 5" />
        </svg>
    )
}

function IconFile() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 2h8l4 4v12a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" />
            <path d="M14 2v4h4" />
        </svg>
    )
}

function IconUsers() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="6" r="3" />
            <path d="M1 17a7 7 0 0114 0" />
            <circle cx="15" cy="7" r="2.5" />
            <path d="M15 13c2.5 0 4 1.5 4 4" />
        </svg>
    )
}

// ── Componente ────────────────────────────────────────────────────────────────

export default function DetalleActividad() {
    const { proyectoId, faseId, actividadId } = useParams()
    const location  = useLocation()
    const navigate  = useNavigate()

    const [actividad, setActividad] = useState(location.state?.actividad ?? null)
    const [loading,   setLoading]   = useState(!actividad)
    const [error,     setError]     = useState('')

    const navState       = location.state ?? {}
    const proyectoNombre = navState.nombre       ?? 'Proyecto'
    const faseNombre     = navState.faseNombre   ?? 'Fase'
    const cursoId        = navState.cursoId

    useEffect(() => {
        if (!actividad) cargar()
    }, [actividadId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const data = await actividadesApi.obtener(actividadId)
            setActividad(data)
        } catch (err) {
            setError(err?.data?.detail || 'No se pudo cargar la actividad.')
        } finally {
            setLoading(false)
        }
    }

    // ── Loading / Error ───────────────────────────────────────────────────────

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center text-[#9ba7ae] text-[14px]"
                style={{ fontFamily: "'Manrope', sans-serif" }}>
                Cargando actividad...
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex-1 flex items-center justify-center p-6"
                style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl px-4 py-3">
                    {error}
                </div>
            </div>
        )
    }

    if (!actividad) return null

    // ── Datos derivados ───────────────────────────────────────────────────────

    const pCfg      = PRIORIDAD_CONFIG[actividad.prioridad] ?? PRIORIDAD_CONFIG.media
    const eCfg      = ESTADO_CONFIG[actividad.estado]       ?? ESTADO_CONFIG.pendiente
    const avancePct = AVANCE_PCT[actividad.estado]          ?? 0
    const fechaFmt  = formatFecha(actividad.fecha_limite)

    const responsables = (actividad.responsables ?? []).map(r => {
        if (typeof r === 'object') {
            return {
                key:    r.id ?? r.usuario_id ?? Math.random(),
                nombre: r.nombre_completo ?? r.nombre ?? r.username ?? '—',
                rol:    r.rol_interno ?? r.rol ?? '',
            }
        }
        return { key: r, nombre: `Usuario ${r}`, rol: '' }
    })

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6"
            style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <nav className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.7px] text-[#9ba7ae] mb-5 flex-wrap">
                <Link
                    to={`/docente/proyectos/${proyectoId}/fases`}
                    state={navState}
                    className="hover:text-[#4c616c] transition-colors"
                >
                    Proyectos
                </Link>
                <IconChevron />
                <Link
                    to={`/docente/proyectos/${proyectoId}/fases/${faseId}/actividades`}
                    state={navState}
                    className="hover:text-[#4c616c] transition-colors"
                >
                    {proyectoNombre}
                </Link>
                <IconChevron />
                <span className="text-[#d32f2f]">Detalle de Actividad</span>
            </nav>

            {/* Título + badges */}
            <h1 className="text-[24px] font-extrabold text-[#191c1d] tracking-tight mb-4 leading-tight">
                {actividad.nombre}
            </h1>

            <div className="flex items-center gap-2.5 mb-6 flex-wrap">
                {/* Prioridad */}
                <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-extrabold tracking-[0.5px] ${pCfg.color}`}>
                    <span className="text-[13px] font-black">{pCfg.icon}</span>
                    {pCfg.label}
                </span>

                {/* Estado */}
                <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-extrabold tracking-[0.5px] ${eCfg.color}`}>
                    <IconClock />
                    {eCfg.label}
                </span>

                {/* Fecha límite */}
                {fechaFmt && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-[#4c616c] bg-[#f0f2f3]">
                        <IconCalendar />
                        Límite: {fechaFmt}
                    </span>
                )}
            </div>

            {/* Layout principal: descripción + equipo */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">

                {/* Descripción — 2 columnas */}
                <div className="lg:col-span-2 bg-white border border-[#e1e3e4] rounded-2xl p-5">
                    <h2 className="text-[15px] font-bold text-[#191c1d] mb-4">
                        Descripción de la Actividad
                    </h2>
                    {actividad.descripcion ? (
                        <p className="text-[14px] text-[#4c616c] leading-relaxed whitespace-pre-wrap">
                            {actividad.descripcion}
                        </p>
                    ) : (
                        <p className="text-[14px] text-[#9ba7ae] italic">
                            Sin descripción registrada.
                        </p>
                    )}
                </div>

                {/* Equipo Responsable — 1 columna */}
                <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 flex flex-col">
                    <h2 className="text-[15px] font-bold text-[#191c1d] mb-4">
                        Equipo Responsable
                    </h2>

                    {responsables.length > 0 ? (
                        <div className="flex flex-col gap-3 flex-1">
                            {responsables.map(r => (
                                <div key={r.key} className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-[#ffdad6] flex items-center justify-center flex-shrink-0 shadow-sm">
                                        <span className="text-[14px] font-bold text-[#af101a]">
                                            {r.nombre[0]?.toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-[13px] font-bold text-[#191c1d] truncate">{r.nombre}</p>
                                        {r.rol && (
                                            <p className="text-[11px] text-[#9ba7ae] capitalize">{r.rol}</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center gap-2 py-4 text-[#9ba7ae]">
                            <IconUsers />
                            <p className="text-[12px] text-center">Sin responsables asignados</p>
                        </div>
                    )}

                    {/* Botón Gestionar Equipo */}
                    {cursoId && (
                        <button
                            onClick={() => navigate(`/docente/cursos/${cursoId}`, { state: navState })}
                            className="mt-4 w-full py-2 border-2 border-[#d32f2f] text-[#d32f2f] text-[13px] font-bold rounded-xl hover:bg-[#fff1f0] transition-colors"
                        >
                            Gestionar Equipo
                        </button>
                    )}
                </div>
            </div>

            {/* Barra inferior: Estado de avance */}
            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 grid grid-cols-1 sm:grid-cols-2 gap-6">

                {/* Estado de Avance */}
                <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae] mb-2">
                        Estado de Avance
                    </p>
                    <div className="flex items-end gap-2 mb-2">
                        <span className="text-[32px] font-extrabold text-[#d32f2f] leading-none">
                            {avancePct}
                        </span>
                        <span className="text-[18px] font-bold text-[#9ba7ae] mb-0.5">%</span>
                    </div>
                    <div className="h-2.5 bg-[#f0f2f3] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-[#d32f2f] rounded-full transition-all duration-500"
                            style={{ width: `${avancePct}%` }}
                        />
                    </div>
                    <p className="text-[12px] text-[#9ba7ae] mt-1.5 capitalize">
                        {eCfg.label.toLowerCase()}
                    </p>
                </div>

                {/* Fase */}
                <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-[#e8f4fd] flex items-center justify-center flex-shrink-0">
                        <IconFile />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae] mb-1">
                            Fase Asociada
                        </p>
                        <p className="text-[14px] font-bold text-[#191c1d]">{faseNombre}</p>
                        <Link
                            to={`/docente/proyectos/${proyectoId}/fases/${faseId}/actividades`}
                            state={navState}
                            className="text-[12px] text-[#d32f2f] font-semibold hover:underline mt-0.5 inline-block"
                        >
                            Ver actividades →
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}