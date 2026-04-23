import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cursosApi } from '../../services/docenteApi'
import { periodosApi, session } from '../../services/api'


// ── Modal de confirmación eliminación ──────────────────────────────────────────

function ModalEliminar({ curso, onConfirm, onCancel }) {
    const tieneProyectos = curso.cantidad_equipos > 0 || curso.cantidad_estudiantes_actual > 0

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
            onClick={onCancel}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
                onClick={e => e.stopPropagation()}>

                <div className="p-6 flex flex-col gap-4">
                    <div className="flex items-start gap-3">
                        <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${tieneProyectos ? 'bg-[#fff1f0]' : 'bg-[#ffdad6]'
                            }`}>
                            <svg className={`w-5 h-5 ${tieneProyectos ? 'text-[#ba1a1a]' : 'text-[#af101a]'}`}
                                viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" clipRule="evenodd"
                                    d="M10 2a8 8 0 100 16 8 8 0 000-16zM9 9V6a1 1 0 112 0v3a1 1 0 11-2 0zm0 4a1 1 0 112 0 1 1 0 01-2 0z" />
                            </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                            <h3 className="text-[17px] font-bold text-[#191c1d] mb-1">
                                {tieneProyectos ? 'No se puede eliminar' : '¿Eliminar curso?'}
                            </h3>
                            <p className="text-[13px] text-[#5b403d] leading-relaxed">
                                {tieneProyectos ? (
                                    <>
                                        El curso <strong>{curso.nombre}</strong> tiene <strong>{curso.cantidad_estudiantes_actual} estudiante{curso.cantidad_estudiantes_actual !== 1 ? 's' : ''}</strong> inscritos{curso.cantidad_equipos > 0 && ` y ${curso.cantidad_equipos} proyecto${curso.cantidad_equipos !== 1 ? 's' : ''}`}.
                                        Debes eliminar o reasignar antes de poder eliminar el curso.
                                    </>
                                ) : (
                                    <>¿Estás seguro de eliminar <strong>{curso.nombre}</strong>? Esta acción no se puede deshacer.</>
                                )}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancel}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">
                        {tieneProyectos ? 'Entendido' : 'Cancelar'}
                    </button>
                    {!tieneProyectos && (
                        <button onClick={onConfirm}
                            className="flex-1 h-11 rounded-xl bg-[#ba1a1a] text-white font-semibold text-[14px] hover:bg-[#a00] transition-colors">
                            Eliminar
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}

// ── Modal crear/editar curso ───────────────────────────────────────────────────

function ModalCurso({ curso, periodos, onGuardar, onCancelar }) {
    const esEdicion = !!curso
    const [form, setForm] = useState({
        nombre: curso?.nombre ?? '',
        codigo: curso?.codigo ?? '',
        descripcion: curso?.descripcion ?? '',
        periodo_id: curso?.periodo_id ?? '',
        cantidad_max_estudiantes: curso?.cantidad_max_estudiantes ?? 30,
    })
    const [errores, setErrores] = useState({})
    const [guardando, setGuardando] = useState(false)

    function validar() {
        const e = {}
        if (!form.nombre.trim()) e.nombre = 'El nombre es obligatorio.'
        if (!form.codigo.trim()) e.codigo = 'El código es obligatorio.'
        if (!form.periodo_id) e.periodo_id = 'Selecciona un periodo.'
        if (!form.cantidad_max_estudiantes || form.cantidad_max_estudiantes < 1) {
            e.cantidad_max_estudiantes = 'La cantidad debe ser mayor a 0.'
        }
        return e
    }

    async function handleGuardar() {
        const e = validar()
        if (Object.keys(e).length > 0) { setErrores(e); return }

        setGuardando(true)
        try {
            const user = session.getUser()
            const data = {
                nombre: form.nombre,
                codigo: form.codigo.toUpperCase(),
                descripcion: form.descripcion,
                periodo_id: parseInt(form.periodo_id),
                cantidad_max_estudiantes: parseInt(form.cantidad_max_estudiantes),
                docente_id: user.id
            }

            let resultado
            if (esEdicion) {
                resultado = await cursosApi.editar(curso.id, data)
            } else {
                resultado = await cursosApi.crear(data)
            }

            onGuardar(resultado)

        } catch (error) {
            console.error('Error guardando curso:', error)

            if (error?.data?.codigo) {
                setErrores(e => ({ ...e, codigo: error.data.codigo[0] }))
            } else if (error?.status === 400) {
                alert('Hay un error en los datos. Verifica el código no esté duplicado.')
            } else {
                alert('Error al guardar el curso. Intenta de nuevo.')
            }
        } finally {
            setGuardando(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
            onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden"
                onClick={e => e.stopPropagation()}>

                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[19px] font-bold text-[#191c1d]">
                        {esEdicion ? 'Editar curso' : 'Crear nuevo curso'}
                    </h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        {esEdicion ? 'Modifica los datos del curso' : 'Completa la información del curso'}
                    </p>
                </div>

                <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto">

                    {/* Nombre */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Nombre del curso</label>
                        <input
                            type="text"
                            value={form.nombre}
                            onChange={e => { setForm(f => ({ ...f, nombre: e.target.value })); setErrores(e => ({ ...e, nombre: '' })) }}
                            placeholder="ej: Ingeniería de Software I"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.nombre ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'
                                }`}
                        />
                        {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                    </div>

                    {/* Código */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Código</label>
                        <input
                            type="text"
                            value={form.codigo}
                            onChange={e => { setForm(f => ({ ...f, codigo: e.target.value.toUpperCase() })); setErrores(e => ({ ...e, codigo: '' })) }}
                            placeholder="ej: IS-101"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.codigo ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'
                                }`}
                        />
                        {errores.codigo && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.codigo}</p>}
                    </div>

                    {/* Periodo */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Periodo académico</label>
                        <select
                            value={form.periodo_id}
                            onChange={e => { setForm(f => ({ ...f, periodo_id: e.target.value })); setErrores(e => ({ ...e, periodo_id: '' })) }}
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all appearance-none bg-white ${errores.periodo_id ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f]'
                                }`}
                        >
                            <option value="">Selecciona un periodo</option>
                            {periodos.map(p => (
                                <option key={p.id} value={p.id}>{p.nombre}</option>
                            ))}
                        </select>
                        {errores.periodo_id && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.periodo_id}</p>}
                    </div>

                    {/* Cantidad máxima de estudiantes */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Cantidad máxima de estudiantes</label>
                        <input
                            type="number"
                            min="1"
                            max="200"
                            value={form.cantidad_max_estudiantes}
                            onChange={e => { setForm(f => ({ ...f, cantidad_max_estudiantes: e.target.value })); setErrores(e => ({ ...e, cantidad_max_estudiantes: '' })) }}
                            placeholder="ej: 30"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.cantidad_max_estudiantes ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'
                                }`}
                        />
                        {errores.cantidad_max_estudiantes && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.cantidad_max_estudiantes}</p>}
                    </div>

                    {/* Descripción */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción (opcional)</label>
                        <textarea
                            value={form.descripcion}
                            onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                            placeholder="Breve descripción del contenido del curso..."
                            rows={3}
                            className="px-4 py-3 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all resize-none"
                        />
                    </div>
                </div>

                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancelar}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button onClick={handleGuardar} disabled={guardando}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        {guardando ? (
                            <>
                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Guardando...
                            </>
                        ) : (esEdicion ? 'Guardar cambios' : 'Crear curso')}
                    </button>
                </div>
            </div>
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function GestionCursos() {
    const navigate = useNavigate()
    const [cursos, setCursos] = useState([])
    const [periodos, setPeriodos] = useState([])
    const [loading, setLoading] = useState(true)

    // Filtros
    const [filtroPeriodo, setFiltroPeriodo] = useState('')
    const [filtroEstado, setFiltroEstado] = useState('')

    // Modales
    const [modalCrear, setModalCrear] = useState(false)
    const [cursoEditando, setCursoEditando] = useState(null)
    const [cursoEliminar, setCursoEliminar] = useState(null)

    useEffect(() => {
        cargarDatos()
    }, [])

    async function cargarDatos() {
        setLoading(true)
        try {
            // Cargar cursos
            const data = await cursosApi.listar()
            const cursosBackend = data.results ?? data

            const adaptados = cursosBackend.map(c => ({
                id: c.id,
                nombre: c.nombre,
                codigo: c.codigo,
                descripcion: c.descripcion,
                periodo_id: c.periodo_id,
                periodo_nombre: c.periodo?.nombre || 'Sin periodo',
                estado: c.estado,
                cantidad_estudiantes_actual: c.cantidad_estudiantes_actual ?? 0,
                cantidad_max_estudiantes: c.cantidad_max_estudiantes ?? 30,
                cantidad_equipos: c.cantidad_equipos ?? 0,
                docente: c.docente,
            }))

            setCursos(adaptados)

            // Cargar periodos
            const periodosData = await periodosApi.listar()
            setPeriodos(periodosData.results ?? periodosData)

        } catch (error) {
            console.error('Error cargando cursos:', error)
            alert('Error al cargar los cursos')
        } finally {
            setLoading(false)
        }
    }

    async function handleGuardarCurso(cursoGuardado) {
        const eraEdicion = !!cursoEditando

        setModalCrear(false)
        setCursoEditando(null)

        if (!eraEdicion && cursoGuardado?.id) {
            navigate(`/docente/cursos/${cursoGuardado.id}`)
        } else {
            cargarDatos()
        }
    }

    async function handleEliminarCurso() {
        try {
            await cursosApi.eliminar(cursoEliminar.id)
            setCursoEliminar(null)
            cargarDatos()

        } catch (error) {
            console.error('Error eliminando curso:', error)

            if (error?.status === 409) {
                alert(error?.data?.error || 'No se puede eliminar este curso')
            } else {
                alert('Error al eliminar el curso')
            }
        }
    }

    const cursosFiltrados = cursos.filter(c => {
        if (filtroPeriodo && c.periodo_id !== parseInt(filtroPeriodo)) return false
        if (filtroEstado && c.estado !== filtroEstado) return false
        return true
    })

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
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <h1 className="text-[24px] font-bold text-[#191c1d] leading-tight">Mis cursos</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Gestiona tus cursos y proyectos asociados</p>
                </div>
                <button
                    onClick={() => setModalCrear(true)}
                    className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm">
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <path d="M8 3v10M3 8h10" />
                    </svg>
                    Crear curso
                </button>
            </div>

            {/* Filtros */}
            <div className="mb-5 flex gap-3 flex-wrap">
                <select value={filtroPeriodo} onChange={e => setFiltroPeriodo(e.target.value)}
                    className="h-10 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all bg-white">
                    <option value="">Todos los periodos</option>
                    {periodos.map(p => (
                        <option key={p.id} value={p.id}>{p.nombre}</option>
                    ))}
                </select>

                <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}
                    className="h-10 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all bg-white">
                    <option value="">Todos los estados</option>
                    <option value="activo">Activo</option>
                    <option value="inactivo">Inactivo</option>
                </select>
            </div>

            {/* Tabla */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                            <th className="text-left px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Curso</th>
                            <th className="text-left px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Código</th>
                            <th className="text-left px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Periodo</th>
                            <th className="text-center px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Estudiantes</th>
                            <th className="text-center px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Proyectos</th>
                            <th className="text-center px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                            <th className="text-right px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cursosFiltrados.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="text-center py-12 text-[13px] text-[#9ba7ae]">
                                    {cursos.length === 0 ? 'No tienes cursos creados' : 'No hay cursos que coincidan con los filtros'}
                                </td>
                            </tr>
                        ) : (
                            cursosFiltrados.map(c => (
                                <tr key={c.id} className="border-b border-[#e1e3e4] last:border-0 hover:bg-[#fafbfb] transition-colors cursor-pointer"
                                    onClick={() => navigate(`/docente/cursos/${c.id}`)}>
                                    <td className="px-4 py-3.5">
                                        <p className="text-[14px] font-semibold text-[#191c1d]">{c.nombre}</p>
                                        {c.descripcion && <p className="text-[12px] text-[#9ba7ae] mt-0.5 line-clamp-1">{c.descripcion}</p>}
                                    </td>
                                    <td className="px-4 py-3.5 text-[13px] text-[#5b403d] font-medium">{c.codigo}</td>
                                    <td className="px-4 py-3.5 text-[13px] text-[#5b403d]">{c.periodo_nombre}</td>
                                    <td className="px-4 py-3.5 text-center">
                                        <span className="inline-flex items-center justify-center min-w-[28px] h-6 px-2 rounded-full bg-[#e3f2fd] text-[12px] font-semibold text-[#1565c0]">
                                            {c.cantidad_estudiantes_actual}/{c.cantidad_max_estudiantes}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 text-center">
                                        <span className="inline-flex items-center justify-center min-w-[28px] h-6 px-2 rounded-full bg-[#e8f5e9] text-[12px] font-semibold text-[#2e7d32]">
                                            {c.cantidad_equipos}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 text-center">
                                        <span className={`inline-block px-3 py-1 rounded-full text-[11px] font-semibold ${c.estado === 'activo' ? 'bg-[#e8f5e9] text-[#2e7d32]' : 'bg-[#f0f2f3] text-[#9ba7ae]'
                                            }`}>
                                            {c.estado === 'activo' ? 'Activo' : 'Inactivo'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
                                            <button
                                                onClick={() => setCursoEditando(c)}
                                                className="w-8 h-8 rounded-lg hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"
                                                title="Editar">
                                                <svg className="w-4 h-4 text-[#4c616c]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M11 2l3 3-9 9H2v-3l9-9z" />
                                                </svg>
                                            </button>
                                            <button
                                                onClick={() => setCursoEliminar(c)}
                                                className="w-8 h-8 rounded-lg hover:bg-[#fff1f0] flex items-center justify-center transition-colors"
                                                title="Eliminar">
                                                <svg className="w-4 h-4 text-[#ba1a1a]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M3 4h10M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1M6 7v5M10 7v5M4 4h8v9a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                                </svg>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modales */}
            {modalCrear && (
                <ModalCurso
                    periodos={periodos}
                    onGuardar={handleGuardarCurso}
                    onCancelar={() => setModalCrear(false)}
                />
            )}

            {cursoEditando && (
                <ModalCurso
                    curso={cursoEditando}
                    periodos={periodos}
                    onGuardar={handleGuardarCurso}
                    onCancelar={() => setCursoEditando(null)}
                />
            )}

            {cursoEliminar && (
                <ModalEliminar
                    curso={cursoEliminar}
                    onConfirm={handleEliminarCurso}
                    onCancel={() => setCursoEliminar(null)}
                />
            )}
        </div>
    )
}