import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { equiposApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']
const TEAM_COLORS   = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f', '#0097a7']

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconEye() {
    return (
        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5z" />
            <circle cx="8" cy="8" r="2" />
        </svg>
    )
}
function IconEdit() {
    return (
        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M11 2l3 3-9 9H2v-3l9-9z" />
        </svg>
    )
}
function IconTrash() {
    return (
        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M2 4h12M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1M6 7v5M10 7v5M3 4l1 9a1 1 0 001 1h6a1 1 0 001-1l1-9" />
        </svg>
    )
}
function IconPerson() {
    return (
        <svg className="w-3 h-3" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-6 6s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z" />
        </svg>
    )
}
function IconPlus() {
    return (
        <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M8 3v10M3 8h10" />
        </svg>
    )
}
function IconPeople() {
    return (
        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="6" cy="5" r="2.5" />
            <path d="M1 13c0-2 2-3.5 5-3.5s5 1.5 5 3.5" />
            <circle cx="12" cy="4" r="2" />
            <path d="M11 9c.5-.2 1-.3 1.5-.3 2 0 3 1.2 3 2.8" />
        </svg>
    )
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function Avatar({ iniciales, colorIndex }) {
    return (
        <div
            style={{ backgroundColor: AVATAR_COLORS[colorIndex % AVATAR_COLORS.length] }}
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[11px] font-bold ring-2 ring-white flex-shrink-0"
        >
            {iniciales}
        </div>
    )
}

// ── Tarjeta de equipo ─────────────────────────────────────────────────────────

function TarjetaEquipo({ equipo, teamIndex, onAgregar }) {
    const miembrosActivos = (equipo.miembros ?? []).filter(m => m.estado === 'activo')

    return (
        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 flex flex-col gap-3">

            {/* Cabecera */}
            <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                    <h3 className="text-[15px] font-bold text-[#191c1d] leading-tight truncate">{equipo.nombre}</h3>
                    {equipo.descripcion && (
                        <p className="text-[13px] text-[#9ba7ae] mt-0.5 line-clamp-1">{equipo.descripcion}</p>
                    )}
                </div>
                <div className="flex items-center gap-0.5 flex-shrink-0">
                    <button className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Ver detalles">
                        <IconEye />
                    </button>
                    <button className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Editar equipo">
                        <IconEdit />
                    </button>
                    <button className="w-7 h-7 rounded-lg text-[#ba1a1a] hover:bg-[#ffdad6] flex items-center justify-center transition-colors" title="Eliminar equipo">
                        <IconTrash />
                    </button>
                </div>
            </div>

            {/* Miembros */}
            <div className="flex items-center gap-2">
                <div className="flex -space-x-1.5">
                    {miembrosActivos.slice(0, 5).map((m, i) => (
                        <Avatar key={m.id} iniciales={m.iniciales} colorIndex={i} />
                    ))}
                    {miembrosActivos.length > 5 && (
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold ring-2 ring-white bg-[#f0f2f3] text-[#4c616c]">
                            +{miembrosActivos.length - 5}
                        </div>
                    )}
                </div>
                <span className="text-[13px] text-[#9ba7ae] ml-1">
                    {equipo.cantidad_miembros} miembro{equipo.cantidad_miembros !== 1 ? 's' : ''}
                </span>
            </div>

            {/* Pie */}
            <div className="flex items-center justify-between gap-2 pt-1 border-t border-[#f0f2f3]">
                <div className="flex items-center gap-2 flex-wrap">
                    {equipo.lider ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#fef9c3] text-[#92400e] text-[12px] font-semibold">
                            <IconPerson />
                            {equipo.lider.nombre.split(' ')[0].toUpperCase()}
                        </span>
                    ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#f0f2f3] text-[#9ba7ae] text-[12px]">
                            Sin líder
                        </span>
                    )}
                    <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#f0f2f3] text-[#5b403d] text-[12px] font-medium">
                        {equipo.cantidad_entregables} entregable{equipo.cantidad_entregables !== 1 ? 's' : ''}
                    </span>
                </div>
                <button
                    onClick={() => onAgregar(equipo.id)}
                    className="flex items-center gap-1.5 h-8 px-3 rounded-xl border border-[#e1e3e4] text-[#4c616c] text-[12px] font-semibold hover:bg-[#f0f2f3] transition-colors flex-shrink-0"
                >
                    <IconPlus /> Agregar
                </button>
            </div>
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function GestionEquipos() {
    const { proyectoId } = useParams()
    const navigate = useNavigate()
    const [datos, setDatos]     = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError]     = useState(null)

    useEffect(() => { cargarDatos() }, [proyectoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        try {
            const data = await equiposApi.obtenerPorProyecto(proyectoId)
            setDatos(data)
        } catch {
            setError('No se pudo cargar la información de equipos.')
        } finally {
            setLoading(false)
        }
    }

    function handleAgregar(equipoId) {
        navigate(`/docente/equipos/${equipoId}/asignar`)
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-4">
                <div className="w-16 h-16 rounded-2xl bg-[#ffdad6] flex items-center justify-center">
                    <svg className="w-8 h-8 text-[#af101a]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                </div>
                <h2 className="text-[17px] font-bold text-[#191c1d]">Error al cargar equipos</h2>
                <p className="text-[13px] text-[#9ba7ae]">{error}</p>
                <button onClick={cargarDatos} className="h-9 px-4 rounded-xl bg-[#d32f2f] text-white text-[13px] font-semibold hover:bg-[#af101a] transition-colors">
                    Reintentar
                </button>
            </div>
        )
    }

    const curso    = datos?.curso    ?? {}
    const equipos  = datos?.equipos  ?? []
    const cantEq   = datos?.cantidad_equipos    ?? equipos.length
    const cantEst  = datos?.cantidad_estudiantes ?? 0

    return (
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px]">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="text-[#191c1d] font-medium">Gestión de Equipos</span>
            </div>

            {/* Encabezado */}
            <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
                <div>
                    {(curso.nombre || curso.codigo) && (
                        <p className="text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">
                            {curso.nombre}{curso.nombre && curso.codigo ? ' · ' : ''}{curso.codigo}
                        </p>
                    )}
                    <h1 className="text-[26px] font-bold text-[#191c1d] leading-tight">Gestión de Equipos</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-1">
                        {cantEq} equipo{cantEq !== 1 ? 's' : ''} · {cantEst} estudiante{cantEst !== 1 ? 's' : ''} asignado{cantEst !== 1 ? 's' : ''}
                    </p>
                </div>
                <button className="h-10 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm">
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
                    Crear Equipo
                </button>
            </div>

            {/* Tarjetas */}
            {equipos.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center mb-6">
                    <div className="w-16 h-16 rounded-2xl bg-[#f0f2f3] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#9ba7ae]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" />
                            <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">No hay equipos aún</h3>
                    <p className="text-[13px] text-[#9ba7ae] mb-4">Crea el primer equipo para este proyecto</p>
                    <button className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors">
                        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
                        Crear equipo
                    </button>
                </div>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 mb-6">
                    {equipos.map((eq, i) => (
                        <TarjetaEquipo key={eq.id} equipo={eq} teamIndex={i} onAgregar={handleAgregar} />
                    ))}
                </div>
            )}

            {/* Tabla resumen */}
            {equipos.length > 0 && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                    <div className="flex items-center justify-between px-5 py-4 border-b border-[#e1e3e4]">
                        <h2 className="text-[15px] font-bold text-[#191c1d]">Resumen de equipos</h2>
                        <span className="text-[11px] text-[#9ba7ae] font-mono bg-[#f0f2f3] px-2.5 py-1 rounded-lg">
                            GET /api/proyectos/:id/equipos/
                        </span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#e1e3e4]">
                                    {['EQUIPO', 'MIEMBROS', 'LÍDER', 'ENTREGABLES', 'ACCIONES'].map(h => (
                                        <th key={h} className="px-5 py-3 text-left text-[11px] font-semibold text-[#9ba7ae] tracking-wide">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {equipos.map((eq, i) => (
                                    <tr key={eq.id} className="border-b border-[#f0f2f3] last:border-0 hover:bg-[#fafbfc] transition-colors">
                                        <td className="px-5 py-3.5">
                                            <div className="flex items-center gap-2.5">
                                                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: TEAM_COLORS[i % TEAM_COLORS.length] }} />
                                                <span className="text-[13px] font-semibold text-[#191c1d]">{eq.nombre}</span>
                                            </div>
                                        </td>
                                        <td className="px-5 py-3.5">
                                            <div className="flex items-center gap-1.5 text-[13px] text-[#5b403d]">
                                                <IconPeople />{eq.cantidad_miembros}
                                            </div>
                                        </td>
                                        <td className="px-5 py-3.5 text-[13px] text-[#5b403d]">
                                            {eq.lider?.nombre ?? <span className="text-[#9ba7ae]">—</span>}
                                        </td>
                                        <td className="px-5 py-3.5 text-[13px] text-[#5b403d]">{eq.cantidad_entregables}</td>
                                        <td className="px-5 py-3.5">
                                            <div className="flex gap-1">
                                                <button className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Ver"><IconEye /></button>
                                                <button className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Editar"><IconEdit /></button>
                                                <button className="w-7 h-7 rounded-lg text-[#ba1a1a] hover:bg-[#ffdad6] flex items-center justify-center transition-colors" title="Eliminar"><IconTrash /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
