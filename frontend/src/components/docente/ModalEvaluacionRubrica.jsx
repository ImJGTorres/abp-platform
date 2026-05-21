import { useState, useEffect } from 'react'
import { evaluacionesApi } from '../../services/docenteApi'

// ── Configuración de niveles (orden visual: mayor a menor) ────────────────────
const NIVELES_META = [
    { etiqueta: 'excelente',     label: 'Excelente',     color: '#2e7d32', bg: '#f1f8e9' },
    { etiqueta: 'satisfactorio', label: 'Satisfactorio', color: '#1565c0', bg: '#e3f2fd' },
    { etiqueta: 'basico',        label: 'Básico',        color: '#e65100', bg: '#fff3e0' },
    { etiqueta: 'insuficiente',  label: 'Insuficiente',  color: '#c62828', bg: '#ffebee' },
]

// ── Icono rúbrica ─────────────────────────────────────────────────────────────
function IconRubricSave() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="14" height="14" rx="2" />
            <path d="M7 3v5h6V3" /><path d="M5 13h10" />
        </svg>
    )
}

function IconFile() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 2h8l4 4v12a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" />
            <path d="M14 2v4h4" />
        </svg>
    )
}

// ── Helper: ordena los niveles de un criterio de mayor a menor (4→1) ──────────
function ordenarNiveles(niveles) {
    return [...(niveles ?? [])].sort((a, b) => b.nivel - a.nivel)
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ModalEvaluacionRubrica({ entregable, rubricas, onClose, onGuardado }) {
    const [rubricaSelId, setRubricaSelId] = useState(rubricas[0]?.id ?? null)
    const [selecciones,  setSelecciones]  = useState({}) // { [criterioId]: nivelId }
    const [comentario,   setComentario]   = useState('')
    const [guardando,    setGuardando]    = useState(false)
    const [error,        setError]        = useState('')

    // Rubrica activa con sus criterios y niveles ordenados
    const rubrica = rubricas.find(r => r.id === rubricaSelId) ?? null
    const criterios = (rubrica?.criterios ?? []).map(c => ({
        ...c,
        nivelesOrdenados: ordenarNiveles(c.niveles),
    }))

    // Columnas de encabezado — niveles del primer criterio (más alto al más bajo)
    // Si no hay criterios, usa los metadatos globales
    const columnasHeader = criterios[0]?.nivelesOrdenados
        ?? NIVELES_META.map((m, i) => ({ id: i, etiqueta: m.etiqueta, puntos: [100, 75, 50, 0][i] }))

    // Reiniciar selecciones al cambiar rúbrica
    useEffect(() => { setSelecciones({}); setError('') }, [rubricaSelId])

    // ── Cálculos ──────────────────────────────────────────────────────────────

    const puntuacionTotal = criterios.reduce((sum, c) => {
        const nv = c.nivelesOrdenados.find(n => n.id === selecciones[c.id])
        return nv ? sum + parseFloat(nv.puntos) * parseFloat(c.peso_porcentual) / 100 : sum
    }, 0)

    const puntuacionMax = criterios.reduce((sum, c) => {
        const maxPts = c.nivelesOrdenados.reduce((m, n) => Math.max(m, parseFloat(n.puntos)), 0)
        return sum + maxPts * parseFloat(c.peso_porcentual) / 100
    }, 0)

    const criteriosSeleccionados = criterios.filter(c => !!selecciones[c.id]).length
    const todoSeleccionado = criterios.length > 0 && criteriosSeleccionados === criterios.length
    const progresoPct = criterios.length > 0 ? (criteriosSeleccionados / criterios.length) * 100 : 0

    // ── Guardar ───────────────────────────────────────────────────────────────

    async function guardar() {
        if (!rubrica || !todoSeleccionado || guardando) return
        setGuardando(true)
        setError('')
        try {
            await evaluacionesApi.crear(entregable.id, {
                id_rubrica:         rubrica.id,
                comentario_general: comentario.trim() || null,
                calificaciones:     criterios.map(c => ({
                    id_criterio:           c.id,
                    id_nivel_seleccionado: selecciones[c.id],
                    comentario_criterio:   '',
                })),
            })
            onGuardado()
        } catch (e) {
            const d = e?.data
            const detail = d?.detail ?? d?.calificaciones ?? d?.id_rubrica
                ?? (typeof d === 'object' ? JSON.stringify(d) : d)
                ?? 'Error al guardar la evaluación.'
            setError(typeof detail === 'string' ? detail : JSON.stringify(detail))
        } finally {
            setGuardando(false)
        }
    }

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        // Sin onClick en el overlay — el modal sólo cierra con Cancelar
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            style={{ fontFamily: "'Manrope', sans-serif" }}
        >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[92vh] flex flex-col">

                {/* ── Cabecera ─────────────────────────────────────────────── */}
                <div className="px-6 py-4 border-b border-[#e1e3e4] flex-shrink-0">
                    <p className="text-[18px] font-extrabold text-[#d32f2f] tracking-tight">
                        Evaluar Entregable
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5 text-[#9ba7ae]">
                        <IconFile />
                        <p className="text-[13px] italic">{entregable.titulo}</p>
                    </div>
                </div>

                {/* ── Cuerpo scrolleable ───────────────────────────────────── */}
                <div className="flex-1 overflow-y-auto">

                    {rubricas.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 text-[#9ba7ae]">
                            <p className="text-[14px] font-semibold mb-1">Sin rúbricas disponibles</p>
                            <p className="text-[13px]">Crea una rúbrica en la sección de Rúbricas para poder evaluar.</p>
                        </div>
                    ) : (
                        <>
                            {/* Selector de rúbrica (sólo si hay más de una) */}
                            {rubricas.length > 1 && (
                                <div className="px-6 pt-4 pb-2">
                                    <label className="text-[11px] font-bold uppercase tracking-[0.7px] text-[#6b7b83] block mb-1.5">
                                        Rúbrica de evaluación
                                    </label>
                                    <select
                                        value={rubricaSelId ?? ''}
                                        onChange={e => setRubricaSelId(Number(e.target.value))}
                                        className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] text-[#191c1d] bg-[#f8f9fa] focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors"
                                    >
                                        {rubricas.map(r => (
                                            <option key={r.id} value={r.id}>{r.nombre}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {/* Progreso de selección */}
                            {criterios.length > 0 && (
                                <div className="px-6 pt-3 pb-1">
                                    <div className="flex items-center justify-between mb-1">
                                        <p className="text-[11px] font-semibold text-[#9ba7ae]">
                                            {criteriosSeleccionados} de {criterios.length} criterios evaluados
                                        </p>
                                        {!todoSeleccionado && (
                                            <p className="text-[11px] text-[#e65100]">
                                                Selecciona un nivel para cada criterio
                                            </p>
                                        )}
                                    </div>
                                    <div className="h-1.5 bg-[#f0f2f3] rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-[#d32f2f] rounded-full transition-all duration-300"
                                            style={{ width: `${progresoPct}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* ── Tabla de criterios ────────────────────────── */}
                            {criterios.length > 0 && (
                                <div className="overflow-x-auto px-6 pt-3 pb-2">
                                    <table className="w-full min-w-[560px] border-collapse">
                                        <thead>
                                            <tr className="border-b-2 border-[#e1e3e4]">
                                                <th className="text-left py-3 pr-4 text-[11px] font-bold uppercase tracking-[0.7px] text-[#6b7b83] w-[240px]">
                                                    Criterios de Evaluación
                                                </th>
                                                {columnasHeader.map(nv => {
                                                    const meta = NIVELES_META.find(m => m.etiqueta === nv.etiqueta)
                                                    return (
                                                        <th key={nv.id} className="text-center py-3 px-3 text-[11px] font-bold uppercase tracking-[0.6px]"
                                                            style={{ color: meta?.color ?? '#6b7b83' }}>
                                                            {meta?.label ?? nv.etiqueta}
                                                            <br />
                                                            <span className="text-[10px] font-semibold opacity-70 normal-case tracking-normal">
                                                                ({nv.puntos} pts)
                                                            </span>
                                                        </th>
                                                    )
                                                })}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {criterios.map((c, idx) => {
                                                const selNivelId = selecciones[c.id]
                                                return (
                                                    <tr
                                                        key={c.id}
                                                        className={`border-b border-[#f0f2f3] last:border-0 transition-colors ${idx % 2 === 1 ? 'bg-[#fafafa]' : ''}`}
                                                    >
                                                        {/* Criterio: nombre + descripción */}
                                                        <td className="py-4 pr-4 align-top">
                                                            <p className="text-[14px] font-bold text-[#191c1d] leading-snug">
                                                                {c.nombre}
                                                            </p>
                                                            {c.descripcion && (
                                                                <p className="text-[12px] text-[#6b7b83] mt-0.5 leading-snug">
                                                                    {c.descripcion}
                                                                </p>
                                                            )}
                                                            <p className="text-[10px] font-bold text-[#9ba7ae] mt-1 uppercase tracking-wide">
                                                                Peso: {c.peso_porcentual}%
                                                            </p>
                                                        </td>

                                                        {/* Radio por nivel */}
                                                        {c.nivelesOrdenados.map(nv => {
                                                            const meta = NIVELES_META.find(m => m.etiqueta === nv.etiqueta)
                                                            const isSelected = selNivelId === nv.id
                                                            return (
                                                                <td
                                                                    key={nv.id}
                                                                    className="py-4 px-3 text-center align-middle cursor-pointer select-none"
                                                                    onClick={() => setSelecciones(s => ({ ...s, [c.id]: nv.id }))}
                                                                >
                                                                    {/* Círculo radio */}
                                                                    <div className="flex flex-col items-center gap-1.5">
                                                                        <div
                                                                            className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-150 mx-auto ${
                                                                                isSelected
                                                                                    ? 'border-transparent shadow-sm'
                                                                                    : 'border-[#d1d5db] hover:border-current'
                                                                            }`}
                                                                            style={isSelected
                                                                                ? { backgroundColor: meta?.color ?? '#d32f2f', boxShadow: `0 0 0 3px ${meta?.bg ?? '#fce4e4'}` }
                                                                                : { color: meta?.color ?? '#9ba7ae' }
                                                                            }
                                                                        >
                                                                            {isSelected && (
                                                                                <div className="w-2.5 h-2.5 rounded-full bg-white" />
                                                                            )}
                                                                        </div>

                                                                        {/* Tooltip con puntos del criterio si difiere del encabezado */}
                                                                        {nv.puntos !== columnasHeader.find(ch => ch.etiqueta === nv.etiqueta)?.puntos && (
                                                                            <span className="text-[10px] font-semibold" style={{ color: meta?.color }}>
                                                                                {nv.puntos} pts
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                            )
                                                        })}
                                                    </tr>
                                                )
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* ── Comentarios ───────────────────────────────── */}
                            <div className="px-6 pb-5 pt-3">
                                <label className="text-[13px] font-bold text-[#191c1d] block mb-2">
                                    Comentarios adicionales
                                </label>
                                <textarea
                                    value={comentario}
                                    onChange={e => setComentario(e.target.value)}
                                    rows={4}
                                    placeholder="Escriba aquí sus observaciones cualitativas para el estudiante..."
                                    className="w-full px-4 py-3 border border-[#e1e3e4] rounded-xl text-[14px] text-[#191c1d] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f] bg-[#fafafa] focus:bg-white transition-colors placeholder-[#c4cdd2]"
                                />
                            </div>
                        </>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="mx-6 mb-4 px-4 py-3 bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl">
                            {error}
                        </div>
                    )}
                </div>

                {/* ── Pie del modal ────────────────────────────────────────── */}
                <div className="border-t border-[#e1e3e4] px-6 py-4 flex-shrink-0 flex items-center gap-4 bg-white rounded-b-2xl">

                    {/* Puntuación total */}
                    <div className="flex-shrink-0">
                        <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae]">
                            Puntuación Total
                        </p>
                        <div className="flex items-baseline gap-1 mt-0.5">
                            <span className={`text-[28px] font-extrabold leading-none transition-colors ${todoSeleccionado ? 'text-[#d32f2f]' : 'text-[#c4cdd2]'}`}>
                                {puntuacionTotal.toFixed(1)}
                            </span>
                            <span className="text-[16px] font-bold text-[#9ba7ae]">
                                / {puntuacionMax.toFixed(0)}
                            </span>
                        </div>
                    </div>

                    <div className="flex-1" />

                    {/* Acciones */}
                    <button
                        onClick={onClose}
                        disabled={guardando}
                        className="px-5 py-2.5 border-2 border-[#e1e3e4] text-[#4c616c] text-[13px] font-semibold rounded-xl hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={guardar}
                        disabled={!todoSeleccionado || guardando || rubricas.length === 0}
                        className="flex items-center gap-2 px-5 py-2.5 bg-[#d32f2f] text-white text-[13px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                    >
                        <IconRubricSave />
                        {guardando ? 'Guardando...' : 'Guardar Evaluación'}
                    </button>
                </div>
            </div>
        </div>
    )
}