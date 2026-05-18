import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { request } from '../../services/api'
import RegistroAvance from './RegistroAvances'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconFolder() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M2 5a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" /></svg>
}
function IconActivity() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10h3l2-6 4 12 2-6h3" /></svg>
}
function IconArrow() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 10h12M10 4l6 6-6 6" /></svg>
}
function IconUsers() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><circle cx="7" cy="7" r="3" /><path d="M1 17a6 6 0 0112 0" /><path d="M13 5a3 3 0 110 6" opacity="0.6" /><path d="M16 17a5 5 0 00-3-4.6" opacity="0.6" /></svg>
}
function IconCalendar() {
    return <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="1" y="2" width="14" height="12" rx="1.5" /><path d="M1 6h14M5 1v2M11 1v2" /></svg>
}
function IconChevronDown({ open }) {
    return <svg viewBox="0 0 16 16" fill="none" className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 6l5 5 5-5" /></svg>
}
function IconEmpty() {
    return <svg viewBox="0 0 48 48" fill="none" className="w-12 h-12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="8" y="12" width="32" height="28" rx="3" /><path d="M16 12V9a2 2 0 012-2h12a2 2 0 012 2v3" /><path d="M24 22v8M20 26h8" /></svg>
}
function IconProgress() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10h3l2-6 4 12 2-6h3" /></svg>
}

// ── Constantes ─────────────────────────────────────────────────────────────

const ESTADO_ACTIVIDAD = {
    pendiente:   { label: 'Pendiente',   color: 'bg-gray-100 text-gray-600' },
    en_progreso: { label: 'En progreso', color: 'bg-blue-100 text-blue-700' },
    completada:  { label: 'Completada',  color: 'bg-green-100 text-green-700' },
    bloqueada:   { label: 'Bloqueada',   color: 'bg-red-100 text-red-700' },
}

const PRIORIDAD = {
    alta:  { label: 'Alta',  color: 'bg-red-100 text-red-700' },
    media: { label: 'Media', color: 'bg-amber-100 text-amber-700' },
    baja:  { label: 'Baja',  color: 'bg-blue-100 text-blue-700' },
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function getMisEquipos() {
    const res = await request('/api/mis-equipos/')
    const data = await res.json()
    if (!res.ok) throw data
    return data
}

function formatFecha(f) {
    if (!f) return null
    return new Date(f + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Componente principal ───────────────────────────────────────────────────

export default function DashboardEstudiante({ basePath = '/estudiante' }) {
    const navigate = useNavigate()
    const [equipos, setEquipos] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [expandidos, setExpandidos] = useState({})
    const [avanceModal, setAvanceModal] = useState(null) // { actividadId, actividadNombre }

    useEffect(() => { cargar() }, [])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const data = await getMisEquipos()
            setEquipos(data)
            if (data.length > 0) {
                setExpandidos({ [data[0].equipo.id]: true })
            }
        } catch (err) {
            setError(err.detail || 'Error cargando tu información.')
        } finally {
            setLoading(false)
        }
    }

    function toggle(equipoId) {
        setExpandidos(p => ({ ...p, [equipoId]: !p[equipoId] }))
    }

    function irAEntregables(actividadId, actividadNombre) {
        navigate(`${basePath}/actividades/${actividadId}/entregables`, {
            state: { actividadNombre },
        })
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <p className="text-[14px] text-[#9ba7ae]">Cargando tu información...</p>
            </div>
        )
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Mis proyectos</h1>
                <p className="text-[13px] text-[#9ba7ae]">Actividades asignadas a tu equipo y sus entregables.</p>
            </div>

            {error && (
                <div className="mb-4 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                    {error}
                </div>
            )}

            {equipos.length === 0 ? (
                <div className="text-center py-20 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-14 h-14 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3 text-[#9ba7ae]">
                        <IconEmpty />
                    </div>
                    <p className="text-[15px] font-bold text-[#4c616c] mb-1">Aún no tienes equipo asignado</p>
                    <p className="text-[13px] text-[#9ba7ae]">Cuando el docente te asigne a un equipo, tus proyectos y actividades aparecerán aquí.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {equipos.map(e => {
                        const equipoId = e.equipo.id
                        const abierto = !!expandidos[equipoId]
                        const totalActividades = e.fases.reduce((sum, f) => sum + f.actividades.length, 0)

                        return (
                            <div key={equipoId} className="bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden shadow-sm">

                                {/* Cabecera del equipo */}
                                <div
                                    className="flex items-start gap-4 p-4 sm:p-5 cursor-pointer hover:bg-[#fafafa] transition-colors"
                                    onClick={() => toggle(equipoId)}
                                >
                                    <div className="w-10 h-10 rounded-xl bg-[#ffdad6] flex items-center justify-center flex-shrink-0">
                                        <IconFolder />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h2 className="text-[16px] font-extrabold text-[#191c1d] mb-0.5">{e.equipo.nombre}</h2>
                                        <p className="text-[13px] font-semibold text-[#4c616c]">{e.proyecto.nombre}</p>
                                        <p className="text-[12px] text-[#9ba7ae] mt-0.5">{e.curso.nombre}</p>
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                        <span className="hidden sm:flex items-center gap-1 text-[12px] text-[#9ba7ae]">
                                            <IconActivity />
                                            {totalActividades} actividad{totalActividades !== 1 ? 'es' : ''}
                                        </span>
                                        <IconChevronDown open={abierto} />
                                    </div>
                                </div>

                                {/* Lista de actividades agrupadas por fase */}
                                {abierto && (
                                    <div className="border-t border-[#f0f2f3]">
                                        {totalActividades === 0 ? (
                                            <div className="py-8 text-center">
                                                <p className="text-[13px] font-semibold text-[#4c616c] mb-1">Sin actividades asignadas</p>
                                                <p className="text-[12px] text-[#9ba7ae]">El docente aún no ha asignado actividades a este equipo.</p>
                                            </div>
                                        ) : (
                                            e.fases.map(fase => fase.actividades.length > 0 && (
                                                <div key={fase.id}>
                                                    <div className="px-4 sm:px-5 py-2 bg-[#f8f9fa] border-b border-[#f0f2f3]">
                                                        <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">{fase.nombre}</p>
                                                    </div>
                                                    {fase.actividades.map(a => {
                                                        const estadoCfg = ESTADO_ACTIVIDAD[a.estado] || ESTADO_ACTIVIDAD.pendiente
                                                        const prioridadCfg = PRIORIDAD[a.prioridad] || PRIORIDAD.media
                                                        const vencida = a.fecha_limite && new Date(a.fecha_limite) < new Date() && a.estado !== 'completada'

                                                        return (
                                                            <div key={a.id} className="flex items-start gap-3 px-4 sm:px-5 py-3.5 border-b border-[#f0f2f3] last:border-0 hover:bg-[#fafafa] transition-colors group">
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="flex items-center gap-2 flex-wrap mb-1">
                                                                        <p className="text-[14px] font-bold text-[#191c1d]">{a.nombre}</p>
                                                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${estadoCfg.color}`}>
                                                                            {estadoCfg.label}
                                                                        </span>
                                                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${prioridadCfg.color}`}>
                                                                            {prioridadCfg.label}
                                                                        </span>
                                                                    </div>
                                                                    {a.descripcion && (
                                                                        <p className="text-[12px] text-[#4c616c] mb-1 line-clamp-1">{a.descripcion}</p>
                                                                    )}
                                                                    {a.fecha_limite && (
                                                                        <div className={`flex items-center gap-1 text-[11px] ${vencida ? 'text-[#ba1a1a] font-semibold' : 'text-[#9ba7ae]'}`}>
                                                                            <IconCalendar />
                                                                            <span>{vencida ? 'Venció' : 'Límite'}: {formatFecha(a.fecha_limite)}</span>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                <div className="flex items-center gap-2 flex-shrink-0 opacity-0 group-hover:opacity-100 sm:opacity-100">
                                                                    <button
                                                                        onClick={() => setAvanceModal({ actividadId: a.id, actividadNombre: a.nombre })}
                                                                        className="flex items-center gap-1.5 px-3 py-2 bg-white border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[12px] font-semibold"
                                                                        title="Registrar avance"
                                                                    >
                                                                        <IconProgress />
                                                                        <span className="hidden sm:inline">Avance</span>
                                                                    </button>
                                                                    <button
                                                                        onClick={() => irAEntregables(a.id, a.nombre)}
                                                                        className="flex items-center gap-1.5 px-3 py-2 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[12px] font-semibold"
                                                                    >
                                                                        Entregables
                                                                        <IconArrow />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )
                                                    })}
                                                </div>
                                            ))
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}

                </div>
            )}

            <RegistroAvance
                open={!!avanceModal}
                actividadId={avanceModal?.actividadId}
                actividadNombre={avanceModal?.actividadNombre ?? ''}
                onClose={() => setAvanceModal(null)}
                onSuccess={() => setAvanceModal(null)}
            />
        </div>
    )
}
