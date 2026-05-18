import { useState, useEffect } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { entregablesApi } from '../../services/entregablesApi'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconChevron() {
    return <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
}
function IconChevronDown({ open }) {
    return (
        <svg viewBox="0 0 16 16" fill="none" className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M3 6l5 5 5-5" />
        </svg>
    )
}
function IconDownload() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 4v9M6 9l4 4 4-4" /><path d="M3 16h14" /></svg>
}
function IconFile() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2h8l4 4v12a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" /><path d="M14 2v4h4" /></svg>
}
function IconCheck() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 10l4 4 8-8" /></svg>
}
function IconX() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 4l12 12M16 4L4 16" /></svg>
}

// ── Constantes ────────────────────────────────────────────────────────────────

const ESTADO_CONFIG = {
    borrador:  { label: 'Borrador',  color: 'bg-gray-100 text-gray-600',   dot: 'bg-gray-400' },
    enviado:   { label: 'Enviado',   color: 'bg-blue-100 text-blue-700',   dot: 'bg-blue-500' },
    aprobado:  { label: 'Aprobado',  color: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
    rechazado: { label: 'Rechazado', color: 'bg-red-100 text-red-700',     dot: 'bg-red-500' },
}

const TIPO_LABELS = {
    documento: 'Documento',
    prototipo: 'Prototipo',
    codigo: 'Código',
    presentacion: 'Presentación',
    otro: 'Otro',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatBytes(bytes) {
    if (!bytes) return '—'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function esImagen(mime) { return mime?.startsWith('image/') }

// ── Sub-componentes ───────────────────────────────────────────────────────────

function Badge({ estado }) {
    const cfg = ESTADO_CONFIG[estado] || ESTADO_CONFIG.borrador
    return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold ${cfg.color}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
        </span>
    )
}

function ErrorBanner({ message }) {
    if (!message) return null
    return <div className="px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">{message}</div>
}

function SuccessBanner({ message }) {
    if (!message) return null
    return <div className="px-3 py-2.5 bg-green-50 border border-green-200 rounded-xl text-[13px] text-green-700 font-medium">{message}</div>
}

function Modal({ open, title, children }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
                <div className="px-6 py-4 border-b border-[#e1e3e4]">
                    <h3 className="text-[17px] font-bold text-[#191c1d]">{title}</h3>
                </div>
                {children}
            </div>
        </div>
    )
}

function ListaArchivos({ archivos }) {
    if (!archivos || archivos.length === 0) {
        return <p className="text-[13px] text-[#9ba7ae]">Sin archivos adjuntos</p>
    }
    return (
        <div className="space-y-2">
            {archivos.map(a => (
                <div key={a.id} className="flex items-center gap-3 bg-[#f8f9fa] border border-[#e1e3e4] rounded-lg px-3 py-2">
                    {esImagen(a.tipo_mime) ? (
                        <div className="w-10 h-10 rounded-lg overflow-hidden border border-[#e1e3e4] flex-shrink-0 bg-white">
                            <img src={a.url_descarga} alt={a.nombre_original} className="w-full h-full object-cover"
                                onError={e => { e.target.style.display = 'none' }} />
                        </div>
                    ) : (
                        <div className="w-8 h-8 rounded-lg bg-white border border-[#e1e3e4] flex items-center justify-center flex-shrink-0 text-[#9ba7ae]">
                            <IconFile />
                        </div>
                    )}
                    <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-semibold text-[#191c1d] truncate">{a.nombre_original}</p>
                        <p className="text-[11px] text-[#9ba7ae]">{formatBytes(a.tamaño_bytes)}</p>
                    </div>
                    <a href={a.url_descarga} download={a.nombre_original} target="_blank" rel="noreferrer"
                        className="p-1.5 rounded-lg hover:bg-white text-[#4c616c] hover:text-[#191c1d] transition-colors flex-shrink-0"
                        title="Descargar">
                        <IconDownload />
                    </a>
                </div>
            ))}
        </div>
    )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function PanelRevisionEntregables() {
    const { proyectoId, faseId, actividadId } = useParams()
    const location = useLocation()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre
    const faseNombre = location.state?.faseNombre
    const actividadNombre = location.state?.actividadNombre ?? 'Actividad'

    const [entregables, setEntregables] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    const [archivos, setArchivos] = useState({})
    const [expandidos, setExpandidos] = useState({})
    const [feedback, setFeedback] = useState({})
    const [validando, setValidando] = useState({})
    const [erroresValidacion, setErroresValidacion] = useState({})
    const [exitos, setExitos] = useState({})
    const [confirmModal, setConfirmModal] = useState(null)
    const [filtroEstado, setFiltroEstado] = useState('enviado')

    useEffect(() => { cargar() }, [actividadId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const data = await entregablesApi.listar(actividadId)
            setEntregables(data)
        } catch (err) {
            setError(err.data?.detail || 'Error cargando entregables.')
        } finally {
            setLoading(false)
        }
    }

    async function cargarArchivos(entregableId) {
        if (archivos[entregableId]) return
        try {
            const data = await entregablesApi.listarArchivos(entregableId)
            setArchivos(p => ({ ...p, [entregableId]: data }))
        } catch { }
    }

    function toggleExpand(entregable) {
        const nuevoEstado = !expandidos[entregable.id]
        setExpandidos(p => ({ ...p, [entregable.id]: nuevoEstado }))
        if (nuevoEstado) cargarArchivos(entregable.id)
    }

    async function ejecutarValidacion() {
        if (!confirmModal) return
        const { entregable, accion } = confirmModal
        const retroalimentacion = feedback[entregable.id] || ''

        setValidando(p => ({ ...p, [entregable.id]: true }))
        setErroresValidacion(p => ({ ...p, [entregable.id]: '' }))

        try {
            const actualizado = await entregablesApi.validar(entregable.id, accion, retroalimentacion)
            setEntregables(p => p.map(e => e.id === actualizado.id ? actualizado : e))
            setExitos(p => ({ ...p, [entregable.id]: accion === 'aprobar' ? 'Entregable aprobado exitosamente.' : 'Entregable rechazado.' }))
            setConfirmModal(null)
            setTimeout(() => setExitos(p => ({ ...p, [entregable.id]: '' })), 4000)
        } catch (err) {
            setErroresValidacion(p => ({ ...p, [entregable.id]: err.data?.detail || 'Error al validar el entregable.' }))
            setConfirmModal(null)
        } finally {
            setValidando(p => ({ ...p, [entregable.id]: false }))
        }
    }

    const entregablesFiltrados = filtroEstado
        ? entregables.filter(e => e.estado === filtroEstado)
        : entregables

    const contadores = {
        todos: entregables.length,
        enviado: entregables.filter(e => e.estado === 'enviado').length,
        aprobado: entregables.filter(e => e.estado === 'aprobado').length,
        rechazado: entregables.filter(e => e.estado === 'rechazado').length,
        borrador: entregables.filter(e => e.estado === 'borrador').length,
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
                        <Link to={`/docente/proyectos/${proyectoId}/fases`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                            {proyectoNombre}
                        </Link>
                    </>
                )}
                {faseNombre && (
                    <>
                        <IconChevron />
                        <Link to={`/docente/proyectos/${proyectoId}/fases/${faseId}/actividades`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                            {faseNombre}
                        </Link>
                    </>
                )}
                <IconChevron />
                <span className="text-[#191c1d] font-semibold">{actividadNombre} — Entregables</span>
            </div>

            {/* Header */}
            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Panel de revisión</h1>
                <p className="text-[13px] text-[#9ba7ae]">
                    Actividad: <span className="font-semibold text-[#4c616c]">{actividadNombre}</span>
                </p>
            </div>

            {/* Estadísticas rápidas */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                {[
                    { key: 'enviado', label: 'Pendientes', color: 'text-blue-700 bg-blue-50 border-blue-200' },
                    { key: 'aprobado', label: 'Aprobados', color: 'text-green-700 bg-green-50 border-green-200' },
                    { key: 'rechazado', label: 'Rechazados', color: 'text-red-700 bg-red-50 border-red-200' },
                    { key: 'borrador', label: 'Borradores', color: 'text-gray-600 bg-gray-50 border-gray-200' },
                ].map(({ key, label, color }) => (
                    <button
                        key={key}
                        onClick={() => setFiltroEstado(filtroEstado === key ? '' : key)}
                        className={`border rounded-xl p-3 text-left transition-all ${color} ${filtroEstado === key ? 'ring-2 ring-offset-1 ring-current' : 'opacity-80 hover:opacity-100'}`}
                    >
                        <p className="text-[24px] font-extrabold leading-none mb-1">{contadores[key]}</p>
                        <p className="text-[12px] font-semibold">{label}</p>
                    </button>
                ))}
            </div>

            {error && <ErrorBanner message={error} />}

            {/* Filtro activo */}
            <div className="flex items-center gap-2 mb-4">
                {filtroEstado ? (
                    <button
                        onClick={() => setFiltroEstado('')}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-[#f0f2f3] text-[#4c616c] rounded-lg text-[12px] font-semibold hover:bg-[#e1e3e4] transition-colors"
                    >
                        Filtro: {ESTADO_CONFIG[filtroEstado]?.label}
                        <IconX />
                    </button>
                ) : (
                    <span className="text-[13px] text-[#9ba7ae]">Mostrando todos ({contadores.todos})</span>
                )}
            </div>

            {loading ? (
                <div className="text-center py-16 text-[#9ba7ae] text-[14px]">Cargando entregables...</div>
            ) : entregablesFiltrados.length === 0 ? (
                <div className="text-center py-16 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-12 h-12 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3 text-[#9ba7ae]">
                        <IconFile />
                    </div>
                    <p className="text-[14px] font-semibold text-[#4c616c] mb-1">
                        {entregables.length === 0 ? 'Sin entregables' : 'Sin resultados'}
                    </p>
                    <p className="text-[13px] text-[#9ba7ae]">
                        {entregables.length === 0
                            ? 'Aún no hay entregables para esta actividad.'
                            : 'Ningún entregable coincide con el filtro aplicado.'}
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {entregablesFiltrados.map(e => {
                        const abierto = !!expandidos[e.id]
                        const archivosE = archivos[e.id] || []
                        const esValidable = e.estado === 'enviado'

                        return (
                            <div key={e.id} className="bg-white border border-[#e1e3e4] rounded-xl overflow-hidden hover:shadow-sm transition-shadow">
                                <div
                                    className="flex items-start gap-3 p-4 cursor-pointer"
                                    onClick={() => toggleExpand(e)}
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap mb-1">
                                            <h3 className="text-[15px] font-bold text-[#191c1d]">{e.titulo}</h3>
                                            <Badge estado={e.estado} />
                                            <span className="text-[11px] text-[#9ba7ae] bg-[#f0f2f3] px-2 py-0.5 rounded-md">
                                                {TIPO_LABELS[e.tipo] || e.tipo}
                                            </span>
                                            {e.numero_version > 1 && (
                                                <span className="text-[11px] text-[#4c616c] bg-[#f0f2f3] px-2 py-0.5 rounded-md">
                                                    v{e.numero_version}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-[11px] text-[#9ba7ae]">
                                            {e.fecha_envio
                                                ? `Enviado ${formatFecha(e.fecha_envio)}`
                                                : `Creado ${formatFecha(e.fecha_creacion)}`}
                                        </p>
                                    </div>
                                    <div className="flex-shrink-0 mt-0.5">
                                        <IconChevronDown open={abierto} />
                                    </div>
                                </div>

                                {abierto && (
                                    <div className="border-t border-[#f0f2f3] p-4 space-y-4">
                                        {e.descripcion && (
                                            <div>
                                                <p className="text-[11px] font-semibold text-[#9ba7ae] mb-1">Descripción</p>
                                                <p className="text-[13px] text-[#4c616c]">{e.descripcion}</p>
                                            </div>
                                        )}

                                        <div>
                                            <p className="text-[11px] font-semibold text-[#9ba7ae] mb-2">Archivos adjuntos</p>
                                            <ListaArchivos archivos={archivosE} />
                                        </div>

                                        {e.retroalimentacion && (
                                            <div className={`rounded-xl p-3 ${e.estado === 'aprobado' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                                <p className={`text-[11px] font-semibold mb-1 ${e.estado === 'aprobado' ? 'text-green-600' : 'text-red-600'}`}>
                                                    Retroalimentación enviada
                                                </p>
                                                <p className="text-[13px] text-[#4c616c]">{e.retroalimentacion}</p>
                                                {e.fecha_validacion && (
                                                    <p className="text-[11px] text-[#9ba7ae] mt-1">{formatFecha(e.fecha_validacion)}</p>
                                                )}
                                            </div>
                                        )}

                                        {erroresValidacion[e.id] && <ErrorBanner message={erroresValidacion[e.id]} />}
                                        {exitos[e.id] && <SuccessBanner message={exitos[e.id]} />}

                                        {esValidable && (
                                            <div className="bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl p-4 space-y-3">
                                                <p className="text-[13px] font-bold text-[#191c1d]">Escribir retroalimentación</p>
                                                <textarea
                                                    value={feedback[e.id] || ''}
                                                    onChange={ev => setFeedback(p => ({ ...p, [e.id]: ev.target.value }))}
                                                    rows={3}
                                                    placeholder="Escribe tus comentarios para el estudiante... (opcional)"
                                                    className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f] bg-white"
                                                />
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => setConfirmModal({ entregable: e, accion: 'aprobar' })}
                                                        disabled={!!validando[e.id]}
                                                        className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors text-[13px] font-semibold disabled:opacity-50"
                                                    >
                                                        <IconCheck />Aprobar
                                                    </button>
                                                    <button
                                                        onClick={() => setConfirmModal({ entregable: e, accion: 'rechazar' })}
                                                        disabled={!!validando[e.id]}
                                                        className="flex items-center gap-2 px-4 py-2.5 bg-[#ba1a1a] text-white rounded-xl hover:bg-[#930014] transition-colors text-[13px] font-semibold disabled:opacity-50"
                                                    >
                                                        <IconX />Rechazar
                                                    </button>
                                                </div>
                                            </div>
                                        )}

                                        {!esValidable && e.fecha_validacion && (
                                            <div className="text-[12px] text-[#9ba7ae]">
                                                Validado el {formatFecha(e.fecha_validacion)}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Modal confirmación */}
            <Modal
                open={!!confirmModal}
                title={confirmModal?.accion === 'aprobar' ? 'Confirmar aprobación' : 'Confirmar rechazo'}
            >
                <div className="p-6">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 ${confirmModal?.accion === 'aprobar' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-[#ba1a1a]'}`}>
                        {confirmModal?.accion === 'aprobar' ? <IconCheck /> : <IconX />}
                    </div>
                    <p className="text-[14px] text-[#4c616c] text-center mb-1">
                        ¿{confirmModal?.accion === 'aprobar' ? 'Aprobar' : 'Rechazar'} el entregable{' '}
                        <strong className="text-[#191c1d]">{confirmModal?.entregable?.titulo}</strong>?
                    </p>
                    {feedback[confirmModal?.entregable?.id] ? (
                        <div className="mt-3 bg-[#f0f2f3] rounded-lg px-3 py-2">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] mb-0.5">Retroalimentación:</p>
                            <p className="text-[13px] text-[#4c616c]">{feedback[confirmModal?.entregable?.id]}</p>
                        </div>
                    ) : (
                        <p className="text-[13px] text-[#9ba7ae] text-center mt-1">
                            No escribiste retroalimentación. El estudiante será notificado igualmente.
                        </p>
                    )}
                </div>
                <div className="flex gap-2 px-6 py-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={() => setConfirmModal(null)}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button
                        onClick={ejecutarValidacion}
                        className={`flex-1 h-11 rounded-xl text-white font-semibold text-[13px] transition-colors ${confirmModal?.accion === 'aprobar' ? 'bg-green-600 hover:bg-green-700' : 'bg-[#ba1a1a] hover:bg-[#930014]'}`}
                    >
                        Confirmar
                    </button>
                </div>
            </Modal>
        </div>
    )
}
