import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { cursosApi, equiposApi } from '../../services/docenteApi'

const TEAM_COLORS = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f', '#0097a7']

function Avatar({ iniciales, colorIndex, size = 'md' }) {
    const sz = size === 'sm' ? 'w-7 h-7 text-[10px]' : 'w-8 h-8 text-[11px]'
    return (
        <div style={{ backgroundColor: TEAM_COLORS[colorIndex % TEAM_COLORS.length] }}
            className={`${sz} rounded-full flex items-center justify-center text-white font-bold ring-2 ring-white flex-shrink-0`}>
            {iniciales}
        </div>
    )
}

function IconUsers() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="7" cy="7" r="3" />
            <path d="M1 17a6 6 0 0112 0" />
            <path d="M13 5a3 3 0 110 6" opacity="0.7" />
            <path d="M16 17a5 5 0 00-3-4.6" opacity="0.7" />
        </svg>
    )
}

function IconTeam() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="7" height="7" rx="1.5" />
            <rect x="11" y="3" width="7" height="7" rx="1.5" />
            <rect x="2" y="12" width="7" height="5" rx="1.5" />
            <rect x="11" y="12" width="7" height="5" rx="1.5" />
        </svg>
    )
}

export default function EquiposCurso() {
    const { id: cursoId } = useParams()
    const [proyectos, setProyectos] = useState([])
    const [equiposMap, setEquiposMap] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => { cargarDatos() }, [cursoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        try {
            const proyectosData = await cursosApi.obtenerProyectos(cursoId)
            const lista = proyectosData.results ?? proyectosData
            setProyectos(lista)

            const map = {}
            await Promise.all(
                lista.map(async p => {
                    try {
                        const eqData = await equiposApi.obtenerPorProyecto(p.id)
                        map[p.id] = eqData.equipos ?? []
                    } catch {
                        map[p.id] = []
                    }
                })
            )
            setEquiposMap(map)
        } catch (err) {
            setError('No se pudo cargar la información de equipos.')
        } finally {
            setLoading(false)
        }
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
            <div className="flex-1 flex flex-col items-center justify-center gap-3 px-4">
                <div className="w-16 h-16 rounded-2xl bg-[#ffdad6] flex items-center justify-center">
                    <svg className="w-8 h-8 text-[#af101a]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                </div>
                <h2 className="text-[17px] font-bold text-[#191c1d]">Error</h2>
                <p className="text-[13px] text-[#9ba7ae]">{error}</p>
                <button onClick={cargarDatos} className="h-9 px-4 rounded-xl bg-[#d32f2f] text-white text-[13px] font-semibold hover:bg-[#af101a] transition-colors">
                    Reintentar
                </button>
            </div>
        )
    }

    const totalEquipos = Object.values(equiposMap).reduce((acc, arr) => acc + arr.length, 0)

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px] flex-wrap">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <Link to={`/docente/cursos/${cursoId}`} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Curso</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="text-[#191c1d] font-medium truncate max-w-[200px]">Equipos</span>
            </div>

            {/* Encabezado */}
            <div className="mb-6">
                <h1 className="text-[24px] font-bold text-[#191c1d] mb-1">Equipos del curso</h1>
                <p className="text-[13px] text-[#9ba7ae]">{totalEquipos} equipo{totalEquipos !== 1 ? 's' : ''} en {proyectos.length} proyecto{proyectos.length !== 1 ? 's' : ''}</p>
            </div>

            {/* Listado por proyecto */}
            {proyectos.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#fdf6f0] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#f57c00]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6M12 18v-6M9 15h6" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">No hay proyectos</h3>
                    <p className="text-[13px] text-[#9ba7ae]">Crea un proyecto para comenzar a formar equipos.</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {proyectos.map((p, idxProy) => {
                        const equipos = equiposMap[p.id] ?? []
                        return (
                            <section key={p.id}>
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="w-8 h-8 rounded-lg bg-[#d32f2f] flex items-center justify-center shadow-sm">
                                        <svg viewBox="0 0 20 20" className="w-5 h-6 text-white" fill="currentColor">
                                            <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                            <path d="M6 10v4c0 2.5 3.5 4 6 4s6-1.5 6-4v-4l-6 3-6-3z" opacity="0.9" />
                                        </svg>
                                    </div>
                                    <h2 className="text-[17px] font-bold text-[#191c1d]">{p.nombre}</h2>
                                    <span className="text-[12px] text-[#9ba7ae]">({equipos.length} equipo{equipos.length !== 1 ? 's' : ''})</span>
                                </div>

                                {equipos.length === 0 ? (
                                    <div className="bg-[#f8f9fa] rounded-xl border border-[#e1e3e4] p-8 text-center">
                                        <p className="text-[13px] text-[#9ba7ae]">Este proyecto aún no tiene equipos.</p>
                                    </div>
                                ) : (
                                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                        {equipos.map((eq, idxEq) => (
                                            <div key={eq.id} className="bg-white rounded-2xl border border-[#e1e3e4] p-5 hover:shadow-md transition-all flex flex-col gap-3">
                                                <div className="flex items-start gap-3">
                                                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-[15px] font-bold flex-shrink-0"
                                                        style={{ backgroundColor: TEAM_COLORS[idxEq % TEAM_COLORS.length] }}>
                                                        {eq.nombre[0].toUpperCase()}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="text-[15px] font-bold text-[#191c1d] leading-tight truncate">{eq.nombre}</h3>
                                                        {eq.descripcion && <p className="text-[12px] text-[#9ba7ae] line-clamp-1">{eq.descripcion}</p>}
                                                    </div>
                                                </div>

                                                <div className="flex items-center justify-between text-[12px] text-[#9ba7ae]">
                                                    <span>{eq.cantidad_miembros} / {eq.cupo_maximo} miembros</span>
                                                    {eq.lider && (
                                                        <span className="text-[11px] font-semibold text-[#92400e] bg-[#fef9c3] px-2 py-0.5 rounded-md">
                                                            👑 {eq.lider.nombre?.split(' ')[0]}
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Miembros */}
                                                {eq.miembros && eq.miembros.length > 0 && (
                                                    <div className="flex items-center gap-2 pt-2 border-t border-[#f0f2f3]">
                                                        <div className="flex -space-x-1.5">
                                                            {eq.miembros.slice(0, 4).map((m, i) => (
                                                                <Avatar key={m.id} iniciales={m.iniciales} colorIndex={i} size="sm" />
                                                            ))}
                                                            {eq.miembros.length > 4 && (
                                                                <div className="w-7 h-7 rounded-full border-2 border-white bg-[#f0f2f3] flex items-center justify-center text-[9px] font-semibold text-[#4c616c]">
                                                                    +{eq.miembros.length - 4}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <span className="text-[11px] text-[#9ba7ae]">
                                                            {eq.miembros.map(m => m.nombre_completo).join(', ')}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        )
                    })}
                </div>
            )}
        </div>
    )
}