import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { estudiantesApi, cursosApi, equiposApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']

function colorFor(id) {
    return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function iniciales(nombre, apellido) {
    return (nombre?.[0]?.toUpperCase() ?? '') + (apellido?.[0]?.toUpperCase() ?? '')
}

// ── Modal de asignación ───────────────────────────────────────────────────────

function ModalAsignar({ estudiantesIds, proyectos, cursoId, onClose, onExito }) {
    const [modo, setModo] = useState('existente')
    const [proyectoId, setProyectoId] = useState(
        proyectos.length === 1 ? String(proyectos[0].id) : ''
    )
    const [nuevoNombre, setNuevoNombre] = useState('')
    const [nuevaFechaInicio, setNuevaFechaInicio] = useState('')
    const [nuevaFechaFin, setNuevaFechaFin] = useState('')
    const [asignando, setAsignando] = useState(false)
    const [errMsg, setErrMsg] = useState('')

    const proyecto = proyectos.find(p => String(p.id) === proyectoId)
    const equipo = proyecto?.equipo

    async function handleConfirmar() {
        setErrMsg('')
        setAsignando(true)
        try {
            let targetEquipoId

            if (modo === 'nuevo') {
                if (!nuevoNombre.trim()) { setErrMsg('El nombre del proyecto es obligatorio.'); setAsignando(false); return }
                const nuevoProy = await cursosApi.crearProyecto(cursoId, {
                    nombre: nuevoNombre.trim(),
                    fecha_inicio: nuevaFechaInicio || undefined,
                    fecha_fin_estimada: nuevaFechaFin || undefined,
                })
                const nuevoEquipo = await equiposApi.crearEquipo(nuevoProy.id, {
                    nombre: nuevoNombre.trim(),
                    descripcion: '',
                    cupo_maximo: 5,
                })
                targetEquipoId = nuevoEquipo.id
            } else {
                if (!proyectoId) { setErrMsg('Selecciona un proyecto.'); setAsignando(false); return }
                targetEquipoId = equipo?.id
                if (!targetEquipoId) {
                    const nuevoEquipo = await equiposApi.crearEquipo(Number(proyectoId), {
                        nombre: proyecto.nombre,
                        descripcion: '',
                        cupo_maximo: 5,
                    })
                    targetEquipoId = nuevoEquipo.id
                }
            }

            const result = await equiposApi.asignarEstudiantes(targetEquipoId, estudiantesIds)
            onExito(result.asignados ?? estudiantesIds.length, result.errores ?? [])
        } catch (err) {
            setErrMsg(err?.data?.detail ?? 'Error al asignar estudiantes.')
        } finally {
            setAsignando(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
            onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
                onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[17px] font-bold text-[#191c1d]">
                        Asignar {estudiantesIds.length} estudiante{estudiantesIds.length !== 1 ? 's' : ''}
                    </h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Asígnalos a un proyecto existente o crea uno nuevo</p>
                </div>

                <div className="p-6 flex flex-col gap-4">
                    {/* Tabs */}
                    <div className="flex rounded-xl border border-[#e1e3e4] overflow-hidden">
                        <button onClick={() => { setModo('existente'); setErrMsg('') }}
                            className={`flex-1 py-2.5 text-[13px] font-semibold transition-colors ${modo === 'existente' ? 'bg-[#d32f2f] text-white' : 'text-[#4c616c] hover:bg-[#f0f2f3]'}`}>
                            Proyecto existente
                        </button>
                        <button onClick={() => { setModo('nuevo'); setErrMsg('') }}
                            className={`flex-1 py-2.5 text-[13px] font-semibold transition-colors ${modo === 'nuevo' ? 'bg-[#d32f2f] text-white' : 'text-[#4c616c] hover:bg-[#f0f2f3]'}`}>
                            Nuevo proyecto
                        </button>
                    </div>

                    {/* Proyecto existente */}
                    {modo === 'existente' && (
                        <>
                            {proyectos.length > 1 ? (
                                <div className="flex flex-col gap-1.5">
                                    <label className="text-[13px] font-semibold text-[#191c1d]">Proyecto</label>
                                    <select
                                        value={proyectoId}
                                        onChange={e => { setProyectoId(e.target.value); setErrMsg('') }}
                                        className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] bg-white transition-all">
                                        <option value="">Seleccionar proyecto…</option>
                                        {proyectos.map(p => (
                                            <option key={p.id} value={p.id}>{p.nombre}</option>
                                        ))}
                                    </select>
                                </div>
                            ) : proyectos.length === 1 ? (
                                <p className="text-[13px] text-[#9ba7ae]">
                                    Proyecto: <span className="font-semibold text-[#191c1d]">{proyectos[0].nombre}</span>
                                </p>
                            ) : (
                                <p className="text-[13px] text-[#9ba7ae]">
                                    No hay proyectos en este curso.{' '}
                                    <button className="text-[#d32f2f] hover:underline" onClick={() => setModo('nuevo')}>Crea uno.</button>
                                </p>
                            )}

                            {proyecto && equipo && (
                                <div className="bg-[#f8f9fa] rounded-xl px-4 py-3 flex items-center justify-between">
                                    <div>
                                        <p className="text-[12px] font-semibold text-[#191c1d]">{equipo.nombre}</p>
                                        <p className="text-[12px] text-[#9ba7ae] mt-0.5">
                                            {equipo.cantidad_miembros ?? equipo.miembros?.length ?? 0} / {equipo.cupo_maximo} miembros
                                        </p>
                                    </div>
                                    <span className="text-[11px] font-semibold text-[#2e7d32] bg-[#e8f5e9] px-2 py-0.5 rounded-md">ACTIVO</span>
                                </div>
                            )}

                            {proyecto && !equipo && (
                                <div className="bg-[#fff8e1] rounded-xl px-4 py-3">
                                    <p className="text-[12px] text-[#f57c00]">
                                        Este proyecto aún no tiene equipo. Se creará uno automáticamente al confirmar.
                                    </p>
                                </div>
                            )}
                        </>
                    )}

                    {/* Nuevo proyecto */}
                    {modo === 'nuevo' && (
                        <>
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-semibold text-[#191c1d]">Nombre del proyecto</label>
                                <input
                                    type="text"
                                    value={nuevoNombre}
                                    onChange={e => { setNuevoNombre(e.target.value); setErrMsg('') }}
                                    placeholder="ej: Sistema de Gestión de Inventario"
                                    className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="flex flex-col gap-1.5">
                                    <label className="text-[13px] font-semibold text-[#191c1d]">Fecha inicio <span className="text-[#9ba7ae] font-normal">(opcional)</span></label>
                                    <input
                                        type="date"
                                        value={nuevaFechaInicio}
                                        onChange={e => setNuevaFechaInicio(e.target.value)}
                                        className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all"
                                    />
                                </div>
                                <div className="flex flex-col gap-1.5">
                                    <label className="text-[13px] font-semibold text-[#191c1d]">Fecha fin <span className="text-[#9ba7ae] font-normal">(opcional)</span></label>
                                    <input
                                        type="date"
                                        value={nuevaFechaFin}
                                        onChange={e => setNuevaFechaFin(e.target.value)}
                                        className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {errMsg && <p className="text-[12px] text-[#ba1a1a] px-1">{errMsg}</p>}
                </div>

                {/* Footer */}
                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onClose}
                        className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">
                        Cancelar
                    </button>
                    <button onClick={handleConfirmar} disabled={asignando || (modo === 'existente' && !proyectoId)}
                        className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        {asignando ? (
                            <>
                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Asignando…
                            </>
                        ) : 'Confirmar asignación'}
                    </button>
                </div>
            </div>
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function EstudiantesCurso() {
    const { id: cursoId } = useParams()

    const [estudiantes, setEstudiantes] = useState(null)
    const [proyectos, setProyectos] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [busqueda, setBusqueda] = useState('')
    const [seleccionados, setSeleccionados] = useState(new Set())
    const [modalAbierto, setModalAbierto] = useState(false)
    const [toast, setToast] = useState(null)

    useEffect(() => { cargarDatos() }, [cursoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        setSeleccionados(new Set())
        try {
            const [estData, proyData] = await Promise.all([
                estudiantesApi.listarPorCurso(cursoId),
                cursosApi.obtenerProyectos(cursoId),
            ])
            setEstudiantes(estData)
            const lista = proyData.results ?? proyData
            setProyectos(lista)
        } catch {
            setError('No se pudo cargar la información del curso.')
        } finally {
            setLoading(false)
        }
    }

    function toggleSeleccion(id) {
        setSeleccionados(prev => {
            const next = new Set(prev)
            next.has(id) ? next.delete(id) : next.add(id)
            return next
        })
    }

    function handleExito(asignados, errores) {
        setModalAbierto(false)
        setSeleccionados(new Set())
        const msg = errores.length > 0
            ? `${asignados} asignados. ${errores.length} con errores.`
            : `${asignados} estudiante${asignados !== 1 ? 's' : ''} asignado${asignados !== 1 ? 's' : ''} correctamente.`
        setToast(msg)
        setTimeout(() => setToast(null), 4000)
        cargarDatos()
    }

    const disponiblesFiltrados = useMemo(() => {
        if (!estudiantes) return []
        const q = busqueda.toLowerCase()
        if (!q) return estudiantes.disponibles
        return estudiantes.disponibles.filter(e =>
            `${e.nombre} ${e.apellido}`.toLowerCase().includes(q) ||
            e.correo.toLowerCase().includes(q) ||
            (e.codigo_estudiante ?? '').toLowerCase().includes(q)
        )
    }, [estudiantes, busqueda])

    const enEquipoFiltrados = useMemo(() => {
        if (!estudiantes) return []
        const q = busqueda.toLowerCase()
        if (!q) return estudiantes.en_equipo
        return estudiantes.en_equipo.filter(e =>
            `${e.nombre} ${e.apellido}`.toLowerCase().includes(q) ||
            e.correo.toLowerCase().includes(q) ||
            (e.codigo_estudiante ?? '').toLowerCase().includes(q)
        )
    }, [estudiantes, busqueda])

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
                <p className="text-[14px] text-[#ba1a1a]">{error}</p>
                <button onClick={cargarDatos} className="text-[13px] text-[#d32f2f] hover:underline">Reintentar</button>
            </div>
        )
    }

    const total = (estudiantes?.disponibles?.length ?? 0) + (estudiantes?.en_equipo?.length ?? 0)

    return (
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px]">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <Link to={`/docente/cursos/${cursoId}`} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Curso</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="text-[#191c1d] font-medium">Estudiantes</span>
            </div>

            {/* Toast */}
            {toast && (
                <div className="mb-4 px-4 py-3 rounded-xl bg-[#e8f5e9] text-[#2e7d32] text-[13px] font-medium flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <circle cx="8" cy="8" r="6" /><path d="M5 8l2 2 4-4" />
                    </svg>
                    {toast}
                </div>
            )}

            {proyectos.length === 0 && (
                <div className="mb-4 px-4 py-3 rounded-xl bg-[#fff8e1] text-[#f57c00] text-[13px] font-medium flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <circle cx="8" cy="8" r="6" /><path d="M8 5v3M8 10.5v.5" />
                    </svg>
                    Este curso no tiene proyectos. Crea un proyecto antes de asignar estudiantes a equipos.
                </div>
            )}

            <div className="flex gap-5 items-start flex-col lg:flex-row">

                {/* Panel izquierdo: lista */}
                <div className="flex-1 bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden min-w-0">

                    <div className="px-5 pt-5 pb-4 border-b border-[#e1e3e4]">
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-[15px] font-bold text-[#191c1d]">Estudiantes del Curso</h2>
                            <span className="text-[12px] text-[#9ba7ae]">{total} en total</span>
                        </div>
                        <div className="relative">
                            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                <circle cx="6.5" cy="6.5" r="4" /><path d="M11 11l3 3" />
                            </svg>
                            <input
                                type="text"
                                value={busqueda}
                                onChange={e => setBusqueda(e.target.value)}
                                placeholder="Buscar por nombre o correo..."
                                className="w-full h-10 pl-9 pr-4 rounded-xl border border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-colors"
                            />
                        </div>
                    </div>

                    <div className="overflow-y-auto max-h-[calc(100vh-310px)]">

                        {/* Disponibles */}
                        {disponiblesFiltrados.length > 0 && (
                            <div>
                                <div className="px-5 pt-4 pb-2 flex items-center justify-between">
                                    <p className="text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase">
                                        Disponibles ({disponiblesFiltrados.length})
                                    </p>
                                    {seleccionados.size > 0 && (
                                        <button
                                            onClick={() => setSeleccionados(new Set())}
                                            className="text-[11px] text-[#9ba7ae] hover:text-[#4c616c] transition-colors">
                                            Limpiar selección
                                        </button>
                                    )}
                                </div>
                                {disponiblesFiltrados.map(est => {
                                    const checked = seleccionados.has(est.id)
                                    return (
                                        <label
                                            key={est.id}
                                            className={`flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors hover:bg-[#f8f9fa] ${checked ? 'bg-[#fff8f7]' : ''}`}>
                                            <input
                                                type="checkbox"
                                                checked={checked}
                                                onChange={() => toggleSeleccion(est.id)}
                                                className="w-4 h-4 rounded accent-[#d32f2f] flex-shrink-0"
                                            />
                                            <div
                                                className="w-9 h-9 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                                                style={{ backgroundColor: colorFor(est.id) }}>
                                                {iniciales(est.nombre, est.apellido)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{est.nombre} {est.apellido}</p>
                                                <p className="text-[12px] text-[#9ba7ae] truncate">{est.correo}</p>
                                            </div>
                                            <span className="flex items-center gap-1 text-[11px] font-semibold text-[#2e7d32] flex-shrink-0">
                                                <span className="w-1.5 h-1.5 rounded-full bg-[#2e7d32]" />
                                                DISPONIBLE
                                            </span>
                                        </label>
                                    )
                                })}
                            </div>
                        )}

                        {/* Ya en equipo */}
                        {enEquipoFiltrados.length > 0 && (
                            <div>
                                <p className="px-5 pt-4 pb-2 text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase">
                                    Ya en equipo ({enEquipoFiltrados.length})
                                </p>
                                {enEquipoFiltrados.map(est => (
                                    <div key={est.id} className="flex items-center gap-3 px-5 py-3 opacity-60">
                                        <div className="w-4 h-4 flex-shrink-0" />
                                        <div
                                            className="w-9 h-9 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                                            style={{ backgroundColor: colorFor(est.id) }}>
                                            {iniciales(est.nombre, est.apellido)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[13px] font-semibold text-[#191c1d] truncate">{est.nombre} {est.apellido}</p>
                                            <p className="text-[12px] text-[#9ba7ae] truncate">
                                                {est.equipos?.[0]?.equipo_nombre ?? ''} · {est.correo}
                                            </p>
                                        </div>
                                        <span className="flex items-center gap-1 text-[11px] font-semibold text-[#1976d2] flex-shrink-0">
                                            <span className="w-1.5 h-1.5 rounded-full bg-[#1976d2]" />
                                            EN EQUIPO
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {disponiblesFiltrados.length === 0 && enEquipoFiltrados.length === 0 && (
                            <p className="px-5 py-10 text-[13px] text-[#9ba7ae] text-center">
                                {busqueda ? `Sin resultados para "${busqueda}"` : 'No hay estudiantes registrados.'}
                            </p>
                        )}

                        <div className="h-4" />
                    </div>
                </div>

                {/* Panel derecho: acciones */}
                <div className="w-full lg:w-64 flex-shrink-0 flex flex-col gap-3">
                    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">

                        <div className="text-center mb-4">
                            <p className="text-[28px] font-bold text-[#191c1d] leading-none">
                                {seleccionados.size}
                            </p>
                            <p className="text-[12px] text-[#9ba7ae] mt-1">seleccionados</p>
                        </div>

                        <div className="mb-4">
                            <div className="flex items-center justify-between mb-1.5">
                                <span className="text-[12px] text-[#5b403d] font-medium">Disponibles</span>
                                <span className="text-[12px] font-bold text-[#191c1d]">
                                    {estudiantes?.disponibles?.length ?? 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-[12px] text-[#5b403d] font-medium">Ya en equipo</span>
                                <span className="text-[12px] font-bold text-[#191c1d]">
                                    {estudiantes?.en_equipo?.length ?? 0}
                                </span>
                            </div>
                        </div>

                        <button
                            onClick={() => setModalAbierto(true)}
                            disabled={seleccionados.size === 0 || proyectos.length === 0}
                            className="w-full h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-6 6s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z" />
                            </svg>
                            {seleccionados.size > 0
                                ? `Asignar ${seleccionados.size} estudiante${seleccionados.size !== 1 ? 's' : ''}`
                                : 'Asignar estudiantes'}
                        </button>
                    </div>

                    <div className="bg-[#f8f9fa] rounded-xl border border-[#e1e3e4] px-4 py-3">
                        <p className="text-[12px] text-[#5b403d] text-center leading-relaxed">
                            Un estudiante no puede pertenecer a más de un equipo en el mismo proyecto.
                        </p>
                    </div>
                </div>
            </div>

            {modalAbierto && (
                <ModalAsignar
                    estudiantesIds={[...seleccionados]}
                    proyectos={proyectos}
                    cursoId={cursoId}
                    onClose={() => setModalAbierto(false)}
                    onExito={handleExito}
                />
            )}
        </div>
    )
}
