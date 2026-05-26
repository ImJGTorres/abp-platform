import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
    PieChart, Pie, Legend,
} from 'recharts'
import { reportesApi } from '../../services/docenteApi'
import ExportarReporte from '../Compartidos/ExportarReporte'

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function pct(val) {
    if (val == null) return '0%'
    return `${Number(val).toFixed(1)}%`
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

function IconChevron({ open }) {
    return (
        <svg viewBox="0 0 16 16" fill="none" className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M3 6l5 5 5-5" />
        </svg>
    )
}

// ── Sección colapsable ────────────────────────────────────────────────────────

function Section({ title, defaultOpen = true, children }) {
    const [open, setOpen] = useState(defaultOpen)
    return (
        <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
            <button
                onClick={() => setOpen(o => !o)}
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[#fafafa] transition-colors"
            >
                <h2 className="text-[14px] font-bold text-[#191c1d]">{title}</h2>
                <IconChevron open={open} />
            </button>
            {open && <div className="px-5 pb-5">{children}</div>}
        </div>
    )
}

// ── Tarjeta de KPI ────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, color = 'gray' }) {
    const palette = {
        blue:   { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200' },
        green:  { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200' },
        red:    { bg: 'bg-red-50',    text: 'text-[#d32f2f]',  border: 'border-red-200' },
        orange: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
        gray:   { bg: 'bg-[#f8f9fa]', text: 'text-[#4c616c]', border: 'border-[#e1e3e4]' },
    }
    const c = palette[color] ?? palette.gray
    return (
        <div className={`rounded-2xl border p-4 flex flex-col gap-1 ${c.bg} ${c.border}`}>
            <p className={`text-[11px] font-semibold uppercase tracking-wide ${c.text}`}>{label}</p>
            <p className={`text-[26px] font-extrabold leading-none ${c.text}`}>{value}</p>
            {sub && <p className="text-[11px] text-[#9ba7ae]">{sub}</p>}
        </div>
    )
}

// ── Barra de progreso ─────────────────────────────────────────────────────────

function ProgressBar({ value, max = 100, color = '#1565c0' }) {
    const pct = Math.min(Math.max((value / max) * 100, 0), 100)
    return (
        <div className="relative h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
            <div
                className="absolute left-0 top-0 h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: color }}
            />
        </div>
    )
}

// ── Estado badge ──────────────────────────────────────────────────────────────

const ESTADO_CFG = {
    activo:      { bg: 'bg-blue-50',   text: 'text-blue-700',   label: 'Activo' },
    completado:  { bg: 'bg-green-50',  text: 'text-green-700',  label: 'Completado' },
    pausado:     { bg: 'bg-orange-50', text: 'text-orange-700', label: 'Pausado' },
    cancelado:   { bg: 'bg-red-50',    text: 'text-[#d32f2f]',  label: 'Cancelado' },
    borrador:    { bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]', label: 'Borrador' },
    completada:  { bg: 'bg-green-50',  text: 'text-green-700',  label: 'Completada' },
}

function EstadoBadge({ estado }) {
    const cfg = ESTADO_CFG[estado] ?? { bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]', label: estado }
    return (
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg ${cfg.bg} ${cfg.text}`}>
            {cfg.label}
        </span>
    )
}

// ── Semáforo ──────────────────────────────────────────────────────────────────

function Semaforo({ value }) {
    if (value >= 60) return <span className="inline-block w-3 h-3 rounded-full bg-green-500" title="Buen avance" />
    if (value >= 30) return <span className="inline-block w-3 h-3 rounded-full bg-yellow-400" title="Avance medio" />
    return <span className="inline-block w-3 h-3 rounded-full bg-[#d32f2f]" title="Avance bajo" />
}

// ── Colores para gráficas ─────────────────────────────────────────────────────

const PIE_COLORS = ['#4caf50', '#d32f2f', '#42a5f5', '#ffa726']

// ── Vista principal ───────────────────────────────────────────────────────────

export default function ReporteProyecto() {
    const { proyectoId } = useParams()
    const [data, setData] = useState(null)
    const [cargando, setCargando] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function cargar() {
            setCargando(true)
            setError(null)
            try {
                const res = await reportesApi.reporteProyecto(Number(proyectoId))
                setData(res)
            } catch {
                setError('No se pudo cargar el reporte del proyecto.')
            } finally {
                setCargando(false)
            }
        }
        cargar()
    }, [proyectoId])

    if (cargando) {
        return (
            <div className="flex-1 flex items-center justify-center p-10">
                <div className="w-8 h-8 border-2 border-[#1565c0] border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    if (error || !data) {
        return (
            <div className="p-6">
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error ?? 'Error cargando el reporte.'}
                </div>
            </div>
        )
    }

    const { proyecto, progreso_global: pg, progreso_por_fase: fases,
        resumen_entregables: re, equipos, avance_por_estudiante: avanceEst,
        estudiantes_bajo_rendimiento: bajosRend, objetivos, hitos } = data

    // Datos para gráfica de progreso por fase (barras horizontales)
    const dataFases = (fases ?? []).map(f => ({
        name: f.nombre_fase ?? `Fase ${f.orden}`,
        progreso: Number(f.porcentaje_progreso ?? 0),
        completadas: Number(f.actividades_completadas ?? 0),
        total: Number(f.total_actividades ?? 0),
    }))

    // Datos para dona de entregables
    const dataEntregables = [
        { name: 'Aprobados',  value: Number(re?.aprobados ?? 0) },
        { name: 'Rechazados', value: Number(re?.rechazados ?? 0) },
        { name: 'Pendientes', value: Number(re?.pendientes ?? 0) },
        { name: 'En revisión', value: Number(re?.en_revision ?? 0) },
    ].filter(d => d.value > 0)

    const progGlobal = Number(pg?.porcentaje_progreso ?? 0)
    const colorProgreso = progGlobal >= 60 ? 'green' : progGlobal >= 30 ? 'orange' : 'red'

    return (
        <div className="p-4 sm:p-6 flex flex-col gap-5">
            {/* Encabezado */}
            <div className="flex items-start gap-4">
                <Link
                    to="/director/reportes"
                    className="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl border border-[#e1e3e4] bg-white hover:bg-[#f0f2f3] transition-colors text-[#4c616c] mt-0.5"
                >
                    <IconBack />
                </Link>
                <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">
                        Reporte de Proyecto
                    </p>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] leading-tight">
                        {proyecto.nombre}
                    </h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        {proyecto.curso} · {fmt(proyecto.fecha_inicio)} – {fmt(proyecto.fecha_fin_estimada)}
                    </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <EstadoBadge estado={proyecto.estado} />
                    <ExportarReporte
                        tipo_reporte="proyecto"
                        parametros={{ proyecto_id: Number(proyectoId) }}
                    />
                </div>
            </div>

            {/* KPIs de resumen */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard
                    label="Avance global"
                    value={pct(pg?.porcentaje_progreso)}
                    sub={`${pg?.actividades_completadas ?? 0} / ${pg?.total_actividades ?? 0} actividades`}
                    color={colorProgreso}
                />
                <KpiCard
                    label="Total equipos"
                    value={equipos?.length ?? 0}
                    sub="en el proyecto"
                    color="blue"
                />
                <KpiCard
                    label="Entregables"
                    value={re?.total_entregables ?? 0}
                    sub={`${re?.aprobados ?? 0} aprobados`}
                    color="gray"
                />
                <KpiCard
                    label="Bajo rendimiento"
                    value={bajosRend?.length ?? 0}
                    sub="estudiantes"
                    color={bajosRend?.length > 0 ? 'red' : 'green'}
                />
            </div>

            {/* Sección: Resumen */}
            <Section title="Resumen del proyecto">
                <p className="text-[13px] text-[#4c616c] leading-relaxed mb-4">
                    {proyecto.descripcion || 'Sin descripción registrada.'}
                </p>
                {objetivos?.length > 0 && (
                    <div>
                        <p className="text-[12px] font-bold text-[#9ba7ae] uppercase tracking-wide mb-2">Objetivos</p>
                        <ul className="flex flex-col gap-1.5">
                            {objetivos.map(o => (
                                <li key={o.id} className="flex items-start gap-2 text-[13px] text-[#4c616c]">
                                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#1565c0] flex-shrink-0" />
                                    {o.descripcion}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                {hitos?.length > 0 && (
                    <div className="mt-4">
                        <p className="text-[12px] font-bold text-[#9ba7ae] uppercase tracking-wide mb-2">Hitos</p>
                        <div className="flex flex-col gap-2">
                            {hitos.map(h => (
                                <div key={h.id} className="flex items-center justify-between gap-3 py-2 border-b border-[#f0f2f3] last:border-0">
                                    <span className="text-[13px] text-[#191c1d] font-medium">{h.nombre}</span>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                        <span className="text-[11px] text-[#9ba7ae]">{fmt(h.fecha_fin)}</span>
                                        <EstadoBadge estado={h.estado} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </Section>

            {/* Sección: Gráficas de progreso */}
            <Section title="Gráficas de progreso">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Barras de progreso por fase */}
                    <div>
                        <p className="text-[13px] font-semibold text-[#4c616c] mb-3">Avance por fase (%)</p>
                        {dataFases.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={dataFases} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
                                    <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
                                    <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 11 }} />
                                    <Tooltip formatter={(v) => [`${v}%`, 'Progreso']} />
                                    <Bar dataKey="progreso" radius={[0, 4, 4, 0]}>
                                        {dataFases.map((entry, i) => (
                                            <Cell
                                                key={i}
                                                fill={entry.progreso >= 60 ? '#4caf50' : entry.progreso >= 30 ? '#ffa726' : '#ef5350'}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="text-[13px] text-[#9ba7ae] text-center py-8">Sin fases registradas.</p>
                        )}
                    </div>

                    {/* Dona de estado de entregables */}
                    <div>
                        <p className="text-[13px] font-semibold text-[#4c616c] mb-3">Estado de entregables</p>
                        {dataEntregables.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie
                                        data={dataEntregables}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={55}
                                        outerRadius={80}
                                        dataKey="value"
                                        label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                                        labelLine={false}
                                    >
                                        {dataEntregables.map((_, i) => (
                                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="text-[13px] text-[#9ba7ae] text-center py-8">Sin entregables registrados.</p>
                        )}
                    </div>
                </div>
            </Section>

            {/* Sección: Tabla de equipos */}
            <Section title="Equipos con indicadores">
                {equipos?.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#e1e3e4]">
                                    <th className="text-left py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Equipo</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Miembros</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Entregables</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Aprobados</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide hidden sm:table-cell">Rechazados</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f0f2f3]">
                                {equipos.map(eq => {
                                    const pctApr = eq.entregables.total > 0
                                        ? (eq.entregables.aprobados / eq.entregables.total) * 100
                                        : 0
                                    return (
                                        <tr key={eq.id} className="hover:bg-[#fafafa] transition-colors">
                                            <td className="py-3 pr-3">
                                                <p className="text-[13px] font-semibold text-[#191c1d]">{eq.nombre}</p>
                                            </td>
                                            <td className="px-3 py-3"><EstadoBadge estado={eq.estado} /></td>
                                            <td className="px-3 py-3 text-[13px] text-[#4c616c]">{eq.total_miembros}</td>
                                            <td className="px-3 py-3">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[13px] text-[#4c616c] w-6">{eq.entregables.total}</span>
                                                    <div className="flex-1 min-w-[60px]">
                                                        <ProgressBar value={pctApr} color="#1565c0" />
                                                    </div>
                                                    <span className="text-[11px] text-[#9ba7ae] w-8">{pct(pctApr)}</span>
                                                </div>
                                            </td>
                                            <td className="px-3 py-3 text-[13px] text-green-700 font-semibold">{eq.entregables.aprobados}</td>
                                            <td className="px-3 py-3 text-[13px] text-[#d32f2f] font-semibold hidden sm:table-cell">{eq.entregables.rechazados}</td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-[13px] text-[#9ba7ae] text-center py-6">Sin equipos registrados.</p>
                )}
            </Section>

            {/* Sección: Avance por estudiante */}
            {avanceEst?.length > 0 && (
                <Section title="Avance por estudiante" defaultOpen={false}>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#e1e3e4]">
                                    <th className="text-left py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estudiante</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Avance</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Nota (0-5)</th>
                                    <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f0f2f3]">
                                {avanceEst.map((est, i) => {
                                    const nota = Number(est.nota_promedio_5 ?? 0)
                                    const esRiesgo = bajosRend?.some(b => b.usuario_id === est.usuario_id)
                                    return (
                                        <tr key={i} className="hover:bg-[#fafafa] transition-colors">
                                            <td className="py-3 pr-3">
                                                <p className="text-[13px] font-semibold text-[#191c1d]">
                                                    {est.nombre} {est.apellido}
                                                </p>
                                                <p className="text-[11px] text-[#9ba7ae]">{est.codigo_estudiante}</p>
                                            </td>
                                            <td className="px-3 py-3">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[12px] text-[#4c616c] w-8">
                                                        {pct(est.promedio_avance_pct)}
                                                    </span>
                                                    <div className="w-24">
                                                        <ProgressBar value={Number(est.promedio_avance_pct ?? 0)} />
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-3 py-3">
                                                <span className={`text-[13px] font-bold ${nota < 3 ? 'text-[#d32f2f]' : nota >= 4 ? 'text-green-700' : 'text-orange-600'}`}>
                                                    {nota5(nota)}
                                                </span>
                                            </td>
                                            <td className="px-3 py-3">
                                                <div className="flex items-center gap-1.5">
                                                    <Semaforo value={Number(est.promedio_avance_pct ?? 0)} />
                                                    {esRiesgo && (
                                                        <span className="text-[10px] font-bold text-[#d32f2f] bg-red-50 px-1.5 py-0.5 rounded">Riesgo</span>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                </Section>
            )}

            {/* Sección: Observaciones */}
            <Section title="Observaciones" defaultOpen={false}>
                {bajosRend?.length > 0 ? (
                    <div className="flex flex-col gap-2">
                        <p className="text-[13px] font-semibold text-[#d32f2f] mb-1">
                            {bajosRend.length} estudiante(s) por debajo del umbral de rendimiento ({pct(data.umbral_bajo_rendimiento * 20)} en nota)
                        </p>
                        {bajosRend.map((est, i) => (
                            <div key={i} className="flex items-center justify-between bg-red-50 border border-red-200 rounded-xl px-4 py-2">
                                <span className="text-[13px] text-[#191c1d] font-medium">{est.nombre} {est.apellido}</span>
                                <span className="text-[12px] font-bold text-[#d32f2f]">
                                    Nota: {nota5(est.nota_promedio_5)}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-[13px] text-[#9ba7ae]">
                        Sin observaciones de bajo rendimiento. Todos los estudiantes están dentro del umbral.
                    </p>
                )}
            </Section>
        </div>
    )
}
