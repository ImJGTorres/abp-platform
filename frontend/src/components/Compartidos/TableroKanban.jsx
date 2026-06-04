import { useState, useEffect } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { actividadesApi, fasesApi } from '../../services/docenteApi'
import { buildMediaUrl, session } from '../../services/api'
import RegistroAvance from '../Estudiante/RegistroAvances'
import LineaTiempoAvances from '../Estudiante/LineaTiempoAvances'

const COLUMNAS = [
    { id: 'pendiente',   titulo: 'Pendiente',   color: 'bg-gray-100'  },
    { id: 'en_progreso', titulo: 'En Progreso',  color: 'bg-blue-100'  },
    { id: 'completada',  titulo: 'Completada',   color: 'bg-green-100' },
    { id: 'bloqueada',   titulo: 'Bloqueada',    color: 'bg-red-100'   },
]

const PRIORIDAD_CONFIG = {
    alta:  { label: 'Alta',  color: 'bg-red-100 text-red-700'     },
    media: { label: 'Media', color: 'bg-yellow-100 text-yellow-700' },
    baja:  { label: 'Baja',  color: 'bg-blue-100 text-blue-700'   },
}

function IconFilter() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 5h14l-5 7v5l-4-2V12L3 5z" />
        </svg>
    )
}

function Modal({ open, onClose, title, children, size = 'md' }) {
    if (!open) return null
    const widthClass = size === 'lg' ? 'max-w-4xl' : 'max-w-2xl'
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className={`bg-white rounded-2xl shadow-2xl w-full ${widthClass} max-h-[90vh] overflow-y-auto`} onClick={e => e.stopPropagation()}>
                <div className="px-6 py-4 border-b border-[#e1e3e4] sticky top-0 bg-white z-10">
                    <h3 className="text-[17px] font-bold text-[#191c1d]">{title}</h3>
                </div>
                {children}
            </div>
        </div>
    )
}

function AvatarResponsable({ u }) {
    return (
        <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-full bg-[#ffdad6] flex items-center justify-center overflow-hidden flex-shrink-0">
                {u.foto_perfil ? (
                    <img src={buildMediaUrl(u.foto_perfil)} alt="" className="w-full h-full object-cover"
                        onError={e => { e.target.style.display = 'none' }} />
                ) : (
                    <span className="text-[8px] font-bold text-[#af101a]">{u.nombre?.[0]?.toUpperCase()}</span>
                )}
            </div>
            <span className="text-[11px] text-[#4c616c] font-medium">{u.nombre} {u.apellido}</span>
        </div>
    )
}

function ActividadCard({ actividad, onClick }) {
    const cfg = PRIORIDAD_CONFIG[actividad.prioridad] ?? { label: actividad.prioridad, color: 'bg-gray-100 text-gray-600' }
    const responsables = actividad.responsables ?? []

    return (
        <div onClick={onClick}
            className="bg-white border border-[#e1e3e4] rounded-xl p-4 mb-3 cursor-pointer hover:shadow-md transition-all">
            <div className="flex items-start justify-between gap-2 mb-2">
                <h4 className="text-[14px] font-semibold text-[#191c1d] leading-tight flex-1">{actividad.nombre}</h4>
                <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase flex-shrink-0 ${cfg.color}`}>
                    {cfg.label}
                </span>
            </div>

            {actividad.descripcion && (
                <p className="text-[12px] text-[#9ba7ae] mb-3 line-clamp-2">{actividad.descripcion}</p>
            )}

            {responsables.length > 0 && (
                <div className="flex flex-col gap-1 mb-2">
                    {responsables.map(u => <AvatarResponsable key={u.id} u={u} />)}
                </div>
            )}

            {actividad.fecha_limite && (
                <p className="text-[11px] text-[#9ba7ae]">📅 {new Date(actividad.fecha_limite).toLocaleDateString('es-CO')}</p>
            )}
        </div>
    )
}

export default function TableroKanban() {
    const { proyectoId } = useParams()
    const location = useLocation()
    const user = session.getUser()
    const esEstudiante = user?.tipo_rol === 'estudiante' || user?.tipo_rol === 'lider_equipo'

    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre

    const [fases, setFases] = useState([])
    const [actividades, setActividades] = useState([])
    const [loading, setLoading] = useState(true)
    const [filtroFase, setFiltroFase] = useState('')
    const [filtroPrioridad, setFiltroPrioridad] = useState('')
    const [actividadSeleccionada, setActividadSeleccionada] = useState(null)
    const [modalAvanceOpen, setModalAvanceOpen] = useState(false)

    useEffect(() => {
        if (proyectoId) cargarDatos()
    }, [proyectoId])

    async function cargarDatos() {
        setLoading(true)
        try {
            const fasesData = await fasesApi.listarPorProyecto(proyectoId)
            const sorted = fasesData.sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0))
            setFases(sorted)

            const actPromises = sorted.map(f =>
                actividadesApi.listarPorFase(f.id).then(lista =>
                    lista.map(a => ({ ...a, fase_id: f.id, fase_nombre: f.nombre }))
                )
            )
            const actArrays = await Promise.all(actPromises)
            setActividades(actArrays.flat())
        } catch (err) {
            console.error('Error al cargar datos:', err)
        } finally {
            setLoading(false)
        }
    }

    function getActividadesPorColumna(estadoId) {
        return actividades.filter(a => {
            if (a.estado !== estadoId) return false
            if (filtroFase && a.fase_id !== +filtroFase) return false
            if (filtroPrioridad && a.prioridad !== filtroPrioridad) return false
            return true
        })
    }

    return (
        <div className="flex-1 overflow-hidden flex flex-col p-6">
            <div className="max-w-full mx-auto flex-1 overflow-hidden flex flex-col">

                {/* Breadcrumb — solo visible cuando hay estado de navegación (docente) */}
                {cursoId && (
                    <div className="mb-4 flex items-center gap-2 text-[13px] flex-wrap">
                        <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                        <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                        <Link to={`/docente/cursos/${cursoId}`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                            {cursoNombre ?? 'Curso'}
                        </Link>
                        {proyectoNombre && (
                            <>
                                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                                <span className="text-[#191c1d] font-medium">{proyectoNombre}</span>
                            </>
                        )}
                    </div>
                )}

                <div className="mb-6">
                    <h1 className="text-[24px] font-bold text-[#191c1d] leading-tight mb-1">Tablero Kanban</h1>
                    <p className="text-[13px] text-[#9ba7ae]">Vista de tablero con columnas por estado donde se pueden ver y filtrar todas las actividades del proyecto.</p>
                </div>

                {/* Filtros */}
                <div className="bg-white border border-[#e1e3e4] rounded-xl p-4 mb-4 flex flex-wrap items-center gap-3">
                    <IconFilter />
                    <select value={filtroFase} onChange={e => setFiltroFase(e.target.value)}
                        className="px-3 py-2 border border-[#e1e3e4] rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20">
                        <option value="">Todas las fases</option>
                        {fases.map(f => <option key={f.id} value={f.id}>{f.nombre}</option>)}
                    </select>
                    <select value={filtroPrioridad} onChange={e => setFiltroPrioridad(e.target.value)}
                        className="px-3 py-2 border border-[#e1e3e4] rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20">
                        <option value="">Todas las prioridades</option>
                        <option value="alta">Alta</option>
                        <option value="media">Media</option>
                        <option value="baja">Baja</option>
                    </select>
                    {actividades.length > 0 && (
                        <span className="ml-auto text-[12px] text-[#9ba7ae]">{actividades.length} actividades</span>
                    )}
                </div>

                {/* Tablero */}
                {loading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    </div>
                ) : actividades.length === 0 && fases.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-[#9ba7ae] text-[14px]">
                        Este proyecto aún no tiene fases ni actividades.
                    </div>
                ) : (
                    <div className="flex-1 overflow-x-auto">
                        <div className="flex gap-4 min-w-max pb-4">
                            {COLUMNAS.map(col => {
                                const acts = getActividadesPorColumna(col.id)
                                return (
                                    <div key={col.id} className="flex-shrink-0 w-80">
                                        <div className={`${col.color} rounded-t-xl px-4 py-3 border-b-2 border-[#e1e3e4]`}>
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-[14px] font-bold text-[#191c1d]">{col.titulo}</h3>
                                                <span className="text-[12px] font-semibold text-[#4c616c] bg-white px-2 py-0.5 rounded-full">{acts.length}</span>
                                            </div>
                                        </div>
                                        <div className="bg-[#f8f9fa] rounded-b-xl p-3 min-h-[400px] max-h-[calc(100vh-380px)] overflow-y-auto">
                                            {acts.map(a => (
                                                <ActividadCard key={a.id} actividad={a} onClick={() => setActividadSeleccionada(a)} />
                                            ))}
                                            {acts.length === 0 && (
                                                <p className="text-[12px] text-[#9ba7ae] text-center py-8">Sin actividades</p>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Modal Detalle Actividad */}
            {actividadSeleccionada && (
                <Modal open={!!actividadSeleccionada} onClose={() => { setActividadSeleccionada(null); setModalAvanceOpen(false) }}
                    title={actividadSeleccionada.nombre} size="lg">
                    <div className="p-6">
                        {actividadSeleccionada.fase_nombre && (
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-4">
                                Fase: {actividadSeleccionada.fase_nombre}
                            </p>
                        )}

                        <div className="mb-4">
                            <p className="text-[13px] text-[#9ba7ae] mb-1">Descripción</p>
                            <p className="text-[14px] text-[#191c1d]">{actividadSeleccionada.descripcion || 'Sin descripción'}</p>
                        </div>

                        <div className="mb-6 grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-1">Prioridad</p>
                                {(() => {
                                    const cfg = PRIORIDAD_CONFIG[actividadSeleccionada.prioridad] ?? { label: actividadSeleccionada.prioridad, color: 'bg-gray-100 text-gray-600' }
                                    return <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${cfg.color}`}>{cfg.label}</span>
                                })()}
                            </div>
                            <div>
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-1">Fecha límite</p>
                                <p className="text-[13px] text-[#191c1d]">
                                    {actividadSeleccionada.fecha_limite
                                        ? new Date(actividadSeleccionada.fecha_limite).toLocaleDateString('es-CO')
                                        : 'Sin definir'}
                                </p>
                            </div>
                        </div>

                        <div className="mb-6">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-2">Responsables</p>
                            {actividadSeleccionada.responsables?.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                    {actividadSeleccionada.responsables.map(u => (
                                        <div key={u.id} className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center overflow-hidden flex-shrink-0">
                                                {u.foto_perfil ? (
                                                    <img src={buildMediaUrl(u.foto_perfil)} alt="" className="w-full h-full object-cover"
                                                        onError={e => { e.target.style.display = 'none' }} />
                                                ) : (
                                                    <span className="text-[11px] font-bold text-[#af101a]">{u.nombre?.[0]?.toUpperCase()}</span>
                                                )}
                                            </div>
                                            <span className="text-[14px] text-[#191c1d] font-medium">{u.nombre} {u.apellido}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-[13px] text-[#9ba7ae] italic">Sin responsables asignados</p>
                            )}
                        </div>

                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="text-[15px] font-bold text-[#191c1d]">Avances Registrados</h4>
                                {esEstudiante && (
                                    <button onClick={() => setModalAvanceOpen(true)}
                                        className="px-3 py-1.5 bg-[#d32f2f] text-white rounded-lg text-[12px] font-semibold hover:bg-[#ba1a1a] transition-colors">
                                        + Registrar Avance
                                    </button>
                                )}
                            </div>
                            <LineaTiempoAvances actividadId={actividadSeleccionada.id} />
                        </div>
                    </div>
                    <div className="px-6 py-4 border-t border-[#e1e3e4]">
                        <button onClick={() => { setActividadSeleccionada(null); setModalAvanceOpen(false) }}
                            className="px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold">
                            Cerrar
                        </button>
                    </div>
                </Modal>
            )}

            {/* Modal Registro Avance */}
            {modalAvanceOpen && actividadSeleccionada && (
                <RegistroAvance
                    actividadId={actividadSeleccionada.id}
                    actividadNombre={actividadSeleccionada.nombre}
                    open={modalAvanceOpen}
                    onClose={() => setModalAvanceOpen(false)}
                    onSuccess={() => setModalAvanceOpen(false)}
                />
            )}
        </div>
    )
}