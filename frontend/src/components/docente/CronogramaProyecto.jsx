import { useState, useEffect } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { proyectosApi } from '../../services/docenteApi'

function IconPlus() {
    return <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
}

function IconEdit() {
    return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M11 2l3 3-9 9H2v-3l9-9z" /></svg>
}

function IconTrash() {
    return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M2 4h12M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1M6 7v5M10 7v5M3 4l1 9a1 1 0 001 1h6a1 1 0 001-1l1-9" /></svg>
}

const ESTADOS = {
    pendiente: { label: 'Pendiente', bg: 'bg-[#f0f2f3]', text: 'text-[#5b403d]', dot: 'bg-[#9ba7ae]' },
    en_progreso: { label: 'En Progreso', bg: 'bg-[#fff3e0]', text: 'text-[#e65100]', dot: 'bg-[#f57c00]' },
    completado: { label: 'Completado', bg: 'bg-[#e8f5e9]', text: 'text-[#2e7d32]', dot: 'bg-[#2e7d32]' },
}

function ModalHito({ hito, raps, onGuardar, onCancelar, fechasProyecto }) {
    const esEdicion = !!hito
    const [form, setForm] = useState({
        nombre: hito?.nombre ?? '',
        descripcion: hito?.descripcion ?? '',
        fecha_limite: hito?.fecha_limite ?? '',
        rap_id: hito?.rap_id ?? '',
        estado: hito?.estado ?? 'pendiente',
    })
    const [errores, setErrores] = useState({})
    const [guardando, setGuardando] = useState(false)

    function validar() {
        const e = {}

        if (!form.nombre.trim()) {
            e.nombre = 'El nombre es obligatorio.'
        }

        if (!form.fecha_limite) {
            e.fecha_limite = 'Selecciona una fecha límite.'
        }

        if (form.fecha_limite && fechasProyecto) {
            const fechaHito = new Date(form.fecha_limite)
            const fechaInicio = new Date(fechasProyecto.inicio)
            const fechaFin = new Date(fechasProyecto.fin)

            if (fechaInicio > fechaFin) {
                e.fecha_limite = 'El proyecto tiene fechas inválidas (inicio mayor que fin).'
            } else if (fechaHito < fechaInicio) {
                e.fecha_limite = `Debe ser posterior al inicio (${formatFecha(fechasProyecto.inicio)})`
            } else if (fechaHito > fechaFin) {
                e.fecha_limite = `Debe ser anterior al fin (${formatFecha(fechasProyecto.fin)})`
            }
        }

        return e
    }

    async function handleGuardar() {
        const e = validar()
        if (Object.keys(e).length > 0) { setErrores(e); return }

        setGuardando(true)
        try {
            await onGuardar(form)
        } finally {
            setGuardando(false)
        }
    }

    function formatFecha(fecha) {
        const d = new Date(fecha)
        return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    }

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden" onClick={e => e.stopPropagation()}>

                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[19px] font-bold text-[#191c1d]">{esEdicion ? 'Editar Hito' : 'Nuevo Hito'}</h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Define un hito académico en la progresión temporal del proyecto</p>
                </div>

                <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto">

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Nombre del hito</label>
                        <input type="text" value={form.nombre}
                            onChange={e => { setForm(f => ({ ...f, nombre: e.target.value })); setErrores(e => ({ ...e, nombre: '' })) }}
                            placeholder="ej: Entrega de Borrador"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.nombre ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción (opcional)</label>
                        <textarea value={form.descripcion}
                            onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                            placeholder="ej: Primera entrega del análisis de requisitos..."
                            rows={3}
                            className="px-4 py-3 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all resize-none"
                        />
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Fecha límite</label>
                        <input type="date" value={form.fecha_limite}
                            onChange={e => { setForm(f => ({ ...f, fecha_limite: e.target.value })); setErrores(e => ({ ...e, fecha_limite: '' })) }}
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.fecha_limite ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.fecha_limite && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.fecha_limite}</p>}
                    </div>

                    {raps.length > 0 && (
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">RAP asociado (opcional)</label>
                            <select value={form.rap_id}
                                onChange={e => setForm(f => ({ ...f, rap_id: e.target.value }))}
                                className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all appearance-none bg-white">
                                <option value="">Sin RAP asociado</option>
                                {raps.map(r => (
                                    <option key={r.id} value={r.id}>{r.nombre} - {r.descripcion?.substring(0, 40)}{r.descripcion?.length > 40 ? '...' : ''}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    {esEdicion && (
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Estado</label>
                            <div className="flex gap-2">
                                {Object.entries(ESTADOS).map(([key, info]) => (
                                    <button key={key}
                                        onClick={() => setForm(f => ({ ...f, estado: key }))}
                                        className={`flex-1 h-10 rounded-xl text-[13px] font-semibold transition-all ${form.estado === key ? `${info.bg} ${info.text}` : 'bg-[#f0f2f3] text-[#9ba7ae] hover:bg-[#e8eaeb]'}`}>
                                        {info.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancelar}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button onClick={handleGuardar} disabled={guardando}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        {guardando
                            ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Guardando...</>
                            : esEdicion ? 'Guardar cambios' : 'Crear hito'}
                    </button>
                </div>
            </div>
        </div>
    )
}

function formatFecha(fecha) {
    if (!fecha) return '—'
    const d = new Date(fecha + 'T00:00:00')
    return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

function getMesNombre(mes) {
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    return meses[mes]
}

export default function CronogramaProyecto() {
    const { proyectoId } = useParams()
    const location = useLocation()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre
    const fechaInicio = location.state?.fecha_inicio
    const fechaFin = location.state?.fecha_fin

    const [hitos, setHitos] = useState([])
    const [raps, setRaps] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalHito, setModalHito] = useState(false)
    const [hitoEditando, setHitoEditando] = useState(null)
    const [eliminando, setEliminando] = useState(null)

    useEffect(() => { cargarDatos() }, [proyectoId])

    async function cargarDatos() {
        setLoading(true)
        try {
            const [hitosData, rapsData] = await Promise.all([
                proyectosApi.listarHitos(proyectoId),
                proyectosApi.listarRAPs(proyectoId),
            ])
            setHitos(hitosData.results ?? hitosData)
            setRaps(rapsData.results ?? rapsData)
        } catch (err) {
            console.error('Error cargando datos:', err)
            setHitos([])
            setRaps([])
        } finally {
            setLoading(false)
        }
    }

    async function handleGuardarHito(formData) {
        try {
            if (hitoEditando) {
                await proyectosApi.editarHito(proyectoId, hitoEditando.id, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    fecha_limite: formData.fecha_limite,
                    rap_id: formData.rap_id || null,
                    estado: formData.estado,
                    orden: hitoEditando.orden,
                })
            } else {
                await proyectosApi.crearHito(proyectoId, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    fecha_limite: formData.fecha_limite,
                    rap_id: formData.rap_id || null,
                    orden: hitos.length + 1,
                })
            }
            setModalHito(false)
            setHitoEditando(null)
            cargarDatos()
        } catch (err) {
            console.error('Error guardando hito:', err)
            throw err
        }
    }

    async function handleEliminar(id) {
        if (!window.confirm('¿Eliminar este hito? Esta acción no se puede deshacer.')) return
        setEliminando(id)
        try {
            await proyectosApi.eliminarHito(proyectoId, id)
            cargarDatos()
        } catch (err) {
            console.error('Error eliminando hito:', err)
            alert('No se pudo eliminar el hito.')
        } finally {
            setEliminando(null)
        }
    }

    const completados = hitos.filter(h => h.estado === 'completado').length
    const porcentaje = hitos.length > 0 ? Math.round((completados / hitos.length) * 100) : 0

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

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px] flex-wrap">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                {cursoId && (
                    <>
                        <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                        <Link to={`/docente/cursos/${cursoId}`} state={location.state} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                            {cursoNombre ?? 'Curso'}
                        </Link>
                    </>
                )}
                {proyectoNombre && (
                    <>
                        <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                        <span className="text-[#191c1d] font-medium">{proyectoNombre}</span>
                    </>
                )}
            </div>

            {/* Header */}
            <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <h1 className="text-[24px] font-bold text-[#191c1d] leading-tight mb-1">Cronograma del Proyecto</h1>
                    <p className="text-[13px] text-[#9ba7ae]">
                        Visualice y gestione la progresión temporal de sus hitos académicos y fases de investigación.
                    </p>
                </div>
                <button
                    onClick={() => setModalHito(true)}
                    className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm">
                    <IconPlus />
                    Nuevo Hito
                </button>
            </div>

            {/* Estado general */}
            <div className="mb-6 bg-white rounded-2xl border border-[#e1e3e4] p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-[15px] font-bold text-[#191c1d]">Estado General</h2>
                    <span className="text-[32px] font-bold text-[#d32f2f]">{porcentaje}%</span>
                </div>
                <div className="w-full h-3 bg-[#f0f2f3] rounded-full overflow-hidden mb-3">
                    <div className="h-full bg-[#d32f2f] transition-all duration-300 rounded-full"
                        style={{ width: `${porcentaje}%` }} />
                </div>
                <p className="text-[13px] text-[#9ba7ae]">
                    {completados} de {hitos.length} hitos completados
                </p>
            </div>

            {/* Timeline */}
            {hitos.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#fdf6f0] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#f57c00]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M7 4v4M17 4v4" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">No hay hitos aún</h3>
                    <p className="text-[13px] text-[#9ba7ae] mb-4">Crea el primer hito para comenzar el cronograma del proyecto</p>
                    <button
                        onClick={() => setModalHito(true)}
                        className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors">
                        <IconPlus />
                        Crear primer hito
                    </button>
                </div>
            ) : (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                    <div className="p-5 border-b border-[#e1e3e4] bg-[#f8f9fa]">
                        <div className="flex items-center gap-2 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">
                            <div className="w-2 h-2 rounded-full bg-[#2e7d32]" />
                            <span>Completado</span>
                            <div className="w-2 h-2 rounded-full bg-[#f57c00] ml-3" />
                            <span>En Progreso</span>
                            <div className="w-2 h-2 rounded-full bg-[#9ba7ae] ml-3" />
                            <span>Pendiente</span>
                        </div>
                    </div>

                    <div className="p-5">
                        {hitos.map((h, idx) => {
                            const info = ESTADOS[h.estado]
                            const rap = raps.find(r => r.id === h.rap_id)
                            return (
                                <div key={h.id} className={`flex items-start gap-4 pb-5 ${idx < hitos.length - 1 ? 'border-b border-[#e1e3e4] mb-5' : ''}`}>

                                    {/* Indicador visual */}
                                    <div className="flex flex-col items-center gap-1 pt-1">
                                        <div className={`w-4 h-4 rounded-full ${info.dot} flex-shrink-0`} />
                                        {idx < hitos.length - 1 && (
                                            <div className="w-0.5 h-12 bg-[#e1e3e4]" />
                                        )}
                                    </div>

                                    {/* Contenido */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-3 mb-2">
                                            <div>
                                                <h3 className="text-[15px] font-bold text-[#191c1d] mb-1">{h.nombre}</h3>
                                                {h.descripcion && (
                                                    <p className="text-[13px] text-[#5b403d] leading-relaxed mb-2">{h.descripcion}</p>
                                                )}
                                                <div className="flex items-center gap-3 flex-wrap">
                                                    <span className="text-[12px] text-[#9ba7ae]">
                                                        📅 {formatFecha(h.fecha_limite)}
                                                    </span>
                                                    {rap && (
                                                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-[#ffdad6] text-[#af101a]">
                                                            {rap.nombre}
                                                        </span>
                                                    )}
                                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold ${info.bg} ${info.text}`}>
                                                        <div className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />
                                                        {info.label}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => { setHitoEditando(h); setModalHito(true) }}
                                                    className="w-8 h-8 rounded-lg hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"
                                                    title="Editar">
                                                    <IconEdit />
                                                </button>
                                                <button
                                                    onClick={() => handleEliminar(h.id)}
                                                    disabled={eliminando === h.id}
                                                    className="w-8 h-8 rounded-lg hover:bg-[#fff1f0] flex items-center justify-center transition-colors disabled:opacity-50"
                                                    title="Eliminar">
                                                    <IconTrash />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Modal */}
            {modalHito && (
                <ModalHito
                    hito={hitoEditando}
                    raps={raps}
                    onGuardar={handleGuardarHito}
                    onCancelar={() => { setModalHito(false); setHitoEditando(null) }}
                    fechasProyecto={fechaInicio && fechaFin ? { inicio: fechaInicio, fin: fechaFin } : null}
                />
            )}
        </div>
    )
}