import { useState, useEffect } from 'react'
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom'
import { fasesApi } from '../../services/docenteApi'

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

function IconGrip() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4 text-[#9ba7ae]">
            <circle cx="7" cy="6" r="1.5" fill="currentColor" />
            <circle cx="13" cy="6" r="1.5" fill="currentColor" />
            <circle cx="7" cy="10" r="1.5" fill="currentColor" />
            <circle cx="13" cy="10" r="1.5" fill="currentColor" />
            <circle cx="7" cy="14" r="1.5" fill="currentColor" />
            <circle cx="13" cy="14" r="1.5" fill="currentColor" />
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

function IconCheck() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10l4 4 8-8" />
        </svg>
    )
}

function IconClock() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 5v5l3 3" />
        </svg>
    )
}

function IconProgress() {
    return (
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            <path d="M6 4l10 6-10 6V4z" />
        </svg>
    )
}

const ESTADO_CONFIG = {
    pendiente: { label: 'Pendiente', color: 'bg-gray-100 text-gray-600', icon: <IconClock /> },
    en_progreso: { label: 'En progreso', color: 'bg-blue-100 text-blue-700', icon: <IconProgress /> },
    completada: { label: 'Completada', color: 'bg-green-100 text-green-700', icon: <IconCheck /> },
}

function EstadoBadge({ estado }) {
    const cfg = ESTADO_CONFIG[estado] || ESTADO_CONFIG.pendiente
    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold flex-shrink-0 ${cfg.color}`}>
            {cfg.icon}{cfg.label}
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

export default function GestionFases() {
    const { proyectoId } = useParams()
    const location = useLocation()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre

    const navigate = useNavigate()

    const [fases, setFases] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalOpen, setModalOpen] = useState(false)
    const [editando, setEditando] = useState(null)
    const [confirmDelete, setConfirmDelete] = useState(null)
    const [draggedIndex, setDraggedIndex] = useState(null)
    const [guardando, setGuardando] = useState(false)
    const [modalError, setModalError] = useState('')

    const [form, setForm] = useState({
        nombre: '',
        descripcion: '',
        fecha_inicio: '',
        fecha_fin: '',
    })

    useEffect(() => { cargarFases() }, [proyectoId])

    async function cargarFases() {
        setLoading(true)
        try {
            const data = await fasesApi.listarPorProyecto(proyectoId)
            setFases(data.sort((a, b) => a.orden - b.orden))
        } catch (err) {
            console.error('Error al cargar fases:', err)
        } finally {
            setLoading(false)
        }
    }

    function abrirModal(fase = null) {
        setModalError('')
        if (fase) {
            setEditando(fase)
            setForm({
                nombre: fase.nombre,
                descripcion: fase.descripcion || '',
                fecha_inicio: fase.fecha_inicio || '',
                fecha_fin: fase.fecha_fin || '',
            })
        } else {
            setEditando(null)
            setForm({ nombre: '', descripcion: '', fecha_inicio: '', fecha_fin: '' })
        }
        setModalOpen(true)
    }

    function buildPayload() {
        const payload = { nombre: form.nombre.trim() }
        if (form.descripcion.trim()) payload.descripcion = form.descripcion.trim()
        else payload.descripcion = null
        if (form.fecha_inicio) payload.fecha_inicio = form.fecha_inicio
        if (form.fecha_fin) payload.fecha_fin = form.fecha_fin
        return payload
    }

    async function guardarFase() {
        setModalError('')
        if (!form.fecha_inicio || !form.fecha_fin) {
            setModalError('Las fechas de inicio y fin son obligatorias.')
            return
        }
        setGuardando(true)
        try {
            const payload = buildPayload()
            if (editando) {
                await fasesApi.editar(editando.id, payload)
            } else {
                const orden = fases.length > 0 ? Math.max(...fases.map(f => f.orden)) + 1 : 1
                await fasesApi.crear(proyectoId, { ...payload, orden })
            }
            await cargarFases()
            setModalOpen(false)
        } catch (err) {
            const detail = err.data?.detail || err.data?.fecha_inicio?.[0] || err.data?.fecha_fin?.[0] || err.data?.orden?.[0]
            setModalError(detail || 'Error al guardar la fase. Verifica los datos.')
        } finally {
            setGuardando(false)
        }
    }

    async function eliminarFase(faseId) {
        try {
            await fasesApi.eliminar(faseId)
            await cargarFases()
            setConfirmDelete(null)
        } catch (err) {
            setConfirmDelete(prev => ({
                ...prev,
                error: err.data?.detail || 'No se pudo eliminar la fase.',
            }))
        }
    }

    function handleDragStart(index) { setDraggedIndex(index) }

    function handleDragOver(e, index) {
        e.preventDefault()
        if (draggedIndex === null || draggedIndex === index) return
        const newFases = [...fases]
        const [removed] = newFases.splice(draggedIndex, 1)
        newFases.splice(index, 0, removed)
        setFases(newFases)
        setDraggedIndex(index)
    }

    async function handleDragEnd() {
        if (draggedIndex === null) return
        try {
            await Promise.all(fases.map((fase, idx) => fasesApi.reordenar(fase.id, idx + 1)))
        } catch (err) {
            console.error('Error al reordenar:', err)
            await cargarFases()
        }
        setDraggedIndex(null)
    }

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
                        <span className="text-[#4c616c] font-medium">{proyectoNombre}</span>
                    </>
                )}
                <IconChevron />
                <span className="text-[#191c1d] font-semibold">Fases</span>
            </div>

            {/* Header */}
            <div className="flex items-start justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Fases del proyecto</h1>
                    <p className="text-[13px] text-[#9ba7ae] leading-relaxed">
                        Define y organiza las fases del ciclo de vida del proyecto. Arrastra para reordenarlas.
                    </p>
                </div>
                <button onClick={() => abrirModal()}
                    className="flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold shadow-sm flex-shrink-0">
                    <IconPlus />Nueva fase
                </button>
            </div>

            {/* Lista */}
            {loading ? (
                <div className="text-center py-16 text-[#9ba7ae] text-[14px]">Cargando fases...</div>
            ) : fases.length === 0 ? (
                <div className="text-center py-16 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-12 h-12 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3">
                        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-[#9ba7ae]" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                    </div>
                    <p className="text-[14px] font-semibold text-[#4c616c] mb-1">Sin fases creadas</p>
                    <p className="text-[13px] text-[#9ba7ae]">Agrega la primera fase para comenzar a organizar el proyecto.</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {fases.map((fase, idx) => (
                        <div key={fase.id}
                            draggable
                            onDragStart={() => handleDragStart(idx)}
                            onDragOver={e => handleDragOver(e, idx)}
                            onDragEnd={handleDragEnd}
                            className="bg-white border border-[#e1e3e4] rounded-xl p-4 hover:shadow-sm transition-all cursor-move group">
                            <div className="flex items-start gap-3">
                                <div className="mt-0.5 flex-shrink-0"><IconGrip /></div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-3 mb-1">
                                        <div className="flex-1 min-w-0">
                                            <span className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Fase {idx + 1}</span>
                                            <h3 className="text-[15px] font-bold text-[#191c1d] mt-0.5">{fase.nombre}</h3>
                                            {fase.descripcion && (
                                                <p className="text-[13px] text-[#4c616c] mt-0.5 leading-relaxed">{fase.descripcion}</p>
                                            )}
                                        </div>
                                        <EstadoBadge estado={fase.estado} />
                                    </div>
                                    {(fase.fecha_inicio || fase.fecha_fin) && (
                                        <div className="flex items-center gap-1.5 text-[12px] text-[#9ba7ae] mt-2">
                                            <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                                <rect x="1" y="2" width="14" height="12" rx="1.5" /><path d="M1 6h14M5 1v2M11 1v2" />
                                            </svg>
                                            {fase.fecha_inicio && (
                                                <span>{new Date(fase.fecha_inicio + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                            )}
                                            {fase.fecha_inicio && fase.fecha_fin && <span>—</span>}
                                            {fase.fecha_fin && (
                                                <span>{new Date(fase.fecha_fin + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                            )}
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-center gap-1 flex-shrink-0">
                                    <button
                                        onClick={() => navigate(`/docente/proyectos/${proyectoId}/fases/${fase.id}/actividades`, { state: { ...location.state, faseNombre: fase.nombre } })}
                                        className="px-2.5 py-1.5 text-[12px] font-semibold text-[#d32f2f] hover:bg-[#fff1f0] rounded-lg transition-colors whitespace-nowrap">
                                        Ver actividades
                                    </button>
                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                                        <button onClick={() => abrirModal(fase)}
                                            className="p-2 rounded-lg hover:bg-[#f0f2f3] text-[#4c616c] hover:text-[#191c1d] transition-colors">
                                            <IconEdit />
                                        </button>
                                        <button onClick={() => setConfirmDelete(fase)}
                                            className="p-2 rounded-lg hover:bg-[#fff1f0] text-[#ba1a1a] transition-colors">
                                            <IconTrash />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal Crear/Editar */}
            <Modal open={modalOpen} onClose={() => !guardando && setModalOpen(false)} title={editando ? 'Editar fase' : 'Nueva fase'}>
                <ErrorBanner message={modalError} />
                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Nombre *</label>
                        <input
                            type="text"
                            value={form.nombre}
                            onChange={e => { setForm({ ...form, nombre: e.target.value }); setModalError('') }}
                            placeholder="Ej. Planificación, Diseño, Implementación..."
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
                            placeholder="Describe los objetivos o entregables de esta fase..."
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Fecha inicio *</label>
                            <input
                                type="date"
                                value={form.fecha_inicio}
                                onChange={e => { setForm({ ...form, fecha_inicio: e.target.value }); setModalError('') }}
                                className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                            />
                        </div>
                        <div>
                            <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Fecha fin *</label>
                            <input
                                type="date"
                                value={form.fecha_fin}
                                onChange={e => { setForm({ ...form, fecha_fin: e.target.value }); setModalError('') }}
                                className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                            />
                        </div>
                    </div>
                </div>
                <div className="px-6 py-4 border-t border-[#e1e3e4] flex gap-2">
                    <button onClick={() => setModalOpen(false)} disabled={guardando}
                        className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={guardarFase} disabled={!form.nombre.trim() || guardando}
                        className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        {guardando ? 'Guardando...' : editando ? 'Guardar cambios' : 'Crear fase'}
                    </button>
                </div>
            </Modal>

            {/* Modal Confirmar eliminar */}
            <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Eliminar fase">
                {confirmDelete?.error && <ErrorBanner message={confirmDelete.error} />}
                <div className="p-6">
                    <div className="w-12 h-12 rounded-full bg-[#ffdad6] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-6 h-6 text-[#ba1a1a]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                        </svg>
                    </div>
                    <p className="text-[14px] text-[#4c616c] text-center mb-1">
                        ¿Eliminar la fase <strong className="text-[#191c1d]">{confirmDelete?.nombre}</strong>?
                    </p>
                    <p className="text-[13px] text-[#9ba7ae] text-center">Esta acción no se puede deshacer.</p>
                </div>
                <div className="flex gap-2 px-6 py-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={() => setConfirmDelete(null)}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button onClick={() => eliminarFase(confirmDelete.id)}
                        className="flex-1 h-11 rounded-xl bg-[#ba1a1a] text-white font-semibold text-[13px] hover:bg-[#930014] transition-colors">
                        Eliminar
                    </button>
                </div>
            </Modal>
        </div>
    )
}