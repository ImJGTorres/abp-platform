import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { fasesApi, actividadesApi, evaluacionesApi } from '../../services/docenteApi'
import { entregablesApi } from '../../services/entregablesApi'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatFecha(fecha) {
    if (!fecha) return '—'
    return new Date(fecha).toLocaleDateString('es-CO', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function IconHistory() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="8" />
            <path d="M10 6v4l3 2" />
            <path d="M3 10H1M10 3V1" />
        </svg>
    )
}

function IconCheck() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10l4 4 8-8" />
        </svg>
    )
}

function IconX() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 5l10 10M15 5L5 15" />
        </svg>
    )
}

function IconStar() {
    return (
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M10 1l2.6 5.3 5.8.8-4.2 4.1 1 5.8L10 14.3l-5.2 2.7 1-5.8L1.6 7.1l5.8-.8z" />
        </svg>
    )
}

function IconMessage() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 4a2 2 0 012-2h12a2 2 0 012 2v9a2 2 0 01-2 2H6l-4 3V4z" />
        </svg>
    )
}

function IconEmpty() {
    return (
        <svg viewBox="0 0 48 48" fill="none" className="w-16 h-16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="24" cy="24" r="20" strokeDasharray="4 3" />
            <path d="M24 16v8M24 28v2" strokeWidth="2" />
        </svg>
    )
}

// ── Tarjeta de historial ──────────────────────────────────────────────────────

function TarjetaHistorial({ item }) {
    const aprobado = item.estado === 'aprobado'

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 hover:border-[#d0d4d6] transition-colors">
            {/* Fila superior: título + badge estado */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="min-w-0 flex-1">
                    <h3 className="text-[15px] font-bold text-[#191c1d] leading-tight truncate">
                        {item.titulo}
                    </h3>
                    <p className="text-[12px] text-[#9ba7ae] mt-0.5 truncate">
                        {item.actividadNombre}
                        {item.equipoNombre && (
                            <span className="ml-2 text-[#b0bec5]">· {item.equipoNombre}</span>
                        )}
                    </p>
                </div>

                {aprobado ? (
                    <span className="flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7]">
                        <IconCheck />
                        APROBADO
                    </span>
                ) : (
                    <span className="flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-extrabold tracking-[0.5px] bg-[#ffebee] text-[#c62828] border border-[#ef9a9a]">
                        <IconX />
                        RECHAZADO
                    </span>
                )}
            </div>

            {/* Fila central: puntuación (si aprobado y tiene evaluación) + fecha */}
            <div className="flex items-center gap-4 mb-3 flex-wrap">
                {aprobado && item.puntuacionTotal != null && (
                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#fff8e1] border border-[#ffe082] rounded-xl">
                            <span className="text-[#f9a825]"><IconStar /></span>
                            <span className="text-[16px] font-extrabold text-[#f9a825] leading-none">
                                {parseFloat(item.puntuacionTotal).toFixed(1)}
                            </span>
                            <span className="text-[11px] font-semibold text-[#f9a825]">/ 100</span>
                        </div>
                        {item.rubricaNombre && (
                            <span className="text-[12px] text-[#9ba7ae] italic truncate max-w-[180px]">
                                {item.rubricaNombre}
                            </span>
                        )}
                    </div>
                )}
                <div className="flex items-center gap-1.5 text-[12px] text-[#9ba7ae]">
                    <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 flex-shrink-0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="8" cy="8" r="6" /><path d="M8 5v3l2 1.5" />
                    </svg>
                    {formatFecha(item.fecha_validacion)}
                </div>
            </div>

            {/* Comentario del docente */}
            {item.retroalimentacion && (
                <div className="flex items-start gap-2 bg-[#f8f9fa] rounded-xl p-3">
                    <span className="text-[#9ba7ae] flex-shrink-0 mt-0.5"><IconMessage /></span>
                    <p className="text-[13px] text-[#4c616c] leading-relaxed whitespace-pre-wrap">
                        {item.retroalimentacion}
                    </p>
                </div>
            )}

            {/* Comentario general de la evaluación (si aprobado) */}
            {aprobado && item.comentarioEvaluacion && !item.retroalimentacion && (
                <div className="flex items-start gap-2 bg-[#f8f9fa] rounded-xl p-3">
                    <span className="text-[#9ba7ae] flex-shrink-0 mt-0.5"><IconMessage /></span>
                    <p className="text-[13px] text-[#4c616c] leading-relaxed">
                        {item.comentarioEvaluacion}
                    </p>
                </div>
            )}
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function HistorialEvaluaciones() {
    const { proyectoId } = useParams()

    const [items,   setItems]   = useState([])
    const [loading, setLoading] = useState(true)
    const [error,   setError]   = useState('')
    const [resumen, setResumen] = useState({ aprobados: 0, rechazados: 0, nota: null })

    useEffect(() => {
        if (proyectoId) cargar()
    }, [proyectoId])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            // 1. Cargar fases del proyecto
            const fases = await fasesApi.listarPorProyecto(proyectoId)
            const fasesArr = Array.isArray(fases) ? fases : (fases.results ?? [])

            // 2. Para cada fase, cargar actividades (en paralelo)
            const actividadesPorFase = await Promise.all(
                fasesArr.map(f => actividadesApi.listarPorFase(f.id).catch(() => []))
            )

            // Aplanar actividades con su nombre
            const todasActividades = actividadesPorFase.flatMap((acts, i) =>
                (Array.isArray(acts) ? acts : (acts.results ?? [])).map(a => ({
                    ...a,
                    faseNombre: fasesArr[i]?.nombre ?? '',
                }))
            )

            // 3. Para cada actividad, cargar entregables (en paralelo)
            const entregablesPorActividad = await Promise.all(
                todasActividades.map(a =>
                    entregablesApi.listar(a.id).catch(() => [])
                )
            )

            // 4. Aplanar y filtrar por estado revisado
            const revisados = entregablesPorActividad.flatMap((ents, i) => {
                const arr = Array.isArray(ents) ? ents : (ents.results ?? [])
                return arr
                    .filter(e => e.estado === 'aprobado' || e.estado === 'rechazado')
                    .map(e => ({
                        ...e,
                        actividadNombre: todasActividades[i]?.nombre ?? '—',
                        puntuacionTotal: null,
                        rubricaNombre: null,
                        comentarioEvaluacion: null,
                    }))
            })

            // 5. Para cada aprobado, cargar su evaluación más reciente publicada
            const aprobados = revisados.filter(e => e.estado === 'aprobado')
            const evalResults = await Promise.all(
                aprobados.map(e =>
                    evaluacionesApi.listar(e.id).catch(() => [])
                )
            )

            evalResults.forEach((evals, i) => {
                const arr = Array.isArray(evals) ? evals : (evals.results ?? [])
                // Prefiere publicadas; si no, la más reciente
                const publicadas = arr.filter(ev => ev.estado === 'publicada')
                const mejor = publicadas.length > 0 ? publicadas[0] : arr[0]
                if (mejor) {
                    aprobados[i].puntuacionTotal    = mejor.puntuacion_total
                    aprobados[i].rubricaNombre      = mejor.rubrica_nombre ?? null
                    aprobados[i].comentarioEvaluacion = mejor.comentario_general ?? null
                }
            })

            // 6. Ordenar por fecha_validacion desc
            revisados.sort((a, b) => {
                const fa = a.fecha_validacion ? new Date(a.fecha_validacion) : new Date(0)
                const fb = b.fecha_validacion ? new Date(b.fecha_validacion) : new Date(0)
                return fb - fa
            })

            // Calcular resumen
            const nAprobados  = revisados.filter(e => e.estado === 'aprobado').length
            const nRechazados = revisados.filter(e => e.estado === 'rechazado').length
            const conNota = revisados.filter(e => e.puntuacionTotal != null)
            const promedio = conNota.length > 0
                ? (conNota.reduce((s, e) => s + parseFloat(e.puntuacionTotal), 0) / conNota.length).toFixed(1)
                : null

            setItems(revisados)
            setResumen({ aprobados: nAprobados, rechazados: nRechazados, nota: promedio })
        } catch (err) {
            setError('No se pudo cargar el historial.')
        } finally {
            setLoading(false)
        }
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
                    <span>Cargando historial...</span>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex-1 flex items-center justify-center p-6"
                style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl px-4 py-3">
                    {error}
                </div>
            </div>
        )
    }

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto p-5 sm:p-6"
            style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Encabezado */}
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-[#e8f4fd] flex items-center justify-center text-[#1565c0] flex-shrink-0">
                    <IconHistory />
                </div>
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight leading-tight">
                        Historial de Evaluaciones
                    </h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        Entregables revisados en este proyecto
                    </p>
                </div>
            </div>

            {/* Tarjetas resumen */}
            {items.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 text-center">
                        <p className="text-[28px] font-extrabold text-[#2e7d32] leading-none mb-1">
                            {resumen.aprobados}
                        </p>
                        <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px]">
                            Aprobados
                        </p>
                    </div>
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 text-center">
                        <p className="text-[28px] font-extrabold text-[#c62828] leading-none mb-1">
                            {resumen.rechazados}
                        </p>
                        <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px]">
                            Rechazados
                        </p>
                    </div>
                    {resumen.nota != null && (
                        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 text-center col-span-2 sm:col-span-1">
                            <p className="text-[28px] font-extrabold text-[#f9a825] leading-none mb-1">
                                {resumen.nota}
                            </p>
                            <p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-[0.7px]">
                                Promedio
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Lista de entregables revisados */}
            {items.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-4 py-20 text-[#9ba7ae]">
                    <IconEmpty />
                    <div className="text-center">
                        <p className="text-[15px] font-bold mb-1">Sin evaluaciones aún</p>
                        <p className="text-[13px]">
                            Aquí aparecerán los entregables revisados (aprobados o rechazados).
                        </p>
                    </div>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    {items.map(item => (
                        <TarjetaHistorial key={item.id} item={item} />
                    ))}
                </div>
            )}
        </div>
    )
}