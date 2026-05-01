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

function IconSave() {
    return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M13 2H3a1 1 0 00-1 1v10a1 1 0 001 1h10a1 1 0 001-1V3a1 1 0 00-1-1zM11 2v4H5V2M10 14v-4H6v4" /></svg>
}

function IconX() {
    return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 4l8 8M12 4l-8 8" /></svg>
}

function FormObjetivo({ descripcion, onChange, onGuardar, onCancelar, placeholder }) {
    return (
        <div className="flex flex-col gap-3">
            <textarea
                value={descripcion}
                onChange={e => onChange(e.target.value)}
                placeholder={placeholder}
                rows={2}
                autoFocus
                className="w-full px-3 py-2 rounded-lg border-2 border-[#d32f2f] text-[14px] outline-none focus:border-[#af101a] transition-all resize-none"
            />
            <div className="flex gap-2">
                <button onClick={onGuardar}
                    className="h-8 px-3 rounded-lg bg-[#d32f2f] text-white text-[13px] font-semibold hover:bg-[#af101a] transition-colors flex items-center gap-1.5">
                    <IconSave />Guardar
                </button>
                <button onClick={onCancelar}
                    className="h-8 px-3 rounded-lg border-2 border-[#e1e3e4] text-[#4c616c] text-[13px] font-semibold hover:bg-[#f0f2f3] transition-colors flex items-center gap-1.5">
                    <IconX />Cancelar
                </button>
            </div>
        </div>
    )
}

export default function ObjetivosProyecto() {
    const { proyectoId } = useParams()
    const location = useLocation()
    const cursoId = location.state?.cursoId
    const cursoNombre = location.state?.cursoNombre
    const proyectoNombre = location.state?.nombre

    const [objetivos, setObjetivos] = useState([])
    const [loading, setLoading] = useState(true)
    const [eliminando, setEliminando] = useState(null)

    const [mostrandoFormGeneral, setMostrandoFormGeneral] = useState(false)
    const [textoGeneral, setTextoGeneral] = useState('')

    const [mostrandoFormEspecifico, setMostrandoFormEspecifico] = useState(false)
    const [textoEspecifico, setTextoEspecifico] = useState('')

    const [editando, setEditando] = useState(null)

    useEffect(() => { cargarObjetivos() }, [proyectoId])

    async function cargarObjetivos() {
        setLoading(true)
        try {
            const data = await proyectosApi.listarObjetivos(proyectoId)
            setObjetivos(data.results ?? data)
        } catch (err) {
            console.error('Error cargando objetivos:', err)
            setObjetivos([])
        } finally {
            setLoading(false)
        }
    }

    async function handleCrear(tipo, descripcion, resetForm) {
        if (!descripcion.trim()) return
        const lista = objetivos.filter(o => o.tipo === tipo)
        try {
            await proyectosApi.crearObjetivo(proyectoId, {
                descripcion: descripcion.trim(),
                tipo,
                orden: lista.length + 1,
            })
            resetForm()
            cargarObjetivos()
        } catch (err) {
            console.error('Error creando objetivo:', err)
            alert('No se pudo crear el objetivo.')
        }
    }

    async function handleGuardarEdicion() {
        if (!editando?.descripcion.trim()) return
        try {
            await proyectosApi.editarObjetivo(proyectoId, editando.id, {
                descripcion: editando.descripcion,
                tipo: editando.tipo,
                orden: editando.orden,
            })
            setEditando(null)
            cargarObjetivos()
        } catch (err) {
            console.error('Error editando objetivo:', err)
            alert('No se pudo editar el objetivo.')
        }
    }

    async function handleEliminar(id) {
        if (!window.confirm('¿Eliminar este objetivo? Esta acción no se puede deshacer.')) return
        setEliminando(id)
        try {
            await proyectosApi.eliminarObjetivo(proyectoId, id)
            cargarObjetivos()
        } catch (err) {
            console.error('Error eliminando objetivo:', err)
            alert('No se pudo eliminar el objetivo.')
        } finally {
            setEliminando(null)
        }
    }

    const objetivoGeneral = objetivos.find(o => o.tipo === 'general') ?? null
    const objetivosEspecificos = objetivos.filter(o => o.tipo === 'especifico')

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
            <div className="mb-6">
                <h1 className="text-[24px] font-bold text-[#191c1d] leading-tight mb-1">Objetivos del Proyecto</h1>
                <p className="text-[13px] text-[#9ba7ae]">
                    Define el objetivo general y los objetivos específicos de tu proyecto de investigación.
                </p>
            </div>

            {/* ── Objetivo General ── */}
            <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-[#d32f2f] flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-white" viewBox="0 0 16 16" fill="currentColor">
                            <circle cx="8" cy="8" r="7" /><circle cx="8" cy="8" r="4" fill="white" /><circle cx="8" cy="8" r="1.5" fill="currentColor" />
                        </svg>
                    </div>
                    <h2 className="text-[17px] font-bold text-[#191c1d]">Objetivo General</h2>
                    {!objetivoGeneral && !mostrandoFormGeneral && (
                        <button
                            onClick={() => setMostrandoFormGeneral(true)}
                            className="ml-auto h-9 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors flex items-center gap-2">
                            <IconPlus />
                            Agregar
                        </button>
                    )}
                </div>

                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    {mostrandoFormGeneral && (
                        <FormObjetivo
                            descripcion={textoGeneral}
                            onChange={setTextoGeneral}
                            placeholder="ej: Desarrollar un marco analítico integral para evaluar..."
                            onGuardar={() => handleCrear('general', textoGeneral, () => { setTextoGeneral(''); setMostrandoFormGeneral(false) })}
                            onCancelar={() => { setMostrandoFormGeneral(false); setTextoGeneral('') }}
                        />
                    )}

                    {!mostrandoFormGeneral && !objetivoGeneral && (
                        <div className="text-center py-4">
                            <p className="text-[13px] text-[#9ba7ae] mb-3">No hay un objetivo general definido</p>
                            <button
                                onClick={() => setMostrandoFormGeneral(true)}
                                className="inline-flex items-center gap-2 h-9 px-4 rounded-xl border-2 border-[#d32f2f] text-[#d32f2f] font-semibold text-[13px] hover:bg-[#fdf0ef] transition-colors">
                                <IconPlus />
                                Crear objetivo general
                            </button>
                        </div>
                    )}

                    {objetivoGeneral && !mostrandoFormGeneral && (
                        editando?.id === objetivoGeneral.id ? (
                            <FormObjetivo
                                descripcion={editando.descripcion}
                                onChange={val => setEditando(e => ({ ...e, descripcion: val }))}
                                placeholder=""
                                onGuardar={handleGuardarEdicion}
                                onCancelar={() => setEditando(null)}
                            />
                        ) : (
                            <div className="flex items-start gap-3 group">
                                <div className="w-2 h-2 rounded-full bg-[#d32f2f] mt-2 flex-shrink-0" />
                                <p className="flex-1 text-[14px] text-[#191c1d] leading-relaxed">{objetivoGeneral.descripcion}</p>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button onClick={() => setEditando({ ...objetivoGeneral })}
                                        className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"
                                        title="Editar">
                                        <IconEdit />
                                    </button>
                                    <button onClick={() => handleEliminar(objetivoGeneral.id)}
                                        disabled={eliminando === objetivoGeneral.id}
                                        className="w-7 h-7 rounded-lg text-[#ba1a1a] hover:bg-[#ffdad6] flex items-center justify-center transition-colors disabled:opacity-50"
                                        title="Eliminar">
                                        <IconTrash />
                                    </button>
                                </div>
                            </div>
                        )
                    )}
                </div>
            </div>

            {/* ── Objetivos Específicos ── */}
            <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-[#1976d2] flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-white" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M2 4h12M2 8h8M2 12h5" />
                        </svg>
                    </div>
                    <h2 className="text-[17px] font-bold text-[#191c1d]">Objetivos Específicos</h2>
                    <span className="text-[12px] text-[#9ba7ae] font-medium">({objetivosEspecificos.length})</span>
                    {!mostrandoFormEspecifico && (
                        <button
                            onClick={() => setMostrandoFormEspecifico(true)}
                            className="ml-auto h-9 px-4 rounded-xl bg-[#1976d2] text-white font-semibold text-[13px] hover:bg-[#1565c0] transition-colors flex items-center gap-2">
                            <IconPlus />
                            Agregar
                        </button>
                    )}
                </div>

                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    {mostrandoFormEspecifico && (
                        <div className="mb-4 pb-4 border-b border-[#e1e3e4]">
                            <FormObjetivo
                                descripcion={textoEspecifico}
                                onChange={setTextoEspecifico}
                                placeholder="ej: Identificar los principales factores que influyen en..."
                                onGuardar={() => handleCrear('especifico', textoEspecifico, () => { setTextoEspecifico(''); setMostrandoFormEspecifico(false) })}
                                onCancelar={() => { setMostrandoFormEspecifico(false); setTextoEspecifico('') }}
                            />
                        </div>
                    )}

                    {objetivosEspecificos.length === 0 && !mostrandoFormEspecifico && (
                        <div className="text-center py-4">
                            <p className="text-[13px] text-[#9ba7ae] mb-3">No hay objetivos específicos definidos</p>
                            <button
                                onClick={() => setMostrandoFormEspecifico(true)}
                                className="inline-flex items-center gap-2 h-9 px-4 rounded-xl border-2 border-[#1976d2] text-[#1976d2] font-semibold text-[13px] hover:bg-[#e3f2fd] transition-colors">
                                <IconPlus />
                                Crear primer objetivo específico
                            </button>
                        </div>
                    )}

                    <div className="space-y-3">
                        {objetivosEspecificos.map((obj, idx) => (
                            <div key={obj.id} className="flex items-start gap-3 group">
                                <span className="w-5 h-5 rounded-full bg-[#e3f2fd] text-[#1565c0] text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                                    {idx + 1}
                                </span>
                                {editando?.id === obj.id ? (
                                    <div className="flex-1">
                                        <FormObjetivo
                                            descripcion={editando.descripcion}
                                            onChange={val => setEditando(e => ({ ...e, descripcion: val }))}
                                            placeholder=""
                                            onGuardar={handleGuardarEdicion}
                                            onCancelar={() => setEditando(null)}
                                        />
                                    </div>
                                ) : (
                                    <>
                                        <p className="flex-1 text-[14px] text-[#191c1d] leading-relaxed">{obj.descripcion}</p>
                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => setEditando({ ...obj })}
                                                className="w-7 h-7 rounded-lg text-[#4c616c] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"
                                                title="Editar">
                                                <IconEdit />
                                            </button>
                                            <button onClick={() => handleEliminar(obj.id)}
                                                disabled={eliminando === obj.id}
                                                className="w-7 h-7 rounded-lg text-[#ba1a1a] hover:bg-[#ffdad6] flex items-center justify-center transition-colors disabled:opacity-50"
                                                title="Eliminar">
                                                <IconTrash />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Nota informativa */}
            <div className="bg-[#e3f2fd] border border-[#90caf9] rounded-xl p-4 flex gap-3">
                <svg className="w-5 h-5 text-[#1565c0] flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" />
                </svg>
                <div>
                    <h3 className="text-[13px] font-bold text-[#1565c0] mb-1">Consejo Académico</h3>
                    <p className="text-[12px] text-[#1565c0] leading-relaxed">
                        Los objetivos deben ser específicos, medibles, alcanzables, relevantes y con tiempo definido (Metodología SMART). El objetivo general expresa el propósito global; los específicos desglosan las acciones concretas para alcanzarlo.
                    </p>
                </div>
            </div>
        </div>
    )
}