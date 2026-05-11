import { useState, useEffect } from 'react'
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom'
import { actividadesApi } from '../../services/docenteApi'

function IconPlus() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M10 4v12M4 10h12" />
        </svg>
    )
}

function IconEdit() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2l4 4-10 10H4v-4L14 2z" />
        </svg>
    )
}

function IconTrash() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 5h14M8 5V3h4v2M6 5v11a1 1 0 001 1h6a1 1 0 001-1V5" />
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

function IconInbox() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 13l2-8h12l2 8H2z" /><path d="M2 13h4l1 2h6l1-2h4" />
        </svg>
    )
}

const PRIORIDAD_CONFIG = {
    alta:  { label: 'Alta',  color: 'bg-red-100 text-red-700' },
    media: { label: 'Media', color: 'bg-amber-100 text-amber-700' },
    baja:  { label: 'Baja',  color: 'bg-blue-100 text-blue-700' },
}

const ESTADO_CONFIG = {
    pendiente:   { label: 'Pendiente',   color: 'bg-gray-100 text-gray-600' },
    en_progreso: { label: 'En progreso', color: 'bg-blue-100 text-blue-700' },
    completada:  { label: 'Completada',  color: 'bg-green-100 text-green-700' },
    bloqueada:   { label: 'Bloqueada',   color: 'bg-red-100 text-red-700' },
}

function Badge({ config, value }) {
    const cfg = config[value] || Object.values(config)[0]
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${cfg.color}`}>
            {cfg.label}
        </span>
    )
}

function ErrorBanner({ message }) {
    if (!message) return null
    return (
        <div className="mx-6 mt-4 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
            {message}
        </div>
    )
}

function Modal({ open, title, children }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
                <div className="px-6 py-4 border-b border-[#e1e3e4]">
                    <h3 className="text-[17px] font-bold text-[#191c1d]">{title}</h3>
                </div>
                {children}
            </div>
        </div>
    )
}

export default function GestionActividades() {
    const { proyectoId, faseId } = useParams()
    const location = useLocation()
    const navigate = useNavigate()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre
    const faseNombre = location.state?.faseNombre

    const [actividades, setActividades] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalOpen, setModalOpen] = useState(false)
    const [editando, setEditando] = useState(null)
    const [confirmDelete, setConfirmDelete] = useState(null)
    const [guardando, setGuardando] = useState(false)
    const [modalError, setModalError] = useState('')
    const [filtroEstado, setFiltroEstado] = useState('')
    const [filtrosPrioridad, setFiltrosPrioridad] = useState('')

    const [form, setForm] = useState({
        nombre: '',
        descripcion: '',
        fecha_limite: '',
        prioridad: 'media',
        estado: 'pendiente',
    })

    useEffect(() => { cargarActividades() }, [faseId])

    async function cargarActividades() {
        setLoading(true)
        try {
            const data = await actividadesApi.listarPorFase(faseId)
            setActividades(data)
        } catch (err) {
            console.error('Error cargando actividades:', err)
        } finally {
            setLoading(false)
        }
    }

    function abrirModal(actividad = null) {
        setModalError('')
        if (actividad) {
            setEditando(actividad)
            setForm({
                nombre: actividad.nombre,
                descripcion: actividad.descripcion || '',
                fecha_limite: actividad.fecha_limite || '',
                prioridad: actividad.prioridad,
                estado: actividad.estado,
            })
        } else {
            setEditando(null)
            setForm({ nombre: '', descripcion: '', fecha_limite: '', prioridad: 'media', estado: 'pendiente' })
        }
        setModalOpen(true)
    }

    async function guardarActividad() {
        setModalError('')
        setGuardando(true)
        try {
            const payload = {
                nombre: form.nombre.trim(),
                descripcion: form.descripcion.trim() || null,
                prioridad: form.prioridad,
                estado: form.estado,
            }
            if (form.fecha_limite) payload.fecha_limite = form.fecha_limite

            if (editando) {
                await actividadesApi.editar(editando.id, payload)
            } else {
                await actividadesApi.crear(faseId, payload)
            }
            await cargarActividades()
            setModalOpen(false)
        } catch (err) {
            const detail = err.data?.detail || err.data?.fecha_limite?.[0] || err.data?.nombre?.[0]
            setModalError(detail || 'Error al guardar la actividad.')
        } finally {
            setGuardando(false)
        }
    }

    async function eliminarActividad(actividadId) {
        try {
            await actividadesApi.eliminar(actividadId)
            await cargarActividades()
            setConfirmDelete(null)
        } catch (err) {
            setConfirmDelete(prev => ({
                ...prev,
                error: err.data?.detail || 'No se pudo eliminar la actividad.',
            }))
        }
    }

    const actividadesFiltradas = actividades.filter(a => {
        if (filtroEstado && a.estado !== filtroEstado) return false
        if (filtrosPrioridad && a.prioridad !== filtrosPrioridad) return false
        return true
    })

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-5 flex items-center gap-2 text-[13px] flex-wrap">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                {cursoId && (
                    <>
                        <IconChevron />
                        <Link to={`/docente/cursos/${cursoId}`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                            {cursoNombre ?? 'Curso'}
                        </Link>
                    </>
                )}
                {proyectoNombre && (
                    <>
                        <IconChevron />
                        <span className="text-[#9ba7ae]">{proyectoNombre}</span>
                    </>
                )}
                <IconChevron />
                <Link to={`/docente/proyectos/${proyectoId}/fases`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                    Fases
                </Link>
                <IconChevron />
                <span className="text-[#191c1d] font-semibold">{faseNombre ?? 'Actividades'}</span>
            </div>

            {/* Header */}
            <div className="flex items-start justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Actividades</h1>
                    {faseNombre && (
                        <p className="text-[13px] text-[#9ba7ae]">Fase: <span className="font-semibold text-[#4c616c]">{faseNombre}</span></p>
                    )}
                </div>
                <button onClick={() => abrirModal()}
                    className="flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold shadow-sm flex-shrink-0">
                    <IconPlus />Nueva actividad
                </button>
            </div>

            {/* Filtros */}
            <div className="flex flex-wrap gap-2 mb-4">
                <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}
                    className="px-3 py-2 border border-[#e1e3e4] rounded-xl text-[13px] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20">
                    <option value="">Todos los estados</option>
                    <option value="pendiente">Pendiente</option>
                    <option value="en_progreso">En progreso</option>
                    <option value="completada">Completada</option>
                    <option value="bloqueada">Bloqueada</option>
                </select>
                <select value={filtrosPrioridad} onChange={e => setFiltrosPrioridad(e.target.value)}
                    className="px-3 py-2 border border-[#e1e3e4] rounded-xl text-[13px] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20">
                    <option value="">Todas las prioridades</option>
                    <option value="alta">Alta</option>
                    <option value="media">Media</option>
                    <option value="baja">Baja</option>
                </select>
            </div>

            {/* Lista */}
            {loading ? (
                <div className="text-center py-16 text-[#9ba7ae] text-[14px]">Cargando actividades...</div>
            ) : actividadesFiltradas.length === 0 ? (
                <div className="text-center py-16 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-12 h-12 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3">
                        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-[#9ba7ae]" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2M12 12v4M10 14h4" />
                        </svg>
                    </div>
                    <p className="text-[14px] font-semibold text-[#4c616c] mb-1">
                        {actividades.length === 0 ? 'Sin actividades' : 'Sin resultados'}
                    </p>
                    <p className="text-[13px] text-[#9ba7ae]">
                        {actividades.length === 0
                            ? 'Crea la primera actividad para esta fase.'
                            : 'Ninguna actividad coincide con los filtros aplicados.'}
                    </p>
                </div>
            ) : (
                <div className="space-y-2">
                    {actividadesFiltradas.map(a => (
                        <div key={a.id} className="bg-white border border-[#e1e3e4] rounded-xl p-4 hover:shadow-sm transition-all group">
                            <div className="flex items-start gap-3">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-3 mb-1">
                                        <h3 className="text-[15px] font-bold text-[#191c1d]">{a.nombre}</h3>
                                        <div className="flex items-center gap-1.5 flex-shrink-0">
                                            <Badge config={PRIORIDAD_CONFIG} value={a.prioridad} />
                                            <Badge config={ESTADO_CONFIG} value={a.estado} />
                                        </div>
                                    </div>
                                    {a.descripcion && (
                                        <p className="text-[13px] text-[#4c616c] leading-relaxed">{a.descripcion}</p>
                                    )}
                                    {a.fecha_limite && (
                                        <div className="flex items-center gap-1.5 text-[12px] text-[#9ba7ae] mt-2">
                                            <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                                <rect x="1" y="2" width="14" height="12" rx="1.5" /><path d="M1 6h14M5 1v2M11 1v2" />
                                            </svg>
                                            <span>Límite: {new Date(a.fecha_limite + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                                    <button
                                        onClick={() => navigate(
                                            `/docente/proyectos/${proyectoId}/fases/${faseId}/actividades/${a.id}/entregables`,
                                            { state: location.state }
                                        )}
                                        className="p-2 rounded-lg hover:bg-[#f0f2f3] text-[#4c616c] hover:text-[#191c1d] transition-colors"
                                        title="Ver entregables">
                                        <IconInbox />
                                    </button>
                                    <button onClick={() => abrirModal(a)}
                                        className="p-2 rounded-lg hover:bg-[#f0f2f3] text-[#4c616c] hover:text-[#191c1d] transition-colors">
                                        <IconEdit />
                                    </button>
                                    <button onClick={() => setConfirmDelete(a)}
                                        className="p-2 rounded-lg hover:bg-[#fff1f0] text-[#ba1a1a] transition-colors">
                                        <IconTrash />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal Crear/Editar */}
            <Modal open={modalOpen} onClose={() => !guardando && setModalOpen(false)} title={editando ? 'Editar actividad' : 'Nueva actividad'}>
                <ErrorBanner message={modalError} />
                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Nombre *</label>
                        <input
                            type="text"
                            value={form.nombre}
                            onChange={e => { setForm({ ...form, nombre: e.target.value }); setModalError('') }}
                            placeholder="Nombre de la actividad..."
                            autoFocus
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Descripción</label>
                        <textarea
                            value={form.descripcion}
                            onChange={e => setForm({ ...form, descripcion: e.target.value })}
                            rows={3}
                            placeholder="Describe qué se debe hacer en esta actividad..."
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Prioridad</label>
                            <select value={form.prioridad} onChange={e => setForm({ ...form, prioridad: e.target.value })}
                                className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]">
                                <option value="alta">Alta</option>
                                <option value="media">Media</option>
                                <option value="baja">Baja</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Estado</label>
                            <select value={form.estado} onChange={e => setForm({ ...form, estado: e.target.value })}
                                className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]">
                                <option value="pendiente">Pendiente</option>
                                <option value="en_progreso">En progreso</option>
                                <option value="completada">Completada</option>
                                <option value="bloqueada">Bloqueada</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Fecha límite</label>
                        <input
                            type="date"
                            value={form.fecha_limite}
                            onChange={e => { setForm({ ...form, fecha_limite: e.target.value }); setModalError('') }}
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                </div>
                <div className="px-6 py-4 border-t border-[#e1e3e4] flex gap-2">
                    <button onClick={() => setModalOpen(false)} disabled={guardando}
                        className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={guardarActividad} disabled={!form.nombre.trim() || guardando}
                        className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        {guardando ? 'Guardando...' : editando ? 'Guardar cambios' : 'Crear actividad'}
                    </button>
                </div>
            </Modal>

            {/* Modal Confirmar eliminar */}
            <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Eliminar actividad">
                {confirmDelete?.error && <ErrorBanner message={confirmDelete.error} />}
                <div className="p-6">
                    <div className="w-12 h-12 rounded-full bg-[#ffdad6] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-6 h-6 text-[#ba1a1a]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                        </svg>
                    </div>
                    <p className="text-[14px] text-[#4c616c] text-center mb-1">
                        ¿Eliminar la actividad <strong className="text-[#191c1d]">{confirmDelete?.nombre}</strong>?
                    </p>
                    <p className="text-[13px] text-[#9ba7ae] text-center">Esta acción no se puede deshacer.</p>
                </div>
                <div className="flex gap-2 px-6 py-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={() => setConfirmDelete(null)}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button onClick={() => eliminarActividad(confirmDelete.id)}
                        className="flex-1 h-11 rounded-xl bg-[#ba1a1a] text-white font-semibold text-[13px] hover:bg-[#930014] transition-colors">
                        Eliminar
                    </button>
                </div>
            </Modal>
        </div>
    )
}