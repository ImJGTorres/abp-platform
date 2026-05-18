import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { entregablesApi } from '../../services/entregablesApi'
import { buildMediaUrl } from '../../services/api'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconPlus() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 4v12M4 10h12" /></svg>
}
function IconUpload() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13V4M6 7l4-4 4 4" /><path d="M3 15v1a1 1 0 001 1h12a1 1 0 001-1v-1" /></svg>
}
function IconTrash() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 5h14M8 5V3h4v2M6 5v11a1 1 0 001 1h6a1 1 0 001-1V5" /></svg>
}
function IconDownload() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 4v9M6 9l4 4 4-4" /><path d="M3 16h14" /></svg>
}
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
function IconHistory() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M2 10a8 8 0 1016 0A8 8 0 002 10zM10 6v4l2.5 2.5" /></svg>
}
function IconFile() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2h8l4 4v12a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" /><path d="M14 2v4h4" /></svg>
}
function IconSend() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10l15-8-8 15v-7L3 10z" /></svg>
}
function IconEdit() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2l4 4-10 10H4v-4L14 2z" /></svg>
}
function IconRefresh() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M16.5 9A6.5 6.5 0 105 15.2" /><path d="M3 18v-5h5" /></svg>
}

// ── Constantes ────────────────────────────────────────────────────────────────

const ESTADO_CONFIG = {
    borrador:  { label: 'Borrador',  color: 'bg-gray-100 text-gray-600' },
    enviado:   { label: 'Enviado',   color: 'bg-blue-100 text-blue-700' },
    aprobado:  { label: 'Aprobado',  color: 'bg-green-100 text-green-700' },
    rechazado: { label: 'Rechazado', color: 'bg-red-100 text-red-700' },
}

const TIPO_LABELS = {
    documento: 'Documento',
    prototipo: 'Prototipo',
    codigo: 'Código',
    presentacion: 'Presentación',
    otro: 'Otro',
}

// 10 MB en bytes
const MAX_SIZE = 10 * 1024 * 1024
const TIPOS_PERMITIDOS = ['pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg']
const MIME_PERMITIDOS = {
    pdf: 'application/pdf',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
}

// ── Componentes auxiliares ────────────────────────────────────────────────────

function Badge({ estado }) {
    const cfg = ESTADO_CONFIG[estado] || ESTADO_CONFIG.borrador
    return <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${cfg.color}`}>{cfg.label}</span>
}

function ErrorBanner({ message }) {
    if (!message) return null
    return <div className="px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">{message}</div>
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

function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function esImagen(mime) {
    return mime?.startsWith('image/')
}

// ── Componente de Zona Drag & Drop ────────────────────────────────────────────

function ZonaArchivos({ archivos, subiendo, onArchivosNuevos, onEliminar, entregableId, puedeModificar }) {
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef(null)

    const validarArchivo = (file) => {
        const ext = file.name.rsplit ? file.name.rsplit('.', 1)[-1] : file.name.split('.').pop()?.toLowerCase()
        const extLower = file.name.split('.').pop()?.toLowerCase()
        if (!TIPOS_PERMITIDOS.includes(extLower)) {
            return `Tipo no permitido (.${extLower}). Formatos aceptados: ${TIPOS_PERMITIDOS.join(', ')}`
        }
        if (file.size > MAX_SIZE) {
            return `El archivo excede el tamaño máximo de 10 MB (${formatBytes(file.size)})`
        }
        return null
    }

    const procesarArchivos = (files) => {
        const validos = []
        const errores = []
        Array.from(files).forEach(f => {
            const err = validarArchivo(f)
            if (err) errores.push({ nombre: f.name, error: err })
            else validos.push(f)
        })
        onArchivosNuevos(validos, errores)
    }

    const onDrop = (e) => {
        e.preventDefault()
        setDragging(false)
        if (!puedeModificar) return
        procesarArchivos(e.dataTransfer.files)
    }

    const onDragOver = (e) => { e.preventDefault(); if (puedeModificar) setDragging(true) }
    const onDragLeave = () => setDragging(false)

    return (
        <div className="space-y-3">
            {puedeModificar && (
                <div
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                    onDragLeave={onDragLeave}
                    onClick={() => inputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${dragging ? 'border-[#d32f2f] bg-[#fff1f0]' : 'border-[#e1e3e4] hover:border-[#d32f2f] hover:bg-[#fafafa]'}`}
                >
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2 ${dragging ? 'bg-[#ffdad6] text-[#d32f2f]' : 'bg-[#f0f2f3] text-[#9ba7ae]'}`}>
                        <IconUpload />
                    </div>
                    <p className="text-[13px] font-semibold text-[#4c616c]">
                        Arrastra archivos aquí <span className="text-[#9ba7ae] font-normal">o</span>
                    </p>
                    <p className="text-[12px] text-[#d32f2f] font-semibold mt-0.5">Haz clic para seleccionar</p>
                    <p className="text-[11px] text-[#9ba7ae] mt-1.5">PDF, DOCX, XLSX, PNG, JPG · Máx. 10 MB por archivo</p>
                    <input
                        ref={inputRef}
                        type="file"
                        multiple
                        className="hidden"
                        accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg"
                        onChange={e => { procesarArchivos(e.target.files); e.target.value = '' }}
                    />
                </div>
            )}

            {/* Archivos subiendo */}
            {subiendo.map((s, i) => (
                <div key={i} className="bg-white border border-[#e1e3e4] rounded-xl p-3">
                    <div className="flex items-center gap-2.5 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-[#f0f2f3] flex items-center justify-center flex-shrink-0">
                            <IconFile />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-[13px] font-semibold text-[#191c1d] truncate">{s.nombre}</p>
                            <p className="text-[11px] text-[#9ba7ae]">{s.error ? s.error : `${s.progreso}%`}</p>
                        </div>
                    </div>
                    {!s.error && (
                        <div className="h-1.5 bg-[#f0f2f3] rounded-full overflow-hidden">
                            <div
                                className="h-full bg-[#d32f2f] rounded-full transition-all duration-200"
                                style={{ width: `${s.progreso}%` }}
                            />
                        </div>
                    )}
                    {s.error && (
                        <p className="text-[11px] text-[#ba1a1a] mt-1">{s.error}</p>
                    )}
                </div>
            ))}

            {/* Archivos subidos */}
            {archivos.map(a => (
                <div key={a.id} className="bg-white border border-[#e1e3e4] rounded-xl p-3 flex items-center gap-3">
                    {esImagen(a.tipo_mime) ? (
                        <div className="w-12 h-12 rounded-lg overflow-hidden border border-[#e1e3e4] flex-shrink-0 bg-[#f0f2f3]">
                            <img
                                src={a.url_descarga}
                                alt={a.nombre_original}
                                className="w-full h-full object-cover"
                                onError={e => { e.target.style.display = 'none' }}
                            />
                        </div>
                    ) : (
                        <div className="w-10 h-10 rounded-lg bg-[#f0f2f3] flex items-center justify-center flex-shrink-0">
                            <IconFile />
                        </div>
                    )}
                    <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-semibold text-[#191c1d] truncate">{a.nombre_original}</p>
                        <p className="text-[11px] text-[#9ba7ae]">{formatBytes(a.tamaño_bytes)} · versión {a.version}</p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                        <a
                            href={a.url_descarga}
                            download={a.nombre_original}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 rounded-lg hover:bg-[#f0f2f3] text-[#4c616c] hover:text-[#191c1d] transition-colors"
                            title="Descargar"
                        >
                            <IconDownload />
                        </a>
                        {puedeModificar && (
                            <button
                                onClick={() => onEliminar(a.id)}
                                className="p-2 rounded-lg hover:bg-[#fff1f0] text-[#ba1a1a] transition-colors"
                                title="Eliminar"
                            >
                                <IconTrash />
                            </button>
                        )}
                    </div>
                </div>
            ))}

            {archivos.length === 0 && subiendo.length === 0 && !puedeModificar && (
                <p className="text-[13px] text-[#9ba7ae] text-center py-4">Sin archivos adjuntos</p>
            )}
        </div>
    )
}

// ── Historial de versiones ────────────────────────────────────────────────────

function HistorialVersiones({ entregableId, estadoActual }) {
    const [versiones, setVersiones] = useState([])
    const [cargando, setCargando] = useState(false)
    const [abierto, setAbierto] = useState(false)
    const [expandidos, setExpandidos] = useState({})

    useEffect(() => {
        if (abierto && versiones.length === 0) cargar()
    }, [abierto])

    async function cargar() {
        setCargando(true)
        try {
            const data = await entregablesApi.obtenerVersiones(entregableId)
            setVersiones(data)
        } catch { }
        finally { setCargando(false) }
    }

    function toggleVersion(num) {
        setExpandidos(p => ({ ...p, [num]: !p[num] }))
    }

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-xl overflow-hidden">
            <button
                onClick={() => setAbierto(o => !o)}
                className="w-full flex items-center gap-2.5 px-4 py-3 hover:bg-[#f0f2f3] transition-colors"
            >
                <IconHistory />
                <span className="text-[13px] font-semibold text-[#191c1d] flex-1 text-left">Historial de versiones</span>
                <IconChevronDown open={abierto} />
            </button>

            {abierto && (
                <div className="border-t border-[#e1e3e4]">
                    {cargando ? (
                        <p className="text-center py-6 text-[13px] text-[#9ba7ae]">Cargando historial...</p>
                    ) : versiones.length === 0 ? (
                        <p className="text-center py-6 text-[13px] text-[#9ba7ae]">Sin historial de versiones</p>
                    ) : (
                        <div className="divide-y divide-[#f0f2f3]">
                            {versiones.map((v, idx) => {
                                const esActual = idx === versiones.length - 1
                                return (
                                    <div key={v.numero_version} className={`${esActual ? 'bg-[#fafafa]' : ''}`}>
                                        <button
                                            onClick={() => toggleVersion(v.numero_version)}
                                            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#f0f2f3] transition-colors"
                                        >
                                            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${esActual ? 'bg-[#d32f2f] text-white' : 'bg-[#f0f2f3] text-[#4c616c]'}`}>
                                                {v.numero_version}
                                            </div>
                                            <div className="flex-1 text-left">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[13px] font-semibold text-[#191c1d]">
                                                        Versión {v.numero_version}
                                                    </span>
                                                    {esActual && (
                                                        <span className="px-1.5 py-0.5 bg-[#d32f2f] text-white text-[10px] font-bold rounded-full">Actual</span>
                                                    )}
                                                    <Badge estado={v.estado} />
                                                </div>
                                                <p className="text-[11px] text-[#9ba7ae] mt-0.5">{formatFecha(v.fecha_creacion)}</p>
                                            </div>
                                            <IconChevronDown open={expandidos[v.numero_version]} />
                                        </button>

                                        {expandidos[v.numero_version] && (
                                            <div className="px-4 pb-4 space-y-2">
                                                {v.motivo_revision && (
                                                    <div className="bg-[#f0f2f3] rounded-lg px-3 py-2">
                                                        <p className="text-[11px] font-semibold text-[#9ba7ae] mb-0.5">Motivo de revisión</p>
                                                        <p className="text-[13px] text-[#4c616c]">{v.motivo_revision}</p>
                                                    </div>
                                                )}
                                                {v.retroalimentacion && (
                                                    <div className="bg-[#f0f2f3] rounded-lg px-3 py-2">
                                                        <p className="text-[11px] font-semibold text-[#9ba7ae] mb-0.5">Retroalimentación del docente</p>
                                                        <p className="text-[13px] text-[#4c616c]">{v.retroalimentacion}</p>
                                                    </div>
                                                )}
                                                {v.archivos?.length > 0 && (
                                                    <div className="space-y-1.5">
                                                        <p className="text-[11px] font-semibold text-[#9ba7ae]">Archivos adjuntos</p>
                                                        {v.archivos.map(a => (
                                                            <div key={a.id} className="flex items-center gap-2.5 bg-white border border-[#e1e3e4] rounded-lg px-3 py-2">
                                                                <IconFile />
                                                                <span className="flex-1 text-[12px] text-[#4c616c] truncate">{a.nombre_original}</span>
                                                                <a href={a.url_descarga} download={a.nombre_original} target="_blank" rel="noreferrer"
                                                                    className="text-[#4c616c] hover:text-[#191c1d] transition-colors">
                                                                    <IconDownload />
                                                                </a>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function EntregablesActividad() {
    const { actividadId } = useParams()
    const location = useLocation()
    const actividadNombre = location.state?.actividadNombre ?? 'Actividad'

    const [entregables, setEntregables] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    // Modal crear
    const [modalOpen, setModalOpen] = useState(false)
    const [form, setForm] = useState({ titulo: '', descripcion: '', tipo: 'documento' })
    const [guardando, setGuardando] = useState(false)
    const [modalError, setModalError] = useState('')

    // Entregable activo (expandido)
    const [activoId, setActivoId] = useState(null)

    // Archivos
    const [archivos, setArchivos] = useState({})
    const [subiendoMap, setSubiendoMap] = useState({})
    const [erroresArchivo, setErroresArchivo] = useState({})

    // Confirmación enviar
    const [confirmEnviar, setConfirmEnviar] = useState(null)
    const [enviando, setEnviando] = useState(false)

    // Confirmación nueva versión
    const [confirmNuevaVersion, setConfirmNuevaVersion] = useState(null)
    const [creandoVersion, setCreandoVersion] = useState(false)

    useEffect(() => { cargar() }, [actividadId])

    async function cargar() {
        setLoading(true)
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
        try {
            const data = await entregablesApi.listarArchivos(entregableId)
            setArchivos(p => ({ ...p, [entregableId]: data }))
        } catch { }
    }

    function abrirDetalle(entregable) {
        const nuevoActivo = activoId === entregable.id ? null : entregable.id
        setActivoId(nuevoActivo)
        if (nuevoActivo && !archivos[nuevoActivo]) {
            cargarArchivos(nuevoActivo)
        }
    }

    async function crearEntregable() {
        setModalError('')
        if (!form.titulo.trim()) { setModalError('El título es obligatorio.'); return }
        setGuardando(true)
        try {
            const nuevo = await entregablesApi.crear(actividadId, {
                titulo: form.titulo.trim(),
                descripcion: form.descripcion.trim(),
                tipo: form.tipo,
            })
            setEntregables(p => [nuevo, ...p])
            setModalOpen(false)
            setForm({ titulo: '', descripcion: '', tipo: 'documento' })
        } catch (err) {
            setModalError(err.data?.detail || err.data?.titulo?.[0] || 'Error al crear el entregable.')
        } finally {
            setGuardando(false)
        }
    }

    async function manejarArchivosNuevos(entregableId, archivosValidos, errores) {
        if (errores.length > 0) {
            setErroresArchivo(p => ({ ...p, [entregableId]: errores.map(e => `${e.nombre}: ${e.error}`).join(' · ') }))
        } else {
            setErroresArchivo(p => ({ ...p, [entregableId]: '' }))
        }

        for (const archivo of archivosValidos) {
            const key = `${entregableId}-${archivo.name}-${Date.now()}`
            setSubiendoMap(p => ({
                ...p,
                [entregableId]: [...(p[entregableId] || []), { key, nombre: archivo.name, progreso: 0 }],
            }))

            try {
                const adjunto = await entregablesApi.subirArchivo(
                    entregableId,
                    archivo,
                    (pct) => {
                        setSubiendoMap(p => ({
                            ...p,
                            [entregableId]: (p[entregableId] || []).map(s => s.key === key ? { ...s, progreso: pct } : s),
                        }))
                    }
                )
                setArchivos(p => ({ ...p, [entregableId]: [...(p[entregableId] || []), adjunto] }))
            } catch (err) {
                const msg = err.data?.archivo?.[0] || err.data?.detail || 'Error al subir el archivo.'
                setSubiendoMap(p => ({
                    ...p,
                    [entregableId]: (p[entregableId] || []).map(s => s.key === key ? { ...s, error: msg } : s),
                }))
            } finally {
                setTimeout(() => {
                    setSubiendoMap(p => ({
                        ...p,
                        [entregableId]: (p[entregableId] || []).filter(s => s.key !== key),
                    }))
                }, 2000)
            }
        }
    }

    async function eliminarArchivo(entregableId, archivoId) {
        try {
            await entregablesApi.eliminarArchivo(archivoId)
            setArchivos(p => ({ ...p, [entregableId]: (p[entregableId] || []).filter(a => a.id !== archivoId) }))
        } catch (err) {
            setErroresArchivo(p => ({ ...p, [entregableId]: err.data?.error || 'Error al eliminar el archivo.' }))
        }
    }

    async function enviarEntregable() {
        if (!confirmEnviar) return
        setEnviando(true)
        try {
            const actualizado = await entregablesApi.enviar(confirmEnviar.id)
            setEntregables(p => p.map(e => e.id === actualizado.id ? actualizado : e))
            setConfirmEnviar(null)
        } catch (err) {
            setConfirmEnviar(p => ({ ...p, error: err.data?.detail || err.data?.non_field_errors?.[0] || 'Error al enviar.' }))
        } finally {
            setEnviando(false)
        }
    }

    async function crearNuevaVersion() {
        if (!confirmNuevaVersion) return
        setCreandoVersion(true)
        try {
            const nuevo = await entregablesApi.crearNuevaVersion(confirmNuevaVersion.id)
            setEntregables(p => [nuevo, ...p])
            setConfirmNuevaVersion(null)
        } catch (err) {
            setConfirmNuevaVersion(p => ({ ...p, error: err.data?.detail || 'Error al crear nueva versión.' }))
        } finally {
            setCreandoVersion(false)
        }
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-5 flex items-center gap-2 text-[13px] flex-wrap">
                <Link to="/estudiante" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Inicio</Link>
                <IconChevron />
                <span className="text-[#191c1d] font-semibold">{actividadNombre}</span>
                <IconChevron />
                <span className="text-[#191c1d] font-semibold">Entregables</span>
            </div>

            {/* Header */}
            <div className="flex items-start justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Mis entregables</h1>
                    <p className="text-[13px] text-[#9ba7ae]">Actividad: <span className="font-semibold text-[#4c616c]">{actividadNombre}</span></p>
                </div>
                <button
                    onClick={() => { setModalError(''); setForm({ titulo: '', descripcion: '', tipo: 'documento' }); setModalOpen(true) }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold shadow-sm flex-shrink-0"
                >
                    <IconPlus />Nuevo entregable
                </button>
            </div>

            {error && <ErrorBanner message={error} />}

            {loading ? (
                <div className="text-center py-16 text-[#9ba7ae] text-[14px]">Cargando entregables...</div>
            ) : entregables.length === 0 ? (
                <div className="text-center py-16 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-12 h-12 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3 text-[#9ba7ae]">
                        <IconFile />
                    </div>
                    <p className="text-[14px] font-semibold text-[#4c616c] mb-1">Sin entregables</p>
                    <p className="text-[13px] text-[#9ba7ae]">Crea el primer entregable para esta actividad.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {entregables.map(e => {
                        const abierto = activoId === e.id
                        const puedeModificar = e.estado === 'borrador'
                        const archivosEntregable = archivos[e.id] || []
                        const subiendoEntregable = subiendoMap[e.id] || []
                        const errorArchivo = erroresArchivo[e.id] || ''

                        return (
                            <div key={e.id} className="bg-white border border-[#e1e3e4] rounded-xl overflow-hidden">
                                {/* Cabecera */}
                                <div
                                    className="flex items-start gap-3 p-4 cursor-pointer hover:bg-[#fafafa] transition-colors"
                                    onClick={() => abrirDetalle(e)}
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                            <h3 className="text-[15px] font-bold text-[#191c1d]">{e.titulo}</h3>
                                            <Badge estado={e.estado} />
                                            <span className="text-[11px] text-[#9ba7ae] bg-[#f0f2f3] px-2 py-0.5 rounded-md">
                                                {TIPO_LABELS[e.tipo] || e.tipo}
                                            </span>
                                            {e.numero_version > 1 && (
                                                <span className="text-[11px] text-[#4c616c] bg-[#f0f2f3] px-2 py-0.5 rounded-md">
                                                    versión {e.numero_version}
                                                </span>
                                            )}
                                        </div>
                                        {e.descripcion && (
                                            <p className="text-[13px] text-[#4c616c] truncate">{e.descripcion}</p>
                                        )}
                                        <p className="text-[11px] text-[#9ba7ae] mt-1">
                                            Creado {formatFecha(e.fecha_creacion)}
                                            {e.fecha_envio && ` · Enviado ${formatFecha(e.fecha_envio)}`}
                                        </p>
                                    </div>
                                    <div className="flex-shrink-0 mt-0.5">
                                        <IconChevronDown open={abierto} />
                                    </div>
                                </div>

                                {/* Detalle expandido */}
                                {abierto && (
                                    <div className="border-t border-[#f0f2f3] p-4 space-y-4">
                                        {e.descripcion && (
                                            <div>
                                                <p className="text-[11px] font-semibold text-[#9ba7ae] mb-1">Descripción</p>
                                                <p className="text-[13px] text-[#4c616c]">{e.descripcion}</p>
                                            </div>
                                        )}

                                        {/* Retroalimentación del docente */}
                                        {e.retroalimentacion && (
                                            <div className={`rounded-xl p-3 ${e.estado === 'aprobado' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                                <p className={`text-[11px] font-semibold mb-1 ${e.estado === 'aprobado' ? 'text-green-600' : 'text-red-600'}`}>
                                                    Retroalimentación del docente
                                                </p>
                                                <p className="text-[13px] text-[#4c616c]">{e.retroalimentacion}</p>
                                            </div>
                                        )}

                                        {/* Archivos */}
                                        <div>
                                            <p className="text-[11px] font-semibold text-[#9ba7ae] mb-2">Archivos adjuntos</p>
                                            {errorArchivo && <ErrorBanner message={errorArchivo} />}
                                            <ZonaArchivos
                                                archivos={archivosEntregable}
                                                subiendo={subiendoEntregable}
                                                entregableId={e.id}
                                                puedeModificar={puedeModificar}
                                                onArchivosNuevos={(validos, errores) => manejarArchivosNuevos(e.id, validos, errores)}
                                                onEliminar={(archivoId) => eliminarArchivo(e.id, archivoId)}
                                            />
                                        </div>

                                        {/* Historial */}
                                        <HistorialVersiones entregableId={e.id} estadoActual={e.estado} />

                                        {/* Acciones */}
                                        {puedeModificar && (
                                            <div className="flex gap-2 pt-1">
                                                <button
                                                    onClick={() => setConfirmEnviar(e)}
                                                    className="flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold"
                                                >
                                                    <IconSend />Enviar al docente
                                                </button>
                                                <button
                                                    onClick={() => {/* guardar como borrador — ya está guardado */}}
                                                    className="flex items-center gap-2 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold"
                                                >
                                                    Guardar borrador
                                                </button>
                                            </div>
                                        )}

                                        {e.estado === 'rechazado' && (
                                            <div className="pt-1">
                                                <button
                                                    onClick={() => setConfirmNuevaVersion(e)}
                                                    className="flex items-center gap-2 px-4 py-2.5 border-2 border-[#d32f2f] text-[#d32f2f] rounded-xl hover:bg-[#fff1f0] transition-colors text-[13px] font-semibold"
                                                >
                                                    <IconRefresh />Nueva versión
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Modal crear entregable */}
            <Modal open={modalOpen} title="Nuevo entregable">
                <div className="p-6 space-y-4">
                    {modalError && <ErrorBanner message={modalError} />}
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Título *</label>
                        <input
                            type="text"
                            value={form.titulo}
                            onChange={e => { setForm(p => ({ ...p, titulo: e.target.value })); setModalError('') }}
                            placeholder="Nombre del entregable..."
                            autoFocus
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Descripción</label>
                        <textarea
                            value={form.descripcion}
                            onChange={e => setForm(p => ({ ...p, descripcion: e.target.value }))}
                            rows={3}
                            placeholder="Describe este entregable..."
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        />
                    </div>
                    <div>
                        <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Tipo</label>
                        <select
                            value={form.tipo}
                            onChange={e => setForm(p => ({ ...p, tipo: e.target.value }))}
                            className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]"
                        >
                            {Object.entries(TIPO_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                    </div>
                </div>
                <div className="px-6 py-4 border-t border-[#e1e3e4] flex gap-2">
                    <button onClick={() => setModalOpen(false)} disabled={guardando}
                        className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={crearEntregable} disabled={!form.titulo.trim() || guardando}
                        className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        {guardando ? 'Creando...' : 'Crear entregable'}
                    </button>
                </div>
            </Modal>

            {/* Modal confirmar enviar */}
            <Modal open={!!confirmEnviar} title="Enviar entregable">
                {confirmEnviar?.error && <ErrorBanner message={confirmEnviar.error} />}
                <div className="p-6">
                    <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4 text-blue-600">
                        <IconSend />
                    </div>
                    <p className="text-[14px] text-[#4c616c] text-center mb-1">
                        ¿Enviar el entregable <strong className="text-[#191c1d]">{confirmEnviar?.titulo}</strong> al docente?
                    </p>
                    <p className="text-[13px] text-[#9ba7ae] text-center">
                        El docente podrá revisarlo, aprobarlo o rechazarlo. No podrás modificarlo después.
                    </p>
                </div>
                <div className="flex gap-2 px-6 py-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={() => setConfirmEnviar(null)} disabled={enviando}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-white transition-colors disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={enviarEntregable} disabled={enviando}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#ba1a1a] transition-colors disabled:opacity-50">
                        {enviando ? 'Enviando...' : 'Sí, enviar'}
                    </button>
                </div>
            </Modal>

            {/* Modal nueva versión */}
            <Modal open={!!confirmNuevaVersion} title="Nueva versión">
                {confirmNuevaVersion?.error && <ErrorBanner message={confirmNuevaVersion.error} />}
                <div className="p-6 space-y-4">
                    <p className="text-[14px] text-[#4c616c]">
                        Se creará una nueva versión del entregable <strong className="text-[#191c1d]">{confirmNuevaVersion?.titulo}</strong>.
                        Podrás subir nuevos archivos y enviarlo nuevamente.
                    </p>
                </div>
                <div className="flex gap-2 px-6 py-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={() => setConfirmNuevaVersion(null)} disabled={creandoVersion}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-white transition-colors disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={crearNuevaVersion} disabled={creandoVersion}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#ba1a1a] transition-colors disabled:opacity-50">
                        {creandoVersion ? 'Creando...' : 'Crear nueva versión'}
                    </button>
                </div>
            </Modal>
        </div>
    )
}
