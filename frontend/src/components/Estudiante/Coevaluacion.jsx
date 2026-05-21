import { useState, useEffect } from 'react'
import { useOutletContext } from 'react-router-dom'
import { rubricasApi } from '../../services/docenteApi'
import { coevaluacionApi } from '../../services/estudianteApi'

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

function IconPeers() {
    return (
        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="7" r="3" />
            <path d="M3 20a6 6 0 0112 0" />
            <circle cx="17" cy="8" r="2.5" />
            <path d="M17 14c2.5 0 4 1.5 4 4" />
        </svg>
    )
}

function IconCheck() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10l4 4 8-8" />
        </svg>
    )
}

// ── Tarjeta de criterio ───────────────────────────────────────────────────────

function CriterioCard({ criterio, seleccionado, onChange }) {
    const nivelesOrdenados = [...(criterio.niveles ?? [])].sort((a, b) => a.nivel - b.nivel)

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-4">
            <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                    <h3 className="text-[16px] font-bold text-[#191c1d]">{criterio.nombre}</h3>
                    {criterio.descripcion && (
                        <p className="text-[13px] text-[#9ba7ae] mt-0.5">{criterio.descripcion}</p>
                    )}
                </div>
                <span className="flex-shrink-0 text-[12px] font-bold text-[#d32f2f] bg-[#fff1f0] px-2.5 py-1 rounded-lg border border-[#ffdad6]">
                    {parseFloat(criterio.peso_porcentual)}% del Total
                </span>
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

// ── Vista de coevaluación ya enviada ──────────────────────────────────────────

function CoevaluacionEnviada({ coeval, companeroNombre }) {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-5">
            <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7]">
                    <IconCheck />
                    EVALUACIÓN COMPLETADA
                </span>
                <span className="text-[13px] text-[#9ba7ae]">
                    {new Date(coeval.fecha_registro).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' })}
                </span>
            </div>

            <h3 className="text-[16px] font-bold text-[#191c1d] mb-1">
                {companeroNombre}
            </h3>
            {coeval.rubrica_nombre && (
                <p className="text-[12px] text-[#9ba7ae] mb-3 italic">{coeval.rubrica_nombre}</p>
            )}

            {/* Puntuación */}
            <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-[#fff8e1] border border-[#ffe082] rounded-xl">
                    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-[#f9a825]">
                        <path d="M10 1l2.6 5.3 5.8.8-4.2 4.1 1 5.8L10 14.3l-5.2 2.7 1-5.8L1.6 7.1l5.8-.8z" />
                    </svg>
                    <span className="text-[18px] font-extrabold text-[#f9a825] leading-none">
                        {parseFloat(coeval.puntuacion_total).toFixed(1)}
                    </span>
                    <span className="text-[11px] font-semibold text-[#f9a825]">/ 100</span>
                </div>
            </div>

            {/* Detalles */}
            {coeval.detalles && coeval.detalles.length > 0 && (
                <div className="flex flex-col gap-2">
                    {coeval.detalles.map(d => (
                        <div key={d.id} className="flex items-center justify-between gap-3 py-2 border-b border-[#f0f2f3] last:border-0">
                            <div className="min-w-0">
                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{d.criterio_nombre}</p>
                                <p className="text-[11px] text-[#9ba7ae]">{d.nivel_etiqueta} · {d.puntos_obtenidos} pts</p>
                            </div>
                            <span className="flex-shrink-0 text-[12px] font-bold text-[#4c616c] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                                {parseFloat(d.peso_porcentual ?? 0)}%
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* Comentario */}
            {coeval.comentario && (
                <div className="mt-3 flex items-start gap-2 bg-[#f8f9fa] rounded-xl p-3">
                    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#9ba7ae]" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2 4a2 2 0 012-2h12a2 2 0 012 2v9a2 2 0 01-2 2H6l-4 3V4z" />
                    </svg>
                    <p className="text-[13px] text-[#4c616c] leading-relaxed">{coeval.comentario}</p>
                </div>
            )}
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function Coevaluacion() {
    const ctx = useOutletContext() ?? {}
    const { proyectoId, proyecto, companeros, selectedEvaluadoId, setSelectedEvaluadoId, recargarCompaneros } = ctx

    const [rubricas,    setRubricas]    = useState([])
    const [rubricaSel,  setRubricaSel]  = useState(null)
    const [misCoev,     setMisCoev]     = useState([])  // coevaluaciones que yo hice
    const [loading,     setLoading]     = useState(true)
    const [periodoError,setPeriodoError]= useState(false)

    // Form state
    const [selecciones, setSelecciones] = useState({})   // { criterioId: nivelId }
    const [comentario,  setComentario]  = useState('')
    const [guardando,   setGuardando]   = useState(false)
    const [error,       setError]       = useState('')

    useEffect(() => {
        if (proyectoId) cargar()
    }, [proyectoId])

    // Reset form when evaluado changes
    useEffect(() => {
        setSelecciones({})
        setComentario('')
        setError('')
    }, [selectedEvaluadoId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const [rubData, coevData] = await Promise.allSettled([
                rubricasApi.listar(proyectoId),
                coevaluacionApi.listar(proyectoId),
            ])

            const rubs = rubData.status === 'fulfilled'
                ? (Array.isArray(rubData.value) ? rubData.value : (rubData.value.results ?? []))
                : []
            setRubricas(rubs)
            if (rubs.length > 0) setRubricaSel(rubs[0])

            const coevs = coevData.status === 'fulfilled'
                ? (Array.isArray(coevData.value) ? coevData.value : (coevData.value.results ?? []))
                : []
            setMisCoev(coevs)
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
            if (nivel) {
                total += parseFloat(nivel.puntos) * parseFloat(criterio.peso_porcentual) / 100
            }
        }
        return total.toFixed(1)
    }

    const criterios = rubricaSel?.criterios ?? []
    const totalCriterios = criterios.length
    const evaluados = Object.keys(selecciones).filter(k => criterios.find(c => c.id === parseInt(k))).length
    const completo = evaluados === totalCriterios && totalCriterios > 0

    // Estadísticas de progreso general
    const totalCompaneros = companeros.length
    const evaluadosCount  = companeros.filter(c => c.yaEvaluado).length

    // Compañero seleccionado
    const companeroActual = companeros.find(c => c.id === selectedEvaluadoId)

    // ¿Ya evalué a este compañero?
    const coevExistente = misCoev.find(c => c.id_evaluado === selectedEvaluadoId)

    async function handleEnviar() {
        if (!rubricaSel || !completo || !selectedEvaluadoId) return
        setGuardando(true)
        setError('')
        try {
            const payload = {
                id_evaluado: selectedEvaluadoId,
                id_rubrica:  rubricaSel.id,
                comentario:  comentario.trim() || null,
                detalles: criterios.map(c => ({
                    id_criterio:          c.id,
                    id_nivel_seleccionado: selecciones[c.id],
                })),
            }
            const result = await coevaluacionApi.crear(proyectoId, payload)
            setMisCoev(prev => [...prev, result])
            // Recargar estado del layout para actualizar "yaEvaluado"
            if (recargarCompaneros) await recargarCompaneros()
            // Pasar al siguiente compañero sin evaluar
            const siguiente = companeros.find(c => !c.yaEvaluado && c.id !== selectedEvaluadoId)
            if (siguiente) setSelectedEvaluadoId?.(siguiente.id)
        } catch (err) {
            const detail = err?.data?.detail ?? err?.data?.non_field_errors?.[0]
            if (detail?.includes('periodo')) {
                setPeriodoError(true)
            } else {
                setError(detail ?? 'No se pudo enviar la coevaluación.')
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
                    <span>Cargando coevaluación...</span>
                </div>
            </div>
        )
    }

    // Sin rubricas
    if (rubricas.length === 0) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm">
                    <div className="w-16 h-16 rounded-2xl bg-[#f0f2f3] flex items-center justify-center mx-auto mb-4 text-[#9ba7ae]">
                        <IconPeers />
                    </div>
                    <p className="text-[16px] font-bold text-[#191c1d] mb-2">Sin rúbricas disponibles</p>
                    <p className="text-[13px] text-[#9ba7ae]">El docente aún no ha creado rúbricas para este proyecto.</p>
                </div>
            </div>
        )
    }

    // Sin compañeros
    if (companeros.length === 0) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm">
                    <div className="w-16 h-16 rounded-2xl bg-[#f0f2f3] flex items-center justify-center mx-auto mb-4 text-[#9ba7ae]">
                        <IconPeers />
                    </div>
                    <p className="text-[16px] font-bold text-[#191c1d] mb-2">Sin compañeros de equipo</p>
                    <p className="text-[13px] text-[#9ba7ae]">No hay compañeros a quienes evaluar en este proyecto.</p>
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
                    <p className="text-[13px] text-[#9ba7ae]">La coevaluación solo puede realizarse dentro del período académico activo.</p>
                </div>
            </div>
        )
    }

    // Sin compañero seleccionado
    if (!selectedEvaluadoId || !companeroActual) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center max-w-sm text-[#9ba7ae]">
                    <svg viewBox="0 0 48 48" fill="none" className="w-16 h-16 mx-auto mb-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="16" cy="14" r="6" />
                        <path d="M4 38a12 12 0 0124 0" />
                        <circle cx="32" cy="16" r="5" />
                        <path d="M32 28c5 0 8 2.5 8 7" />
                    </svg>
                    <p className="text-[15px] font-bold text-[#191c1d] mb-1">Selecciona un compañero</p>
                    <p className="text-[13px]">Elige a quién deseas evaluar desde la barra lateral.</p>
                </div>
            </div>
        )
    }

    // ── Formulario / Vista por compañero ──────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e3f2fd] text-[#1565c0] border border-[#90caf9] mb-3">
                    COEVALUACIÓN DE PARES
                </span>
                <h1 className="text-[24px] font-extrabold text-[#191c1d] tracking-tight leading-tight mb-1">
                    Coevaluación{proyecto?.nombre ? ` · ${proyecto.nombre}` : ''}
                </h1>
                <p className="text-[14px] text-[#4c616c] leading-relaxed max-w-2xl">
                    Evalúa a cada compañero de tu equipo de forma honesta y constructiva.
                    Tu retroalimentación contribuye al crecimiento colectivo del proyecto.
                </p>
            </div>

            {/* Progreso general */}
            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 mb-5 flex items-center gap-4">
                <div className="flex-1">
                    <div className="flex justify-between mb-1.5">
                        <span className="text-[12px] font-semibold text-[#4c616c]">Compañeros evaluados</span>
                        <span className="text-[12px] font-bold text-[#d32f2f]">{evaluadosCount}/{totalCompaneros}</span>
                    </div>
                    <div className="h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-[#d32f2f] rounded-full transition-all duration-300"
                            style={{ width: totalCompaneros ? `${(evaluadosCount / totalCompaneros) * 100}%` : '0%' }}
                        />
                    </div>
                </div>
                {evaluadosCount === totalCompaneros && totalCompaneros > 0 && (
                    <span className="flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7]">
                        <IconCheck />
                        ¡Todos evaluados!
                    </span>
                )}
            </div>

            {/* Nombre del compañero */}
            <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 rounded-full bg-[#ffdad6] flex items-center justify-center text-[14px] font-bold text-[#af101a] flex-shrink-0">
                    {companeroActual.nombre?.[0]?.toUpperCase() ?? '?'}
                </div>
                <div>
                    <h2 className="text-[18px] font-bold text-[#191c1d] leading-tight">
                        {companeroActual.nombre}
                    </h2>
                    <p className="text-[12px] text-[#9ba7ae]">Evaluando a este compañero</p>
                </div>
            </div>

            {/* Si ya fue evaluado, mostrar vista de solo lectura */}
            {coevExistente ? (
                <>
                    <CoevaluacionEnviada coeval={coevExistente} companeroNombre={companeroActual.nombre} />
                    <div className="text-center py-4">
                        <p className="text-[13px] text-[#9ba7ae]">
                            Ya evaluaste a este compañero. Selecciona otro desde el panel lateral.
                        </p>
                    </div>
                </>
            ) : (
                <>
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

                    {/* Barra de progreso de criterios */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 mb-5 flex items-center gap-4">
                        <div className="flex-1">
                            <div className="flex justify-between mb-1.5">
                                <span className="text-[12px] font-semibold text-[#4c616c]">Criterios evaluados</span>
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

                    {/* Comentario opcional */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 mb-5">
                        <h2 className="text-[16px] font-bold text-[#191c1d] mb-1 flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-xl bg-[#e3f2fd] flex items-center justify-center text-[#1565c0] flex-shrink-0">
                                <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M2 4a2 2 0 012-2h12a2 2 0 012 2v9a2 2 0 01-2 2H6l-4 3V4z" />
                                </svg>
                            </div>
                            Comentario (opcional)
                        </h2>
                        <p className="text-[13px] text-[#9ba7ae] mb-4 ml-[42px]">
                            Añade observaciones específicas sobre el desempeño de tu compañero.
                        </p>
                        <textarea
                            value={comentario}
                            onChange={e => setComentario(e.target.value)}
                            rows={4}
                            placeholder={`¿Algo específico que destacar sobre ${companeroActual.nombre}?`}
                            className="w-full px-4 py-3 bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl text-[14px] text-[#191c1d] placeholder-[#b0bec5] resize-y focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors leading-relaxed"
                        />
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
                            onClick={() => { setSelecciones({}); setComentario(''); setError('') }}
                            className="px-5 py-2.5 border-2 border-[#e1e3e4] text-[#4c616c] text-[13px] font-bold rounded-xl hover:bg-[#f0f2f3] transition-colors">
                            Limpiar
                        </button>
                        <button
                            onClick={handleEnviar}
                            disabled={!completo || guardando}
                            className="flex items-center gap-2 px-6 py-2.5 bg-[#d32f2f] text-white text-[13px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                            {guardando ? 'Enviando...' : `Evaluar a ${companeroActual.nombre.split(' ')[0]}`}
                            {!guardando && (
                                <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                    <path d="M3 8h10M9 4l4 4-4 4" />
                                </svg>
                            )}
                        </button>
                    </div>
                </>
            )}
        </div>
    )
}