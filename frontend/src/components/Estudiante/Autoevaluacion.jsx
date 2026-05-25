import { useState, useEffect } from 'react'
import { useOutletContext } from 'react-router-dom'
import { rubricasApi } from '../../services/docenteApi'
import { autoevaluacionApi } from '../../services/estudianteApi'

// ── Niveles visuales ──────────────────────────────────────────────────────────

const NIVEL_STYLES = {
    insuficiente: { bg: 'bg-[#ffebee]', border: 'border-[#ef9a9a]', text: 'text-[#c62828]', selBg: 'bg-[#ffebee]', selBorder: 'border-[#d32f2f]' },
    basico:       { bg: 'bg-[#fff8e1]', border: 'border-[#ffe082]', text: 'text-[#e65100]', selBg: 'bg-[#fff8e1]', selBorder: 'border-[#f9a825]' },
    satisfactorio:{ bg: 'bg-[#e3f2fd]', border: 'border-[#90caf9]', text: 'text-[#1565c0]', selBg: 'bg-[#e3f2fd]', selBorder: 'border-[#1565c0]' },
    excelente:    { bg: 'bg-[#e8f5e9]', border: 'border-[#a5d6a7]', text: 'text-[#2e7d32]', selBg: 'bg-[#e8f5e9]', selBorder: 'border-[#2e7d32]' },
}

const ETIQUETA_DISPLAY = {
    insuficiente: 'Insuficiente',
    basico:       'Básico',
    satisfactorio:'Satisfactorio',
    excelente:    'Excelente',
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function IconReflexion() {
    return (
        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 12h6M9 16h6M9 8h3" />
            <path d="M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
        </svg>
    )
}

// ── Tarjeta de criterio ───────────────────────────────────────────────────────

function CriterioCard({ criterio, seleccionado, onChange }) {
    // Ordenar niveles: insuficiente → basico → satisfactorio → excelente (nivel asc)
    const nivelesOrdenados = [...(criterio.niveles ?? [])].sort((a, b) => a.nivel - b.nivel)

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-4">
            <div className="mb-4">
                <h3 className="text-[16px] font-bold text-[#191c1d]">{criterio.nombre}</h3>
                {criterio.descripcion && (
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">{criterio.descripcion}</p>
                )}
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {nivelesOrdenados.map(nivel => {
                    const etq = nivel.etiqueta
                    const style = NIVEL_STYLES[etq] ?? NIVEL_STYLES.satisfactorio
                    const isSelected = seleccionado === nivel.id

                    return (
                        <button
                            key={nivel.id}
                            onClick={() => onChange(criterio.id, nivel.id)}
                            className={`relative text-left p-3.5 rounded-xl border-2 transition-all duration-150 ${
                                isSelected
                                    ? `${style.selBg} ${style.selBorder} shadow-md ring-2 ring-offset-1 ${style.selBorder.replace('border-', 'ring-')}`
                                    : `bg-[#fafafa] border-[#e1e3e4] hover:border-[#c8cdd0] hover:bg-[#f5f6f7]`
                            }`}>
                            <p className={`text-[12px] font-extrabold mb-1.5 ${isSelected ? style.text : 'text-[#4c616c]'}`}>
                                {ETIQUETA_DISPLAY[etq] ?? etq}
                            </p>
                            <p className={`text-[12px] leading-snug ${isSelected ? style.text : 'text-[#9ba7ae]'}`}>
                                {nivel.descripcion}
                            </p>
                            {isSelected && (
                                <span className={`absolute top-2 right-2 w-4 h-4 rounded-full ${style.selBorder.replace('border-', 'bg-')} flex items-center justify-center`}>
                                    <svg viewBox="0 0 12 12" fill="none" className="w-2.5 h-2.5" stroke="white" strokeWidth="2" strokeLinecap="round">
                                        <path d="M2 6l3 3 5-5" />
                                    </svg>
                                </span>
                            )}
                        </button>
                    )
                })}
            </div>
        </div>
    )
}

// ── Vista de autoevaluación ya enviada ────────────────────────────────────────

function AutoevaluacionEnviada({ auto }) {
    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            {/* Header */}
            <div className="mb-6">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7] mb-3">
                    ✓ AUTOEVALUACIÓN COMPLETADA
                </span>
                <h1 className="text-[24px] font-extrabold text-[#191c1d] tracking-tight leading-tight mb-1">
                    Mi Autoevaluación
                </h1>
                <p className="text-[13px] text-[#9ba7ae]">
                    Enviada el {new Date(auto.fecha_registro).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' })}
                    {auto.rubrica_nombre && ` · ${auto.rubrica_nombre}`}
                </p>
            </div>

            {/* Puntuación total */}
            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-5 flex items-center gap-6">
                <div className="text-center">
                    <p className="text-[40px] font-extrabold text-[#d32f2f] leading-none">
                        {parseFloat(auto.puntuacion_total).toFixed(1)}
                    </p>
                    <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px] mt-1">Tu puntuación</p>
                </div>
                {auto.evaluacion_docente && (
                    <>
                        <div className="w-px h-14 bg-[#e1e3e4]" />
                        <div className="text-center">
                            <p className="text-[40px] font-extrabold text-[#1565c0] leading-none">
                                {parseFloat(auto.evaluacion_docente.puntuacion_total).toFixed(1)}
                            </p>
                            <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px] mt-1">Evaluación docente</p>
                        </div>
                    </>
                )}
            </div>

            {/* Reflexión personal */}
            {auto.reflexion_texto && (
                <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-5">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-3 flex items-center gap-2">
                        <IconReflexion />
                        Tu Reflexión
                    </h2>
                    <p className="text-[14px] text-[#4c616c] leading-relaxed whitespace-pre-wrap">{auto.reflexion_texto}</p>
                </div>
            )}

            {/* Detalles por criterio */}
            {auto.detalles && auto.detalles.length > 0 && (
                <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Resultados por criterio</h2>
                    <div className="flex flex-col gap-3">
                        {auto.detalles.map(d => (
                            <div key={d.id} className="flex items-center justify-between gap-3 py-2 border-b border-[#f0f2f3] last:border-0">
                                <div className="min-w-0">
                                    <p className="text-[13px] font-semibold text-[#191c1d] truncate">{d.criterio_nombre}</p>
                                    <p className="text-[11px] text-[#9ba7ae]">{d.nivel_etiqueta}</p>
                                </div>
                                <span className="flex-shrink-0 text-[12px] font-bold text-[#4c616c] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                                    {parseFloat(d.puntos_obtenidos)} pts
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function Autoevaluacion() {
    const ctx = useOutletContext() ?? {}
    const { proyectoId, proyecto } = ctx

    const [rubricas,     setRubricas]     = useState([])
    const [rubricaSel,   setRubricaSel]   = useState(null)
    const [autoExistente,setAutoExistente]= useState(null)   // null = no existe / objeto = ya enviada
    const [loading,      setLoading]      = useState(true)
    const [periodoError, setPeriodoError] = useState(false)
    const [bloqueada,    setBloqueada]    = useState(false)  // docente aún no ha evaluado

    // Form state
    const [selecciones,  setSelecciones]  = useState({})   // { criterioId: nivelId }
    const [reflexion,    setReflexion]    = useState('')
    const [guardando,    setGuardando]    = useState(false)
    const [error,        setError]        = useState('')
    const [exito,        setExito]        = useState(false)

    useEffect(() => {
        if (proyectoId) cargar()
    }, [proyectoId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const [rubData, autoData, puedeData] = await Promise.allSettled([
                rubricasApi.listar(proyectoId),
                autoevaluacionApi.mia(proyectoId),
                autoevaluacionApi.puedeAutoevaluar(proyectoId),
            ])

            const rubs = rubData.status === 'fulfilled'
                ? (Array.isArray(rubData.value) ? rubData.value : (rubData.value.results ?? []))
                : []
            setRubricas(rubs)
            if (rubs.length > 0) setRubricaSel(rubs[0])

            if (autoData.status === 'fulfilled') {
                setAutoExistente(autoData.value)
            }

            if (puedeData.status === 'fulfilled' && puedeData.value.puede === false) {
                setBloqueada(true)
            }
        } catch { }
        finally { setLoading(false) }
    }

    function handleSeleccion(criterioId, nivelId) {
        setSelecciones(prev => ({ ...prev, [criterioId]: nivelId }))
    }

    function calcularTotal() {
        if (!rubricaSel) return 0
        let total = 0
        for (const criterio of (rubricaSel.criterios ?? [])) {
            const nivelId = selecciones[criterio.id]
            if (!nivelId) continue
            const nivel = (criterio.niveles ?? []).find(n => n.id === nivelId)
            if (nivel) total += parseFloat(nivel.puntos)
        }
        return total.toFixed(1)
    }

    const criterios = rubricaSel?.criterios ?? []
    const totalCriterios = criterios.length
    const evaluados = Object.keys(selecciones).filter(k => criterios.find(c => c.id === parseInt(k))).length
    const completo = evaluados === totalCriterios && totalCriterios > 0

    async function handleEnviar() {
        if (!rubricaSel || !completo) return
        if (!reflexion.trim()) {
            setError('La reflexión personal es obligatoria.')
            return
        }
        setGuardando(true)
        setError('')
        try {
            const payload = {
                id_rubrica: rubricaSel.id,
                reflexion_texto: reflexion.trim(),
                detalles: criterios.map(c => ({
                    id_criterio: c.id,
                    id_nivel_seleccionado: selecciones[c.id],
                })),
            }
            const result = await autoevaluacionApi.crear(proyectoId, payload)
            setAutoExistente(result)
            setExito(true)
        } catch (err) {
            const detail = err?.data?.detail ?? err?.data?.non_field_errors?.[0]
            if (detail?.includes('periodo')) {
                setPeriodoError(true)
            } else {
                setError(detail ?? 'No se pudo enviar la autoevaluación.')
            }
        } finally { setGuardando(false) }
    }

    // ── Loading ───────────────────────────────────────────────────────────────

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center text-[#9ba7ae] text-[14px]"
                style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="flex flex-col items-center gap-3">
                    <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Cargando autoevaluación...</span>
                </div>
            </div>
        )
    }

    // Ya enviada → vista de solo lectura
    if (autoExistente) return <AutoevaluacionEnviada auto={autoExistente} />

    // Sin rubricas
    if (rubricas.length === 0) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm">
                    <div className="w-16 h-16 rounded-2xl bg-[#f0f2f3] flex items-center justify-center mx-auto mb-4 text-[#9ba7ae]">
                        <IconReflexion />
                    </div>
                    <p className="text-[16px] font-bold text-[#191c1d] mb-2">Sin rúbricas disponibles</p>
                    <p className="text-[13px] text-[#9ba7ae]">El docente aún no ha creado rúbricas para este proyecto.</p>
                </div>
            </div>
        )
    }

    // Bloqueada: docente aún no ha evaluado
    if (bloqueada) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm">
                    <div className="w-14 h-14 rounded-2xl bg-[#fff8e1] flex items-center justify-center mx-auto mb-4">
                        <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 text-[#f9a825]" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
                        </svg>
                    </div>
                    <p className="text-[16px] font-bold text-[#191c1d] mb-2">Autoevaluación no disponible aún</p>
                    <p className="text-[13px] text-[#9ba7ae] leading-relaxed">
                        El docente debe calificar al menos un entregable con rúbrica antes de que puedas autoevaluarte.
                    </p>
                </div>
            </div>
        )
    }

    // Fuera de período
    if (periodoError) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm">
                    <p className="text-[16px] font-bold text-[#c62828] mb-2">Fuera del período de evaluación</p>
                    <p className="text-[13px] text-[#9ba7ae]">La autoevaluación solo puede realizarse dentro del período académico activo.</p>
                </div>
            </div>
        )
    }

    // ── Formulario ────────────────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e3f2fd] text-[#1565c0] border border-[#90caf9] mb-3">
                    PROCESO DE REFLEXIÓN
                </span>
                <h1 className="text-[24px] font-extrabold text-[#191c1d] tracking-tight leading-tight mb-1">
                    Mi Autoevaluación{proyecto?.nombre ? ` · ${proyecto.nombre}` : ''}
                </h1>
                <p className="text-[14px] text-[#4c616c] leading-relaxed max-w-2xl">
                    Tómate un momento para analizar honestamente tu desempeño. Esta no es solo una calificación,
                    es una herramienta para tu crecimiento profesional y académico.
                </p>
            </div>

            {/* Selector de rúbrica (si hay más de una) */}
            {rubricas.length > 1 && (
                <div className="mb-5">
                    <label className="block text-[12px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px] mb-2">
                        Seleccionar rúbrica
                    </label>
                    <select
                        value={rubricaSel?.id ?? ''}
                        onChange={e => {
                            const r = rubricas.find(r => r.id === parseInt(e.target.value))
                            setRubricaSel(r)
                            setSelecciones({})
                        }}
                        className="w-full sm:w-auto px-3 py-2 bg-white border border-[#e1e3e4] rounded-xl text-[13px] text-[#191c1d] font-medium focus:outline-none focus:border-[#d32f2f]">
                        {rubricas.map(r => <option key={r.id} value={r.id}>{r.nombre}</option>)}
                    </select>
                </div>
            )}

            {/* Barra de progreso */}
            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 mb-5 flex items-center gap-4">
                <div className="flex-1">
                    <div className="flex justify-between mb-1.5">
                        <span className="text-[12px] font-semibold text-[#4c616c]">Progreso</span>
                        <span className="text-[12px] font-bold text-[#d32f2f]">{evaluados}/{totalCriterios}</span>
                    </div>
                    <div className="h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-[#d32f2f] rounded-full transition-all duration-300"
                            style={{ width: totalCriterios ? `${(evaluados / totalCriterios) * 100}%` : '0%' }}
                        />
                    </div>
                </div>
                <div className="text-right flex-shrink-0">
                    <p className="text-[22px] font-extrabold text-[#d32f2f] leading-none">{calcularTotal()}</p>
                    <p className="text-[10px] text-[#9ba7ae] font-semibold uppercase">/ 100 pts</p>
                </div>
            </div>

            {/* Criterios */}
            {criterios.map(c => (
                <CriterioCard
                    key={c.id}
                    criterio={c}
                    seleccionado={selecciones[c.id]}
                    onChange={handleSeleccion}
                />
            ))}

            {/* Reflexión Personal */}
            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-5">
                <h2 className="text-[16px] font-bold text-[#191c1d] mb-1 flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-[#fff1f0] flex items-center justify-center text-[#d32f2f] flex-shrink-0">
                        <IconReflexion />
                    </div>
                    Reflexión Personal
                </h2>
                <p className="text-[13px] text-[#9ba7ae] mb-4 ml-[42px]">
                    Describe tus mayores aprendizajes, los retos que enfrentaste y cómo planeas mejorar.
                </p>
                <textarea
                    value={reflexion}
                    onChange={e => setReflexion(e.target.value)}
                    rows={6}
                    placeholder="Escribe aquí tu reflexión... ¿Qué descubriste sobre ti mismo en este proyecto?"
                    className="w-full px-4 py-3 bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl text-[14px] text-[#191c1d] placeholder-[#b0bec5] resize-y focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors leading-relaxed"
                />
                <p className="text-[11px] text-[#b0bec5] text-right mt-1.5 uppercase tracking-[0.6px] font-semibold">
                    Espacio para pensamiento profundo
                </p>
            </div>

            {/* Error */}
            {error && (
                <div className="mb-4 bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl px-4 py-3">
                    {error}
                </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 pb-4">
                <button
                    onClick={() => {
                        setSelecciones({})
                        setReflexion('')
                        setError('')
                    }}
                    className="px-5 py-2.5 border-2 border-[#e1e3e4] text-[#4c616c] text-[13px] font-bold rounded-xl hover:bg-[#f0f2f3] transition-colors">
                    Guardar Borrador
                </button>
                <button
                    onClick={handleEnviar}
                    disabled={!completo || guardando}
                    className="flex items-center gap-2 px-6 py-2.5 bg-[#d32f2f] text-white text-[13px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                    {guardando ? 'Enviando...' : 'Enviar Autoevaluación'}
                    {!guardando && (
                        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <path d="M3 8h10M9 4l4 4-4 4" />
                        </svg>
                    )}
                </button>
            </div>
        </div>
    )
}