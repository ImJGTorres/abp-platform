import { useState, useEffect, useRef } from 'react'
import { cursosAdminApi, periodosApi } from '../services/api'

// ── Modal crear/editar curso ──────────────────────────────────────────────────

function ModalCurso({ curso, periodos, docentes, onGuardar, onCancelar }) {
    const esEdicion = !!curso
    const [form, setForm] = useState({
        nombre: curso?.nombre ?? '',
        codigo: curso?.codigo ?? '',
        descripcion: curso?.descripcion ?? '',
        id_periodo_academico: curso?.id_periodo_academico ?? '',
        id_docente: curso?.id_docente ?? '',
        cantidad_max_estudiantes: curso?.cantidad_max_estudiantes ?? 30,
        estado: curso?.estado ?? 'borrador',
    })
    const [errores, setErrores] = useState({})
    const [guardando, setGuardando] = useState(false)

    function set(campo, val) {
        setForm(f => ({ ...f, [campo]: val }))
        setErrores(e => ({ ...e, [campo]: '' }))
    }

    function validar() {
        const e = {}
        if (!form.nombre.trim()) e.nombre = 'El nombre es obligatorio.'
        if (!form.codigo.trim()) e.codigo = 'El código es obligatorio.'
        if (!form.id_periodo_academico) e.id_periodo_academico = 'Selecciona un periodo.'
        if (!form.id_docente) e.id_docente = 'Selecciona un docente.'
        if (!form.cantidad_max_estudiantes || form.cantidad_max_estudiantes < 1) e.cantidad_max_estudiantes = 'Debe ser mayor a 0.'
        return e
    }

    async function handleGuardar() {
        const e = validar()
        if (Object.keys(e).length > 0) { setErrores(e); return }
        setGuardando(true)
        try {
            const payload = {
                nombre: form.nombre.trim(),
                codigo: form.codigo.trim().toUpperCase(),
                descripcion: form.descripcion.trim(),
                id_periodo_academico: parseInt(form.id_periodo_academico),
                id_docente: parseInt(form.id_docente),
                cantidad_max_estudiantes: parseInt(form.cantidad_max_estudiantes),
                ...(esEdicion && { estado: form.estado }),
            }
            let resultado
            if (esEdicion) {
                resultado = await cursosAdminApi.editar(curso.id, payload)
            } else {
                resultado = await cursosAdminApi.crear(payload)
            }
            onGuardar(resultado)
        } catch (error) {
            if (error?.data?.codigo) setErrores(e => ({ ...e, codigo: error.data.codigo[0] }))
            else if (error?.data?.non_field_errors) alert(error.data.non_field_errors[0])
            else alert('Error al guardar el curso.')
        } finally {
            setGuardando(false)
        }
    }

    const inputCls = (campo) =>
        `h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all bg-white ${errores[campo] ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f]'}`

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[19px] font-bold text-[#191c1d]">{esEdicion ? 'Editar curso' : 'Crear nuevo curso'}</h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Completa la información del curso</p>
                </div>

                <div className="p-6 flex flex-col gap-4 max-h-[65vh] overflow-y-auto">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Nombre del curso</label>
                            <input type="text" value={form.nombre} onChange={e => set('nombre', e.target.value)}
                                placeholder="ej: Ingeniería de Software I" className={inputCls('nombre')} />
                            {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Código</label>
                            <input type="text" value={form.codigo} onChange={e => set('codigo', e.target.value.toUpperCase())}
                                placeholder="ej: IS-101" className={inputCls('codigo')} />
                            {errores.codigo && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.codigo}</p>}
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Máx. estudiantes</label>
                            <input type="number" min="1" max="300" value={form.cantidad_max_estudiantes}
                                onChange={e => set('cantidad_max_estudiantes', e.target.value)}
                                className={inputCls('cantidad_max_estudiantes')} />
                            {errores.cantidad_max_estudiantes && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.cantidad_max_estudiantes}</p>}
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Periodo académico</label>
                            <select value={form.id_periodo_academico} onChange={e => set('id_periodo_academico', e.target.value)}
                                className={`${inputCls('id_periodo_academico')} appearance-none`}>
                                <option value="">Selecciona un periodo</option>
                                {periodos.filter(p => p.estado === 'activo').map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                            </select>
                            {errores.id_periodo_academico && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.id_periodo_academico}</p>}
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Docente</label>
                            <select value={form.id_docente} onChange={e => set('id_docente', e.target.value)}
                                className={`${inputCls('id_docente')} appearance-none`}>
                                <option value="">Selecciona un docente</option>
                                {docentes.map(d => <option key={d.id} value={d.id}>{d.nombre} {d.apellido}</option>)}
                            </select>
                            {errores.id_docente && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.id_docente}</p>}
                        </div>

                        {esEdicion && (
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Estado</label>
                                <select value={form.estado} onChange={e => set('estado', e.target.value)}
                                    className={`${inputCls('estado')} appearance-none`}>
                                    <option value="borrador">Borrador</option>
                                    <option value="activo">Activo</option>
                                    <option value="cerrado">Cerrado</option>
                                </select>
                            </div>
                        )}

                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción (opcional)</label>
                            <textarea value={form.descripcion} onChange={e => set('descripcion', e.target.value)}
                                placeholder="Breve descripción del curso..." rows={3}
                                className="px-4 py-3 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all resize-none" />
                        </div>
                    </div>
                </div>

                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancelar} className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">Cancelar</button>
                    <button onClick={handleGuardar} disabled={guardando}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        {guardando
                            ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Guardando...</>
                            : esEdicion ? 'Guardar cambios' : 'Crear curso'}
                    </button>
                </div>
            </div>
        </div>
    )
}

// ── Modal confirmar eliminación ───────────────────────────────────────────────

function ModalEliminar({ curso, onConfirm, onCancel }) {
    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancel}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="p-6 flex flex-col gap-4">
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-[#ffdad6] flex items-center justify-center">
                            <svg className="w-5 h-5 text-[#af101a]" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" clipRule="evenodd" d="M10 2a8 8 0 100 16 8 8 0 000-16zM9 9V6a1 1 0 112 0v3a1 1 0 11-2 0zm0 4a1 1 0 112 0 1 1 0 01-2 0z" />
                            </svg>
                        </div>
                        <div>
                            <h3 className="text-[17px] font-bold text-[#191c1d] mb-1">¿Eliminar curso?</h3>
                            <p className="text-[13px] text-[#5b403d] leading-relaxed">
                                Estás por eliminar <strong>{curso.nombre}</strong>. Esta acción no se puede deshacer.
                                {curso.total_proyectos > 0 && (
                                    <span className="block mt-1 text-[#ba1a1a] font-medium">Este curso tiene {curso.total_proyectos} proyecto{curso.total_proyectos !== 1 ? 's' : ''} vinculado{curso.total_proyectos !== 1 ? 's' : ''}.</span>
                                )}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancel} className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">Cancelar</button>
                    {curso.total_proyectos === 0 && (
                        <button onClick={onConfirm} className="flex-1 h-11 rounded-xl bg-[#ba1a1a] text-white font-semibold text-[14px] hover:bg-[#a00] transition-colors">Eliminar</button>
                    )}
                </div>
            </div>
        </div>
    )
}

// ── Carga masiva ──────────────────────────────────────────────────────────────

function CargaMasivaCursos({ onCargado }) {
    const [archivo, setArchivo] = useState(null)
    const [cargando, setCargando] = useState(false)
    const [resultado, setResultado] = useState(null)
    const inputRef = useRef(null)

    async function handleCargar() {
        if (!archivo) return
        setCargando(true)
        setResultado(null)
        try {
            const data = await cursosAdminApi.cargaMasiva(archivo)
            setResultado({ tipo: 'exito', data })
            setArchivo(null)
            if (inputRef.current) inputRef.current.value = ''
            if (data.creados > 0) onCargado?.()
        } catch (error) {
            setResultado({ tipo: 'error', msg: error?.data?.detail ?? 'Error al procesar el archivo.' })
        } finally {
            setCargando(false)
        }
    }

    return (
        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
            <h3 className="text-[15px] font-bold text-[#191c1d] mb-1">Carga masiva de cursos</h3>
            <p className="text-[12px] text-[#9ba7ae] mb-4">Archivo Excel (.xlsx) con columnas: nombre, código, descripción, correo_docente, cantidad_max</p>

            <div className="flex flex-col sm:flex-row gap-3 mb-4">
                <label className="flex-1 h-11 rounded-xl border-2 border-dashed border-[#e1e3e4] flex items-center justify-center gap-2 cursor-pointer hover:border-[#d32f2f] hover:bg-[#fff8f7] transition-all px-4 text-[13px] text-[#9ba7ae]">
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2 12V14h12v-2M8 2v8M5 5l3-3 3 3" />
                    </svg>
                    {archivo ? archivo.name : 'Seleccionar archivo .xlsx'}
                    <input ref={inputRef} type="file" accept=".xlsx" className="hidden"
                        onChange={e => { setArchivo(e.target.files[0] ?? null); setResultado(null) }} />
                </label>
                <button onClick={handleCargar} disabled={!archivo || cargando}
                    className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0">
                    {cargando
                        ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Procesando...</>
                        : 'Cargar'}
                </button>
            </div>

            {resultado?.tipo === 'exito' && (
                <div className="rounded-xl bg-[#e8f5e9] border border-[#a5d6a7] p-4">
                    <p className="text-[13px] font-semibold text-[#2e7d32] mb-1">
                        {resultado.data.creados} curso{resultado.data.creados !== 1 ? 's' : ''} creado{resultado.data.creados !== 1 ? 's' : ''} correctamente
                    </p>
                    {resultado.data.omitidos > 0 && (
                        <p className="text-[12px] text-[#558b2f]">{resultado.data.omitidos} omitido{resultado.data.omitidos !== 1 ? 's' : ''}</p>
                    )}
                    {resultado.data.errores?.length > 0 && (
                        <div className="mt-3 overflow-x-auto">
                            <table className="w-full text-[11px]">
                                <thead><tr className="text-[#558b2f]"><th className="text-left pr-3 pb-1">Fila</th><th className="text-left pr-3 pb-1">Código</th><th className="text-left pb-1">Motivo</th></tr></thead>
                                <tbody>{resultado.data.errores.map((err, i) => (
                                    <tr key={i} className="border-t border-[#c8e6c9]">
                                        <td className="pr-3 py-1">{err.fila}</td>
                                        <td className="pr-3 py-1 font-medium">{err.codigo}</td>
                                        <td className="py-1 text-[#ba1a1a]">{err.motivo}</td>
                                    </tr>
                                ))}</tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
            {resultado?.tipo === 'error' && (
                <div className="rounded-xl bg-[#fff1f0] border border-[#ffcdd2] p-4">
                    <p className="text-[13px] text-[#ba1a1a]">{resultado.msg}</p>
                </div>
            )}
        </div>
    )
}

// ── Badge estado ──────────────────────────────────────────────────────────────

const ESTADO_BADGE = {
    activo: 'bg-[#e8f5e9] text-[#2e7d32]',
    borrador: 'bg-[#fff8e1] text-[#f57f17]',
    cerrado: 'bg-[#f0f2f3] text-[#9ba7ae]',
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function GestionCursosAdmin() {
    const [cursos, setCursos] = useState([])
    const [periodos, setPeriodos] = useState([])
    const [docentes, setDocentes] = useState([])
    const [loading, setLoading] = useState(true)
    const [busqueda, setBusqueda] = useState('')
    const [modalCrear, setModalCrear] = useState(false)
    const [cursoEditando, setCursoEditando] = useState(null)
    const [cursoEliminar, setCursoEliminar] = useState(null)
    const [eliminando, setEliminando] = useState(false)

    useEffect(() => { cargarDatos() }, [])

    async function cargarDatos() {
        setLoading(true)
        try {
            const [cursosData, periodosData, docentesData] = await Promise.all([
                cursosAdminApi.listar(),
                periodosApi.listar(),
                cursosAdminApi.listarDocentes(),
            ])
            setCursos(cursosData.results ?? cursosData)
            setPeriodos(periodosData.results ?? periodosData)
            setDocentes(docentesData.results ?? docentesData)
        } catch (error) {
            console.error('Error cargando datos:', error)
        } finally {
            setLoading(false)
        }
    }

    async function handleEliminar() {
        if (!cursoEliminar) return
        setEliminando(true)
        try {
            await cursosAdminApi.eliminar(cursoEliminar.id)
            setCursoEliminar(null)
            cargarDatos()
        } catch (error) {
            if (error?.status === 409) {
                alert(error?.data?.detail ?? 'No se puede eliminar: tiene proyectos vinculados.')
            } else {
                alert('Error al eliminar el curso.')
            }
        } finally {
            setEliminando(false)
        }
    }

    const cursosFiltrados = cursos.filter(c => {
        if (!busqueda) return true
        const q = busqueda.toLowerCase()
        return c.nombre.toLowerCase().includes(q) || c.codigo.toLowerCase().includes(q) || (c.docente_nombre ?? '').toLowerCase().includes(q)
    })

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-[22px] sm:text-[24px] font-bold text-[#191c1d] leading-tight">Gestión de cursos</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Administra los cursos del sistema</p>
                </div>
                <button onClick={() => setModalCrear(true)}
                    className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm self-start sm:self-auto">
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 3v10M3 8h10" /></svg>
                    Nuevo curso
                </button>
            </div>

            {/* Buscador */}
            <div className="mb-4">
                <input type="text" value={busqueda} onChange={e => setBusqueda(e.target.value)}
                    placeholder="Buscar por nombre, código o docente..."
                    className="w-full sm:max-w-sm h-10 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all bg-white" />
            </div>

            {/* Tabla */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden mb-6">
                {loading ? (
                    <div className="flex items-center justify-center py-16">
                        <svg className="w-7 h-7 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full min-w-[600px]">
                            <thead>
                                <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                    {['Nombre / Código', 'Docente', 'Periodo', 'Proyectos', 'Estado', 'Acciones'].map(col => (
                                        <th key={col} className="text-left px-4 py-3 text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {cursosFiltrados.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="text-center py-12 text-[13px] text-[#9ba7ae]">
                                            {cursos.length === 0 ? 'No hay cursos registrados' : 'Sin resultados para la búsqueda'}
                                        </td>
                                    </tr>
                                ) : cursosFiltrados.map(c => (
                                    <tr key={c.id} className="border-b border-[#e1e3e4] last:border-0 hover:bg-[#fafbfb] transition-colors">
                                        <td className="px-4 py-3.5">
                                            <p className="text-[14px] font-semibold text-[#191c1d]">{c.nombre}</p>
                                            <p className="text-[12px] text-[#9ba7ae] font-medium mt-0.5">{c.codigo}</p>
                                        </td>
                                        <td className="px-4 py-3.5 text-[13px] text-[#5b403d]">{c.docente_nombre}</td>
                                        <td className="px-4 py-3.5 text-[13px] text-[#5b403d]">{c.periodo_nombre}</td>
                                        <td className="px-4 py-3.5 text-center">
                                            <span className="inline-flex items-center justify-center min-w-[24px] h-6 px-2 rounded-full bg-[#e8f5e9] text-[12px] font-semibold text-[#2e7d32]">{c.total_proyectos}</span>
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <span className={`inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold capitalize ${ESTADO_BADGE[c.estado] ?? ESTADO_BADGE.borrador}`}>
                                                {c.estado}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-1">
                                                <button onClick={() => setCursoEditando(c)}
                                                    className="w-8 h-8 rounded-lg hover:bg-[#f0f2f3] flex items-center justify-center transition-colors" title="Editar">
                                                    <svg className="w-4 h-4 text-[#4c616c]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M11 2l3 3-9 9H2v-3l9-9z" />
                                                    </svg>
                                                </button>
                                                <button onClick={() => setCursoEliminar(c)}
                                                    className="w-8 h-8 rounded-lg hover:bg-[#fff1f0] flex items-center justify-center transition-colors" title="Eliminar">
                                                    <svg className="w-4 h-4 text-[#ba1a1a]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M3 4h10M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1M6 7v5M10 7v5M4 4h8v9a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Carga masiva */}
            <CargaMasivaCursos onCargado={cargarDatos} />

            {/* Modales */}
            {(modalCrear || cursoEditando) && (
                <ModalCurso
                    curso={cursoEditando}
                    periodos={periodos}
                    docentes={docentes}
                    onGuardar={() => { setModalCrear(false); setCursoEditando(null); cargarDatos() }}
                    onCancelar={() => { setModalCrear(false); setCursoEditando(null) }}
                />
            )}

            {cursoEliminar && (
                <ModalEliminar
                    curso={cursoEliminar}
                    onConfirm={handleEliminar}
                    onCancel={() => setCursoEliminar(null)}
                />
            )}

            {eliminando && (
                <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
                    <svg className="w-8 h-8 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                </div>
            )}
        </div>
    )
}