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

function ModalRAP({ rap, onGuardar, onCancelar, totalActual }) {
    const esEdicion = !!rap
    const [form, setForm] = useState({
        nombre: rap?.nombre ?? '',
        descripcion: rap?.descripcion ?? '',
        porcentaje_evaluacion: rap?.porcentaje_evaluacion ?? '',
    })
    const [errores, setErrores] = useState({})
    const [guardando, setGuardando] = useState(false)

    function validar() {
        const e = {}
        if (!form.nombre.trim()) e.nombre = 'El nombre es obligatorio.'
        if (!form.descripcion.trim()) e.descripcion = 'La descripción es obligatoria.'
        if (!form.porcentaje_evaluacion || form.porcentaje_evaluacion <= 0 || form.porcentaje_evaluacion > 100) {
            e.porcentaje_evaluacion = 'El porcentaje debe estar entre 1 y 100.'
        }

        // Validar que el total no exceda 100
        const porcentajeActual = parseFloat(rap?.porcentaje_evaluacion ?? 0)
        const porcentajeNuevo = parseFloat(form.porcentaje_evaluacion)
        const totalSinEste = totalActual - porcentajeActual
        if (totalSinEste + porcentajeNuevo > 100) {
            e.porcentaje_evaluacion = `El total excedería 100% (actual: ${totalSinEste}%)`
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

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden" onClick={e => e.stopPropagation()}>

                <div className="p-6 border-b border-[#e1e3e4]">
                    <h2 className="text-[19px] font-bold text-[#191c1d]">{esEdicion ? 'Editar RAP' : 'Nuevo Resultado de Aprendizaje'}</h2>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">Define los indicadores de desempeño que los estudiantes deben alcanzar</p>
                </div>

                <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto">

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Código del RAP</label>
                        <input type="text" value={form.nombre}
                            onChange={e => { setForm(f => ({ ...f, nombre: e.target.value.toUpperCase() })); setErrores(e => ({ ...e, nombre: '' })) }}
                            placeholder="ej: RAP-001"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.nombre ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción del resultado de aprendizaje</label>
                        <textarea value={form.descripcion}
                            onChange={e => { setForm(f => ({ ...f, descripcion: e.target.value })); setErrores(e => ({ ...e, descripcion: '' })) }}
                            placeholder="ej: Analiza conjuntos de datos masivos utilizando algoritmos de regresión..."
                            rows={3}
                            className={`px-4 py-3 rounded-xl border-2 text-[14px] outline-none transition-all resize-none ${errores.descripcion ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.descripcion && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.descripcion}</p>}
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-semibold text-[#191c1d] pl-1">Porcentaje de evaluación (%)</label>
                        <input type="number" min="1" max="100" value={form.porcentaje_evaluacion}
                            onChange={e => { setForm(f => ({ ...f, porcentaje_evaluacion: e.target.value })); setErrores(e => ({ ...e, porcentaje_evaluacion: '' })) }}
                            placeholder="20"
                            className={`h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all ${errores.porcentaje_evaluacion ? 'border-[#ba1a1a] bg-[#fff8f7]' : 'border-[#e1e3e4] focus:border-[#d32f2f] bg-white'}`}
                        />
                        {errores.porcentaje_evaluacion && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.porcentaje_evaluacion}</p>}
                    </div>
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
                            : esEdicion ? 'Guardar cambios' : 'Crear RAP'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default function RAPsProyecto() {
    const { proyectoId } = useParams()
    const location = useLocation()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre
    const [raps, setRaps] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalRAP, setModalRAP] = useState(false)
    const [rapEditando, setRapEditando] = useState(null)
    const [eliminando, setEliminando] = useState(null)

    useEffect(() => { cargarRAPs() }, [proyectoId])

    async function cargarRAPs() {
        setLoading(true)
        try {
            const data = await proyectosApi.listarRAPs(proyectoId)
            const lista = data.results ?? data
            setRaps(lista)
        } catch (err) {
            console.error('Error cargando RAPs:', err)
            setRaps([])
        } finally {
            setLoading(false)
        }
    }

    async function handleGuardarRAP(formData) {
        try {
            if (rapEditando) {
                await proyectosApi.editarRAP(proyectoId, rapEditando.id, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    porcentaje_evaluacion: parseFloat(formData.porcentaje_evaluacion),
                    orden: rapEditando.orden,
                })
            } else {
                await proyectosApi.crearRAP(proyectoId, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    porcentaje_evaluacion: parseFloat(formData.porcentaje_evaluacion),
                    orden: raps.length + 1,
                })
            }
            setModalRAP(false)
            setRapEditando(null)
            cargarRAPs()
        } catch (err) {
            console.error('Error guardando RAP:', err)
            throw err
        }
    }

    async function handleEliminar(id) {
        if (!window.confirm('¿Eliminar este RAP? Esta acción no se puede deshacer.')) return
        setEliminando(id)
        try {
            await proyectosApi.eliminarRAP(proyectoId, id)
            cargarRAPs()
        } catch (err) {
            console.error('Error eliminando RAP:', err)
            alert('No se pudo eliminar el RAP.')
        } finally {
            setEliminando(null)
        }
    }

    const totalPorcentaje = raps.reduce((sum, r) => sum + (r.porcentaje_evaluacion ?? 0), 0)
    const porcentajeRestante = 100 - totalPorcentaje

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
                    <h1 className="text-[24px] font-bold text-[#191c1d] leading-tight mb-1">Resultados de Aprendizaje</h1>
                    <p className="text-[13px] text-[#9ba7ae]">
                        Define los indicadores de desempeño que los estudiantes deben alcanzar al finalizar el módulo de investigación.
                    </p>
                </div>
                <button
                    onClick={() => setModalRAP(true)}
                    disabled={totalPorcentaje >= 100}
                    className="h-11 px-5 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed">
                    <IconPlus />
                    Agregar Resultado de Aprendizaje
                </button>
            </div>

            {/* Indicador de porcentaje */}
            <div className="mb-6 bg-white rounded-2xl border border-[#e1e3e4] p-5">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-[13px] font-semibold text-[#191c1d]">Total asignado</span>
                    <span className={`text-[15px] font-bold ${totalPorcentaje === 100 ? 'text-[#2e7d32]' : totalPorcentaje > 100 ? 'text-[#ba1a1a]' : 'text-[#4c616c]'}`}>
                        {totalPorcentaje}%
                    </span>
                </div>
                <div className="w-full h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
                    <div
                        className={`h-full transition-all duration-300 ${totalPorcentaje === 100 ? 'bg-[#2e7d32]' : totalPorcentaje > 100 ? 'bg-[#ba1a1a]' : 'bg-[#d32f2f]'}`}
                        style={{ width: `${Math.min(totalPorcentaje, 100)}%` }}
                    />
                </div>
                {totalPorcentaje !== 100 && (
                    <p className="text-[12px] text-[#9ba7ae] mt-2">
                        {totalPorcentaje > 100
                            ? `Excede en ${totalPorcentaje - 100}%. Ajusta los porcentajes.`
                            : `Restante: ${porcentajeRestante}%`}
                    </p>
                )}
            </div>

            {/* Tabla de RAPs */}
            {raps.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#fdf6f0] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#f57c00]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="5" y="2" width="14" height="3" rx="1" /><rect x="3" y="4" width="18" height="16" rx="2" />
                            <path d="M7 10h10M7 14h6" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">No hay RAPs aún</h3>
                    <p className="text-[13px] text-[#9ba7ae] mb-4">Crea el primer resultado de aprendizaje para este proyecto</p>
                    <button
                        onClick={() => setModalRAP(true)}
                        className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors">
                        <IconPlus />
                        Crear primer RAP
                    </button>
                </div>
            ) : (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                <th className="text-left px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Código</th>
                                <th className="text-left px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Descripción</th>
                                <th className="text-center px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Competencia</th>
                                <th className="text-center px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">%</th>
                                <th className="text-right px-4 py-3 text-[12px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {raps.map(rap => (
                                <tr key={rap.id} className="border-b border-[#e1e3e4] last:border-0 hover:bg-[#fafbfb] transition-colors">
                                    <td className="px-4 py-3.5">
                                        <span className="inline-block px-2.5 py-1 rounded-md bg-[#ffdad6] text-[#af101a] text-[12px] font-bold">
                                            {rap.nombre}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <p className="text-[14px] text-[#191c1d] leading-relaxed line-clamp-2">{rap.descripcion}</p>
                                    </td>
                                    <td className="px-4 py-3.5 text-center">
                                        <span className="inline-block px-3 py-1 rounded-full bg-[#e3f2fd] text-[#1565c0] text-[11px] font-semibold">
                                            Pensamiento Analítico
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 text-center">
                                        <span className="text-[14px] font-bold text-[#191c1d]">{rap.porcentaje_evaluacion}%</span>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <div className="flex items-center justify-end gap-1">
                                            <button
                                                onClick={() => { setRapEditando(rap); setModalRAP(true) }}
                                                className="w-8 h-8 rounded-lg hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"
                                                title="Editar">
                                                <IconEdit />
                                            </button>
                                            <button
                                                onClick={() => handleEliminar(rap.id)}
                                                disabled={eliminando === rap.id}
                                                className="w-8 h-8 rounded-lg hover:bg-[#fff1f0] flex items-center justify-center transition-colors disabled:opacity-50"
                                                title="Eliminar">
                                                <IconTrash />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    <div className="p-4 bg-[#f8f9fa] border-t border-[#e1e3e4] text-center">
                        <p className="text-[12px] text-[#9ba7ae]">
                            Mostrando {raps.length} resultado{raps.length !== 1 ? 's' : ''} de aprendizaje
                        </p>
                    </div>
                </div>
            )}

            {/* Nota informativa */}
            <div className="mt-6 bg-[#e8f5e9] border border-[#a5d6a7] rounded-xl p-4 flex gap-3">
                <svg className="w-5 h-5 text-[#2e7d32] flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" />
                </svg>
                <div>
                    <h3 className="text-[13px] font-bold text-[#2e7d32] mb-1">Nota de Calidad</h3>
                    <p className="text-[12px] text-[#2e7d32] leading-relaxed">
                        Asegúrese de que cada resultado de aprendizaje sea medible y utilice verbos de acción según la Taxonomía de Bloom.
                    </p>
                </div>
            </div>

            {/* Modal */}
            {modalRAP && (
                <ModalRAP
                    rap={rapEditando}
                    onGuardar={handleGuardarRAP}
                    onCancelar={() => { setModalRAP(false); setRapEditando(null) }}
                    totalActual={totalPorcentaje}
                />
            )}
        </div>
    )
}