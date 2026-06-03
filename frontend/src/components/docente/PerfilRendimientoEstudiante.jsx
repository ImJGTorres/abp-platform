import { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { reportesApi } from '../../services/docenteApi'
import ExportarReporte from '../Compartidos/ExportarReporte'

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function nota5(val) {
    if (val == null) return '—'
    return Number(val).toFixed(2)
}

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconBack() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M10 3L5 8l5 5" />
        </svg>
    )
}

function IconAlert() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M10 2L1.5 17h17L10 2z" /><path d="M10 8v4" /><circle cx="10" cy="14" r="0.6" fill="currentColor" />
        </svg>
    )
}

// ── Tarjeta de métrica ────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, color = 'gray', icon }) {
    const colors = {
        red: { bg: 'bg-red-50', text: 'text-[#d32f2f]', border: 'border-red-200' },
        green: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
        orange: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
        gray: { bg: 'bg-[#f8f9fa]', text: 'text-[#4c616c]', border: 'border-[#e1e3e4]' },
    }
    const c = colors[color] ?? colors.gray
    return (
        <div className={`rounded-2xl border p-4 flex flex-col gap-1 ${c.bg} ${c.border}`}>
            <div className={`text-[11px] font-semibold uppercase tracking-wide ${c.text} flex items-center gap-1.5`}>
                {icon}
                {label}
            </div>
            <p className={`text-[26px] font-extrabold ${c.text} leading-none`}>{value}</p>
            {sub && <p className="text-[11px] text-[#9ba7ae]">{sub}</p>}
        </div>
    )
}

// ── Barra comparativa ─────────────────────────────────────────────────────────

function BarraComparativa({ label, valorEst, valorGrupo, max, formatVal }) {
    const pctEst = Math.min((valorEst / max) * 100, 100)
    const pctGrupo = Math.min((valorGrupo / max) * 100, 100)
    const fmtFn = formatVal ?? (v => v)
    return (
        <div className="mb-4">
            <div className="flex justify-between items-center mb-1.5">
                <span className="text-[13px] font-semibold text-[#191c1d]">{label}</span>
                <div className="flex items-center gap-3 text-[12px]">
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-[#d32f2f] inline-block" /> Estudiante: <strong>{fmtFn(valorEst)}</strong></span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-[#9ba7ae] inline-block" /> Grupo: <strong>{fmtFn(valorGrupo)}</strong></span>
                </div>
            </div>
            <div className="relative h-5 bg-[#f0f2f3] rounded-full overflow-hidden">
                <div
                    className="absolute left-0 top-0 h-full bg-[#9ba7ae]/40 rounded-full transition-all duration-500"
                    style={{ width: `${pctGrupo}%` }}
                />
                <div
                    className="absolute left-0 top-0 h-full bg-[#d32f2f] rounded-full transition-all duration-500 opacity-80"
                    style={{ width: `${pctEst}%` }}
                />
            </div>
        </div>
    )
}

// ── Línea de tiempo de actividades ────────────────────────────────────────────

const hoy = new Date()
hoy.setHours(0, 0, 0, 0)

function estadoActividad(act) {
    if (act.estado === 'completada') return 'completada'
    const limite = act.fecha_limite ? new Date(act.fecha_limite) : null
    if (limite && limite < hoy) return 'vencida'
    if (act.estado === 'en_progreso') return 'en_progreso'
    return 'pendiente'
}

const ESTADO_ACTIVIDAD = {
    completada: { dot: 'bg-green-500', texto: 'text-green-700', label: 'Completada', linea: 'bg-green-200' },
    vencida: { dot: 'bg-[#d32f2f]', texto: 'text-[#d32f2f]', label: 'Vencida', linea: 'bg-red-200' },
    en_progreso: { dot: 'bg-blue-500', texto: 'text-blue-700', label: 'En progreso', linea: 'bg-blue-200' },
    pendiente: { dot: 'bg-[#9ba7ae]', texto: 'text-[#9ba7ae]', label: 'Pendiente', linea: 'bg-[#e1e3e4]' },
}

function LineaTiempo({ actividades }) {
    if (!actividades || actividades.length === 0) {
        return <p className="text-[13px] text-[#9ba7ae] text-center py-6">Sin actividades registradas.</p>
    }
    const sorted = [...actividades].sort((a, b) => {
        if (!a.fecha_limite) return 1
        if (!b.fecha_limite) return -1
        return new Date(a.fecha_limite) - new Date(b.fecha_limite)
    })
    return (
        <div className="relative pl-5">
            {sorted.map((act, i) => {
                const estado = estadoActividad(act)
                const cfg = ESTADO_ACTIVIDAD[estado]
                const isLast = i === sorted.length - 1
                return (
                    <div key={act.id} className="relative mb-4 last:mb-0">
                        {!isLast && (
                            <div className={`absolute left-[-13px] top-[18px] w-0.5 h-full ${cfg.linea}`} />
                        )}
                        <div className={`absolute left-[-18px] top-[5px] w-3 h-3 rounded-full border-2 border-white ${cfg.dot} shadow-sm`} />
                        <div className="bg-[#f8f9fa] rounded-xl p-3 border border-[#e1e3e4]">
                            <div className="flex items-start justify-between gap-2">
                                <p className="text-[13px] font-semibold text-[#191c1d] leading-snug">{act.nombre}</p>
                                <span className={`text-[11px] font-bold ${cfg.texto} whitespace-nowrap`}>{cfg.label}</span>
                            </div>
                            {act.fecha_limite && (
                                <p className="text-[11px] text-[#9ba7ae] mt-1">Límite: {fmt(act.fecha_limite)}</p>
                            )}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

// ── Tabla de entregables ──────────────────────────────────────────────────────

const ESTADO_ENTREGABLE = {
    aprobado: { badge: 'bg-green-50 text-green-700 border-green-200', label: 'Aprobado' },
    rechazado: { badge: 'bg-red-50 text-[#d32f2f] border-red-200', label: 'Rechazado' },
    enviado: { badge: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Enviado' },
    borrador: { badge: 'bg-[#f0f2f3] text-[#9ba7ae] border-[#e1e3e4]', label: 'Borrador' },
}

function TablaEntregables({ entregables }) {
    if (!entregables || entregables.length === 0) {
        return <p className="text-[13px] text-[#9ba7ae] text-center py-6">Sin entregables en este proyecto.</p>
    }
    return (
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="border-b border-[#e1e3e4]">
                        <th className="text-left px-0 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Entregable</th>
                        <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Actividad</th>
                        <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                        <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Enviado</th>
                        <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide hidden sm:table-cell">A tiempo</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f2f3]">
                    {entregables.map(e => {
                        const cfg = ESTADO_ENTREGABLE[e.estado] ?? ESTADO_ENTREGABLE.borrador
                        return (
                            <tr key={e.id} className="hover:bg-[#fafafa] transition-colors">
                                <td className="py-3 pr-3">
                                    <p className="text-[13px] font-semibold text-[#191c1d]">{e.titulo}</p>
                                    <p className="text-[11px] text-[#9ba7ae]">v{e.numero_version}</p>
                                </td>
                                <td className="px-3 py-3 text-[12px] text-[#4c616c]">{e.actividad ?? '—'}</td>
                                <td className="px-3 py-3">
                                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg border ${cfg.badge}`}>
                                        {cfg.label}
                                    </span>
                                </td>
                                <td className="px-3 py-3 text-[12px] text-[#9ba7ae]">{fmt(e.fecha_envio)}</td>
                                <td className="px-3 py-3 hidden sm:table-cell">
                                    {e.entregado_a_tiempo == null ? (
                                        <span className="text-[#9ba7ae] text-[12px]">—</span>
                                    ) : e.entregado_a_tiempo ? (
                                        <span className="text-green-600 text-[12px] font-semibold">Sí</span>
                                    ) : (
                                        <span className="text-[#d32f2f] text-[12px] font-semibold">No</span>
                                    )}
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function PerfilRendimientoEstudiante() {
    const { estudianteId } = useParams()
    const [searchParams] = useSearchParams()
    const cursoId = searchParams.get('curso_id')
    const proyectoId = searchParams.get('proyecto_id')

    const [indicadores, setIndicadores] = useState(null)
    const [reporte, setReporte] = useState(null)
    const [cargando, setCargando] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function cargar() {
            setCargando(true)
            setError(null)
            try {
                const [indData, repData] = await Promise.allSettled([
                    reportesApi.rendimientoEstudiante(Number(estudianteId), {
                        cursoId: cursoId ? Number(cursoId) : undefined,
                        proyectoId: proyectoId ? Number(proyectoId) : undefined,
                    }),
                    proyectoId
                        ? reportesApi.reporteEstudianteProyecto(Number(estudianteId), Number(proyectoId))
                        : Promise.resolve(null),
                ])
                if (indData.status === 'fulfilled') setIndicadores(indData.value)
                else throw indData.reason
                if (repData.status === 'fulfilled') setReporte(repData.value)
            } catch {
                setError('No se pudo cargar el perfil de rendimiento.')
            } finally {
                setCargando(false)
            }
        }
        cargar()
    }, [estudianteId, cursoId, proyectoId])

    const backUrl = cursoId ? `/docente/cursos/${cursoId}/riesgo` : -1

    if (cargando) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    if (error || !indicadores) {
        return (
            <div className="flex-1 overflow-y-auto p-6">
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error ?? 'Error al cargar el perfil.'}
                </div>
            </div>
        )
    }

    const est = indicadores.estudiante
    const ind = indicadores.indicadores
    const grupo = indicadores.comparativo_grupo ?? {}
    const desemp = reporte?.desempeno ?? {}
    const histActs = reporte?.historial_actividades ?? []
    const histEnts = reporte?.historial_entregables ?? []
    const notaFinal = reporte?.nota_final ?? null
    const componentes = notaFinal?.componentes ?? {}

    const notaColor = ind.nota_promedio < 3.0 ? 'red' : ind.nota_promedio >= 4.0 ? 'green' : 'orange'
    const incumplidasColor = ind.porcentaje_actividades_incumplidas >= 50 ? 'red' : 'gray'
    const rechazadosColor = ind.entregables_rechazados >= 2 ? 'red' : 'gray'

    // Retroalimentaciones: entregables con retroalimentación del docente
    const retroalimentaciones = histEnts.filter(e => e.retroalimentacion)

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            {/* Encabezado */}
            <div className="flex items-start gap-4 mb-6">
                <Link
                    to={backUrl}
                    className="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl border border-[#e1e3e4] bg-white hover:bg-[#f0f2f3] transition-colors text-[#4c616c] mt-0.5"
                >
                    <IconBack />
                </Link>
                <div className="flex-1 min-w-0">
                    <h1 className="text-[20px] font-extrabold text-[#191c1d] leading-tight">
                        {est.nombre} {est.apellido}
                    </h1>
                    <p className="text-[13px] text-[#9ba7ae]">{est.correo} · {est.codigo ?? 'Sin código'}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    {ind.en_riesgo && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-200 rounded-xl text-[#d32f2f] text-[12px] font-bold">
                            <IconAlert />
                            En riesgo
                        </div>
                    )}
                    {proyectoId && (
                        <ExportarReporte
                            tipo_reporte="estudiante"
                            parametros={{ estudiante_id: Number(estudianteId), proyecto_id: Number(proyectoId) }}
                        />
                    )}
                </div>
            </div>

            {/* Tarjeta de nota final con componentes ponderados */}
            {notaFinal && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 mb-6">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Nota final ponderada</h2>
                    <div className="flex items-center gap-6 flex-wrap">
                        <div className="text-center">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Nota final</p>
                            <p className={`text-[40px] font-extrabold leading-none ${notaFinal.nota_final < 3.0 ? 'text-[#d32f2f]' : notaFinal.nota_final >= 4.0 ? 'text-green-600' : 'text-orange-600'}`}>
                                {nota5(notaFinal.nota_final)}
                            </p>
                            <p className="text-[11px] text-[#9ba7ae] mt-1">/ 5.0</p>
                        </div>
                        <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3 min-w-0">
                            {Object.entries(componentes).map(([k, comp]) => {
                                const labels = { docente: 'Docente', autoevaluacion: 'Autoevaluación', coevaluacion: 'Coevaluación' }
                                return (
                                    <div key={k} className="bg-[#f8f9fa] rounded-xl p-3 border border-[#e1e3e4]">
                                        <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">{labels[k] ?? k}</p>
                                        <p className="text-[20px] font-extrabold text-[#191c1d] leading-tight">{nota5(comp.nota)}</p>
                                        <p className="text-[11px] text-[#9ba7ae]">Peso: {comp.peso_aplicado}%</p>
                                        <div className="mt-2 h-1 bg-[#e1e3e4] rounded-full overflow-hidden">
                                            <div className="h-full bg-[#d32f2f] rounded-full" style={{ width: `${(comp.nota / 5) * 100}%` }} />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            )}

            {/* Métricas */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <MetricCard
                    label="Nota promedio"
                    value={`${nota5(ind.nota_promedio)} / 5`}
                    sub="Escala 0–5"
                    color={notaColor}
                />
                <MetricCard
                    label="% Incumplidas"
                    value={`${ind.porcentaje_actividades_incumplidas?.toFixed(1)}%`}
                    sub={`${ind.actividades_incumplidas} de ${ind.total_actividades}`}
                    color={incumplidasColor}
                />
                <MetricCard
                    label="Entregables rechazados"
                    value={ind.entregables_rechazados}
                    sub={`de ${ind.total_entregables} total`}
                    color={rechazadosColor}
                />
                <MetricCard
                    label="Actividades completadas"
                    value={desemp.actividades_completadas ?? (ind.total_actividades - ind.actividades_incumplidas)}
                    sub={`de ${desemp.total_actividades_equipo ?? ind.total_actividades}`}
                    color="gray"
                />
            </div>

            {/* Comparativo + Línea de tiempo */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                {/* Comparativo con el grupo */}
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Comparativo con el equipo</h2>
                    <BarraComparativa
                        label="Nota promedio (0–5)"
                        valorEst={ind.nota_promedio ?? 0}
                        valorGrupo={grupo.nota_promedio ?? 0}
                        max={5}
                        formatVal={v => nota5(v)}
                    />
                    <BarraComparativa
                        label="% Actividades incumplidas"
                        valorEst={ind.porcentaje_actividades_incumplidas ?? 0}
                        valorGrupo={grupo.pct_actividades_incumplidas ?? 0}
                        max={100}
                        formatVal={v => `${Number(v).toFixed(1)}%`}
                    />
                    {ind.en_riesgo && ind.alertas?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-[#f0f2f3]">
                            <p className="text-[12px] font-bold text-[#d32f2f] mb-2 flex items-center gap-1.5">
                                <IconAlert />
                                Criterios superados
                            </p>
                            <ul className="flex flex-col gap-1">
                                {ind.alertas.map((a, i) => (
                                    <li key={i} className="text-[12px] text-[#4c616c] flex items-start gap-1.5">
                                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#d32f2f] flex-shrink-0" />
                                        {a}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Línea de tiempo */}
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Línea de tiempo de actividades</h2>
                    {histActs.length > 0 ? (
                        <LineaTiempo actividades={histActs} />
                    ) : ind.total_actividades > 0 ? (
                        <div className="text-[13px] text-[#9ba7ae] text-center py-4">
                            Selecciona un proyecto para ver el detalle de actividades.
                        </div>
                    ) : (
                        <p className="text-[13px] text-[#9ba7ae] text-center py-4">Sin actividades registradas.</p>
                    )}
                    {/* Leyenda */}
                    {histActs.length > 0 && (
                        <div className="flex flex-wrap gap-3 mt-4 pt-3 border-t border-[#f0f2f3]">
                            {Object.entries(ESTADO_ACTIVIDAD).map(([k, v]) => (
                                <span key={k} className="flex items-center gap-1.5 text-[11px] text-[#9ba7ae]">
                                    <span className={`w-2 h-2 rounded-full ${v.dot}`} />
                                    {v.label}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Historial de entregables */}
            {proyectoId && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 mb-6">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Historial de entregables evaluados</h2>
                    <TablaEntregables entregables={histEnts} />
                </div>
            )}

            {/* Línea de tiempo de retroalimentaciones */}
            {proyectoId && retroalimentaciones.length > 0 && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Retroalimentaciones del docente</h2>
                    <div className="relative pl-5 flex flex-col gap-4">
                        {retroalimentaciones.map((e, i) => {
                            const isLast = i === retroalimentaciones.length - 1
                            const ESTADO_COLOR = {
                                aprobado: 'bg-green-500',
                                rechazado: 'bg-[#d32f2f]',
                                enviado: 'bg-blue-500',
                                borrador: 'bg-[#9ba7ae]',
                            }
                            const dot = ESTADO_COLOR[e.estado] ?? 'bg-[#9ba7ae]'
                            return (
                                <div key={e.id} className="relative">
                                    {!isLast && <div className="absolute left-[-13px] top-[18px] w-0.5 h-full bg-[#e1e3e4]" />}
                                    <div className={`absolute left-[-18px] top-[5px] w-3 h-3 rounded-full border-2 border-white ${dot} shadow-sm`} />
                                    <div className="bg-[#f8f9fa] rounded-xl p-3 border border-[#e1e3e4]">
                                        <div className="flex items-start justify-between gap-2 mb-1.5">
                                            <p className="text-[13px] font-semibold text-[#191c1d]">{e.titulo}</p>
                                            <span className="text-[11px] text-[#9ba7ae] flex-shrink-0">{fmt(e.fecha_validacion)}</span>
                                        </div>
                                        {e.docente_validador && (
                                            <p className="text-[11px] text-[#9ba7ae] mb-1.5">
                                                Docente: {e.docente_validador}
                                            </p>
                                        )}
                                        <p className="text-[12px] text-[#4c616c] leading-relaxed bg-white rounded-lg p-2 border border-[#e1e3e4]">
                                            {e.retroalimentacion}
                                        </p>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </div>
    )
}
