import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { cursosApi } from '../../services/docenteApi'

const ESTADO_PROYECTO = {
    planificado: { label: 'Planificado', bg: 'bg-[#e3f2fd]', text: 'text-[#1565c0]', dot: 'bg-[#1565c0]' },
    en_ejecucion: { label: 'En ejecución', bg: 'bg-[#e8f5e9]', text: 'text-[#2e7d32]', dot: 'bg-[#2e7d32]' },
    finalizado: { label: 'Finalizado', bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]', dot: 'bg-[#9ba7ae]' },
}

function ModalProyecto({ cursoId, proyecto, onGuardar, onCancelar }) {
    const esEdicion = !!proyecto
    const [form, setForm] = useState({
        nombre: proyecto?.nombre ?? '',
        descripcion: proyecto?.descripcion ?? '',
        fecha_inicio: proyecto?.fecha_inicio ?? '',
        fecha_fin: proyecto?.fecha_fin ?? '',
        estado: proyecto?.estado ?? 'planificado',
    })
    const [errores, setErrores] = useState({})
    const [guardando, setGuardando] = useState(false)

    function validar() {
        const e = {}
        if (!form.nombre.trim()) e.nombre = 'El nombre es obligatorio.'
        if (!form.fecha_inicio) e.fecha_inicio = 'Selecciona una fecha de inicio.'
        if (!form.fecha_fin) e.fecha_fin = 'Selecciona una fecha de fin.'
        if (form.fecha_inicio && form.fecha_fin && new Date(form.fecha_fin) <= new Date(form.fecha_inicio)) {
            e.fecha_fin = 'La fecha de fin debe ser posterior a la de inicio.'
        }
        return e
    }

    async function handleGuardar() {
        const e = validar()
        if (Object.keys(e).length > 0) { setErrores(e); return }

        setGuardando(true)
        try {
            const data = { nombre: form.nombre, descripcion: form.descripcion, fecha_inicio: form.fecha_inicio, fecha_fin: form.fecha_fin, estado: form.estado, }
            if (esEdicion) {
                await cursosApi.editarProyecto(cursoId, proyecto.id, data)
            } else {
                await cursosApi.crearProyecto(cursoId, data)
            }
            onGuardar()
        } catch (error) {
            console.error('Error guardando proyecto:', error)
            if (error?.status === 400) {
                const msg = error?.data?.fecha_fin?.[0] ?? error?.data?.non_field_errors?.[0]
                if (msg) setErrores(e => ({ ...e, fecha_fin: msg }))
                else alert('Verifica los datos e intenta de nuevo.')
            } else {
                alert('Error al guardar el proyecto.')
            }
        } finally {
            setGuardando(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[19px] font-bold text-[#191c1d]">{esEdicion ? 'Editar proyecto' : 'Nuevo proyecto'}</h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Define los datos del proyecto ABP</p>
                </div>

                <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto">
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Nombre del proyecto</label>
                        <input type="text" value={form.nombre}
                            onChange={e => { setForm(f => ({ ...f, nombre: e.target.value })); setErrores(e => ({ ...e, nombre: '' })) }}
                            placeholder="ej: Sistema de Gestión de Inventario"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.nombre ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción (opcional)</label>
                        <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                            placeholder="Breve descripción del alcance..." rows={3}
                            className="px-4 py-3 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all resize-none"
                        />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Fecha de inicio</label>
                            <input type="date" value={form.fecha_inicio}
                                onChange={e => { setForm(f => ({ ...f, fecha_inicio: e.target.value })); setErrores(e => ({ ...e, fecha_inicio: '', fecha_fin: '' })) }}
                                className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.fecha_inicio ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                            />
                            {errores.fecha_inicio && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.fecha_inicio}</p>}
                        </div>
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Fecha de fin</label>
                            <input type="date" value={form.fecha_fin}
                                onChange={e => { setForm(f => ({ ...f, fecha_fin: e.target.value })); setErrores(e => ({ ...e, fecha_fin: '' })) }}
                                className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.fecha_fin ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                            />
                            {errores.fecha_fin && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.fecha_fin}</p>}
                        </div>
                    </div>
                </div>

                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancelar} className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">Cancelar</button>
                    <button onClick={handleGuardar} disabled={guardando}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        {guardando
                            ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Guardando...</>
                            : esEdicion ? 'Guardar cambios' : 'Crear proyecto'}
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

export default function DetalleCurso() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [curso, setCurso] = useState(null)
    const [proyectos, setProyectos] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalNuevoProyecto, setModalNuevoProyecto] = useState(false)
    const [proyectoEditando, setProyectoEditando] = useState(null)

    useEffect(() => { cargarDatos() }, [id])

    async function cargarDatos() {
        setLoading(true)
        try {
            const [cursoData, proyectosData] = await Promise.all([
                cursosApi.obtener(id),
                cursosApi.obtenerProyectos(id).catch(() => []),
            ])
            setCurso(cursoData)
            setProyectos(proyectosData.results ?? proyectosData)
        } catch (error) {
            console.error('Error cargando datos:', error)
            setCurso(null)
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

    if (!curso) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-4">
                <div className="w-16 h-16 rounded-2xl bg-[#ffdad6] flex items-center justify-center">
                    <svg className="w-8 h-8 text-[#af101a]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                </div>
                <h2 className="text-[17px] font-bold text-[#191c1d]">Curso no encontrado</h2>
                <Link to="/docente/cursos" className="text-[13px] text-[#d32f2f] hover:underline">Volver a mis cursos</Link>
            </div>
        )
    }

    const estadoCurso = curso.estado === 'activo' ? { label: 'Activo', bg: 'bg-[#e8f5e9]', text: 'text-[#2e7d32]' }
        : curso.estado === 'cerrado' ? { label: 'Cerrado', bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]' }
            : { label: 'Borrador', bg: 'bg-[#fff8e1]', text: 'text-[#f57f17]' }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px] flex-wrap">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="text-[#191c1d] font-medium truncate max-w-[200px]">{curso.nombre}</span>
            </div>

            {/* Card info curso */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 sm:p-6 mb-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                            <h1 className="text-[20px] sm:text-[24px] font-bold text-[#191c1d] leading-tight">{curso.nombre}</h1>
                            <span className={`inline-block px-3 py-1 rounded-full text-[11px] font-semibold ${estadoCurso.bg} ${estadoCurso.text}`}>
                                {estadoCurso.label}
                            </span>
                        </div>
                        {curso.descripcion && (
                            <p className="text-[14px] text-[#5b403d] leading-relaxed mb-3">{curso.descripcion}</p>
                        )}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] text-[#5b403d]">
                            <span><strong>Código:</strong> {curso.codigo}</span>
                            <span><strong>Periodo:</strong> {curso.periodo_nombre}</span>
                            <span><strong>Estudiantes:</strong> {curso.cantidad_estudiantes_actual}/{curso.cantidad_max_estudiantes}</span>
                            {curso.docente_nombre && <span><strong>Docente:</strong> {curso.docente_nombre}</span>}
                        </div>
                    </div>
                    <button
                        onClick={() => setModalNuevoProyecto(true)}
                        className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm flex-shrink-0 self-start">
                        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
                        Nuevo proyecto
                    </button>
                </div>
            </div>

            {/* Proyectos */}
            <h2 className="text-[17px] font-bold text-[#191c1d] mb-3">
                Proyectos del curso <span className="text-[#9ba7ae] font-medium">({proyectos.length})</span>
            </h2>

            {proyectos.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#fdf6f0] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#f57c00]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6M12 18v-6M9 15h6" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">No hay proyectos aún</h3>
                    <p className="text-[13px] text-[#9ba7ae] mb-4">Crea el primer proyecto ABP para este curso</p>
                    <button onClick={() => setModalNuevoProyecto(true)}
                        className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors">
                        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
                        Crear proyecto
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {proyectos.map(p => {
                        const info = ESTADO_PROYECTO[p.estado] ?? ESTADO_PROYECTO.planificado
                        return (
                            <div key={p.id} className="bg-white rounded-2xl border border-[#e1e3e4] p-5 hover:shadow-md hover:border-[#d1d3d4] transition-all flex flex-col gap-3">
                                {/* Header */}
                                <div className="flex items-start justify-between gap-2">
                                    <h3 className="text-[15px] font-semibold text-[#191c1d] leading-snug">{p.nombre}</h3>
                                    <span className={`flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[11px] font-semibold ${info.bg} ${info.text}`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />
                                        {info.label}
                                    </span>
                                </div>

                                {p.descripcion && (
                                    <p className="text-[13px] text-[#5b403d] leading-relaxed line-clamp-2">{p.descripcion}</p>
                                )}

                                {/* Fechas */}
                                <div className="flex items-center gap-1.5 text-[12px] text-[#9ba7ae]">
                                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                        <rect x="2" y="3" width="12" height="11" rx="1.5" /><path d="M2 6h12M5 2v2M11 2v2" />
                                    </svg>
                                    <span>{formatFecha(p.fecha_inicio)} — {formatFecha(p.fecha_fin)}</span>
                                </div>

                                {/* Footer */}
                                <div className="flex items-center justify-between pt-3 border-t border-[#f0f2f3] mt-auto">
                                    <span className="text-[12px] text-[#5b403d] font-medium">
                                        {p.cantidad_equipos} equipo{p.cantidad_equipos !== 1 ? 's' : ''}
                                    </span>
                                    <div className="flex gap-1">
                                        <button onClick={() => setProyectoEditando(p)}
                                            className="w-7 h-7 rounded-lg hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Editar proyecto">
                                            <svg className="w-3.5 h-3.5 text-[#4c616c]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M11 2l3 3-9 9H2v-3l9-9z" /></svg>
                                        </button>
                                        <button onClick={() => navigate(`/docente/proyectos/${p.id}/equipos`)}
                                            className="h-7 px-2.5 rounded-lg bg-[#f0f2f3] hover:bg-[#d32f2f] hover:text-white text-[#4c616c] text-[11px] font-semibold transition-colors flex items-center gap-1">
                                            <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M11 7a3 3 0 11-6 0 3 3 0 016 0z" /><path d="M3 14a5 5 0 0110 0" />
                                            </svg>
                                            Equipos
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Modales */}
            {modalNuevoProyecto && (
                <ModalProyecto cursoId={id} onGuardar={() => { setModalNuevoProyecto(false); cargarDatos() }} onCancelar={() => setModalNuevoProyecto(false)} />
            )}
            {proyectoEditando && (
                <ModalProyecto cursoId={id} proyecto={proyectoEditando} onGuardar={() => { setProyectoEditando(null); cargarDatos() }} onCancelar={() => setProyectoEditando(null)} />
            )}
        </div>
    )
}