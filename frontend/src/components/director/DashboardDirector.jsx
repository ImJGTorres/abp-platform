import { useState, useEffect, useCallback } from 'react'
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend, Cell,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'
import { reportesApi } from '../../services/docenteApi'
import { periodosApi } from '../../services/api'

// ── Helpers ───────────────────────────────────────────────────────────────────

function pct(val) {
    if (val == null) return '0%'
    return `${Number(val).toFixed(1)}%`
}

function num(val) {
    if (val == null) return '—'
    return Number(val).toLocaleString('es-CO')
}

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconRefresh({ spinning }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" className={`w-4 h-4 ${spinning ? 'animate-spin' : ''}`} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4a8 8 0 0112 0M16 16a8 8 0 01-12 0" />
            <path d="M16 4v4h-4M4 16v-4h4" />
        </svg>
    )
}

function IconTrend({ positivo }) {
    return positivo ? (
        <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 text-green-600" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M2 11l5-5 3 3 4-4" />
        </svg>
    ) : (
        <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 text-[#d32f2f]" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M2 5l5 5 3-3 4 4" />
        </svg>
    )
}

// ── Tarjeta KPI ───────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, variacion, invertido = false }) {
    const hayVariacion = variacion != null && variacion !== 0
    const esPositivo = invertido ? variacion < 0 : variacion > 0

    return (
        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">{label}</p>
            <p className="text-[28px] font-extrabold text-[#191c1d] leading-none">{value}</p>
            {sub && <p className="text-[11px] text-[#9ba7ae] mt-1">{sub}</p>}
            {hayVariacion && (
                <div className={`flex items-center gap-1 mt-2 text-[11px] font-semibold ${esPositivo ? 'text-green-600' : 'text-[#d32f2f]'}`}>
                    <IconTrend positivo={esPositivo} />
                    {esPositivo ? '+' : ''}{Number(variacion).toFixed(1)} vs periodo anterior
                </div>
            )}
        </div>
    )
}

// ── Semáforo ──────────────────────────────────────────────────────────────────

function Semaforo({ value }) {
    if (value >= 60) return <span className="inline-flex items-center gap-1 text-green-600 text-[11px] font-bold"><span className="w-2.5 h-2.5 rounded-full bg-green-500" />Bueno</span>
    if (value >= 30) return <span className="inline-flex items-center gap-1 text-yellow-600 text-[11px] font-bold"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />Regular</span>
    return <span className="inline-flex items-center gap-1 text-[#d32f2f] text-[11px] font-bold"><span className="w-2.5 h-2.5 rounded-full bg-[#d32f2f]" />En riesgo</span>
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function DashboardDirector() {
    const [periodos, setPeriodos] = useState([])
    const [periodoSel, setPeriodoSel] = useState('')
    const [dashboard, setDashboard] = useState(null)
    const [tendencia, setTendencia] = useState(null)
    const [cargando, setCargando] = useState(false)
    const [error, setError] = useState(null)
    const [refreshing, setRefreshing] = useState(false)

    useEffect(() => {
        periodosApi.listar().then(ps => {
            setPeriodos(ps)
        }).catch(() => {})
    }, [])

    const cargar = useCallback(async (periodoId) => {
        setCargando(true)
        setError(null)
        try {
            const [dash, tend] = await Promise.all([
                reportesApi.indicadoresDashboard({ periodoId: periodoId || undefined }),
                reportesApi.indicadoresTendencia(5),
            ])
            setDashboard(dash)
            setTendencia(tend)
        } catch {
            setError('No se pudieron cargar los indicadores.')
        } finally {
            setCargando(false)
            setRefreshing(false)
        }
    }, [])

    useEffect(() => {
        cargar(periodoSel)
    }, [periodoSel, cargar])

    function handleRefresh() {
        setRefreshing(true)
        cargar(periodoSel)
    }

    // ── Datos para gráficas ──────────────────────────────────────────────────

    const distNotas = (() => {
        const d = dashboard?.distribucion_notas ?? {}
        return [
            { rango: '0.0–1.9', count: Number(d.rango_0_2 ?? 0), fill: '#ef5350' },
            { rango: '2.0–2.9', count: Number(d.rango_2_3 ?? 0), fill: '#ffa726' },
            { rango: '3.0–3.9', count: Number(d.rango_3_4 ?? 0), fill: '#42a5f5' },
            { rango: '4.0–5.0', count: Number(d.rango_4_5 ?? 0), fill: '#4caf50' },
        ]
    })()

    const dataTendencia = (tendencia?.periodos ?? []).map(p => ({
        nombre: p.periodo_nombre ?? `P${p.periodo_id}`,
        'Avance %': Number(p.avance_promedio_proyectos_pct ?? 0).toFixed(1),
        'Aprobación %': Number(p.tasa_aprobacion_pct ?? 0).toFixed(1),
    }))

    const dataCursosBarras = (dashboard?.proyectos ?? []).slice(0, 8).map(p => ({
        nombre: p.nombre?.substring(0, 20) + (p.nombre?.length > 20 ? '…' : ''),
        'Avance': Number(p.porcentaje_progreso ?? 0).toFixed(1),
        'A tiempo': Number(p.tasa_entrega_tiempo_pct ?? 0).toFixed(1),
    }))

    // Radar de indicadores globales
    const resumen = Array.isArray(dashboard?.resumen_periodo)
        ? dashboard?.resumen_periodo[0] ?? {}
        : dashboard?.resumen_periodo ?? {}

    const dataRadar = [
        { indicador: 'Avance', valor: Number(resumen.avance_promedio_proyectos_pct ?? 0) },
        { indicador: 'Aprobación', valor: Number(resumen.tasa_aprobacion_pct ?? 0) },
        { indicador: 'Entrega a tiempo', valor: Number(resumen.tasa_entrega_tiempo_pct ?? 0) },
        { indicador: 'Completados', valor: Number(resumen.proyectos_completados ?? 0) * 10 },
        { indicador: 'Estudiantes activos', valor: Math.min(Number(resumen.total_estudiantes ?? 0) / 2, 100) },
    ]

    const tendencias = tendencia?.tendencias ?? {}

    return (
        <div className="p-4 sm:p-6 flex flex-col gap-5">
            {/* Encabezado */}
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">Director</p>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d]">Dashboard institucional</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        Indicadores de desempeño académico por periodo
                    </p>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={cargando}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-[#e1e3e4] rounded-xl text-[12px] font-semibold text-[#4c616c] hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                >
                    <IconRefresh spinning={refreshing} />
                    Actualizar
                </button>
            </div>

            {/* Selector de periodo */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-4">
                <div className="flex items-center gap-3 flex-wrap">
                    <p className="text-[13px] font-semibold text-[#191c1d] flex-shrink-0">Periodo académico:</p>
                    <select
                        value={periodoSel}
                        onChange={e => setPeriodoSel(e.target.value)}
                        className="border border-[#e1e3e4] rounded-xl px-3 py-1.5 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#1565c0]/30"
                    >
                        <option value="">Todos los periodos</option>
                        {periodos.map(p => (
                            <option key={p.id} value={p.id}>{p.nombre ?? `Periodo ${p.id}`}</option>
                        ))}
                    </select>
                    {cargando && (
                        <div className="w-4 h-4 border-2 border-[#1565c0] border-t-transparent rounded-full animate-spin" />
                    )}
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error}
                </div>
            )}

            {dashboard && !cargando && (
                <>
                    {/* KPIs */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <KpiCard
                            label="Avance promedio"
                            value={pct(resumen.avance_promedio_proyectos_pct)}
                            sub="en proyectos activos"
                            variacion={tendencias.avance_proyectos}
                        />
                        <KpiCard
                            label="Tasa de aprobación"
                            value={pct(resumen.tasa_aprobacion_pct)}
                            sub="entregables aprobados"
                            variacion={tendencias.tasa_aprobacion}
                        />
                        <KpiCard
                            label="Total estudiantes"
                            value={num(resumen.total_estudiantes)}
                            sub="activos"
                            variacion={tendencias.total_estudiantes}
                        />
                        <KpiCard
                            label="Proyectos completados"
                            value={num(resumen.proyectos_completados)}
                            sub={`de ${num(resumen.total_proyectos)} totales`}
                            variacion={tendencias.proyectos_completados}
                        />
                    </div>

                    {/* Gráficas de tendencia + Radar */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                        {/* Tendencia histórica */}
                        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                            <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Tendencia histórica</h2>
                            {dataTendencia.length > 1 ? (
                                <ResponsiveContainer width="100%" height={220}>
                                    <LineChart data={dataTendencia} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f3" />
                                        <XAxis dataKey="nombre" tick={{ fontSize: 11 }} />
                                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                                        <Tooltip formatter={(v) => `${v}%`} />
                                        <Legend wrapperStyle={{ fontSize: 11 }} />
                                        <Line type="monotone" dataKey="Avance %" stroke="#1565c0" strokeWidth={2} dot={{ r: 4 }} />
                                        <Line type="monotone" dataKey="Aprobación %" stroke="#4caf50" strokeWidth={2} dot={{ r: 4 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-[220px] text-[#9ba7ae] text-[13px]">
                                    Se necesitan al menos 2 periodos para mostrar tendencias.
                                </div>
                            )}
                        </div>

                        {/* Radar de competencias */}
                        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                            <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Indicadores globales (radar)</h2>
                            <ResponsiveContainer width="100%" height={220}>
                                <RadarChart data={dataRadar}>
                                    <PolarGrid stroke="#f0f2f3" />
                                    <PolarAngleAxis dataKey="indicador" tick={{ fontSize: 10 }} />
                                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
                                    <Radar name="Indicadores" dataKey="valor" stroke="#1565c0" fill="#1565c0" fillOpacity={0.2} />
                                    <Tooltip formatter={(v) => `${Number(v).toFixed(1)}`} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Distribución de notas + Barras por proyecto */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                        {/* Histograma de distribución de notas */}
                        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                            <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Distribución de calificaciones</h2>
                            <p className="text-[11px] text-[#9ba7ae] mb-3">
                                Nota promedio global: <strong className="text-[#191c1d]">
                                    {Number(dashboard?.distribucion_notas?.nota_promedio_global ?? 0).toFixed(2)}
                                </strong>
                            </p>
                            <ResponsiveContainer width="100%" height={180}>
                                <BarChart data={distNotas} margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
                                    <XAxis dataKey="rango" tick={{ fontSize: 11 }} />
                                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                                    <Tooltip formatter={(v) => [v, 'Estudiantes']} />
                                    <Bar dataKey="count" name="Estudiantes" radius={[4, 4, 0, 0]}>
                                        {distNotas.map((entry, i) => (
                                            <Cell key={i} fill={entry.fill} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Avance por proyecto — barras agrupadas */}
                        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                            <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Comparativa de proyectos</h2>
                            {dataCursosBarras.length > 0 ? (
                                <ResponsiveContainer width="100%" height={220}>
                                    <BarChart data={dataCursosBarras} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
                                        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
                                        <YAxis dataKey="nombre" type="category" width={100} tick={{ fontSize: 10 }} />
                                        <Tooltip formatter={(v) => `${v}%`} />
                                        <Legend wrapperStyle={{ fontSize: 11 }} />
                                        <Bar dataKey="Avance" fill="#1565c0" radius={[0, 3, 3, 0]} barSize={7} />
                                        <Bar dataKey="A tiempo" fill="#4caf50" radius={[0, 3, 3, 0]} barSize={7} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-[220px] text-[#9ba7ae] text-[13px]">
                                    Sin proyectos en el periodo seleccionado.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tabla de cursos con semáforos */}
                    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                        <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Proyectos activos</h2>
                        {dashboard?.proyectos?.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-[#e1e3e4]">
                                            <th className="text-left py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Proyecto</th>
                                            <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Curso</th>
                                            <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Avance</th>
                                            <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide hidden sm:table-cell">Actividades</th>
                                            <th className="text-left px-3 py-2 text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#f0f2f3]">
                                        {dashboard.proyectos.map((p, i) => (
                                            <tr key={i} className="hover:bg-[#fafafa] transition-colors">
                                                <td className="py-3 pr-3">
                                                    <p className="text-[13px] font-semibold text-[#191c1d] truncate max-w-[160px]">{p.nombre}</p>
                                                </td>
                                                <td className="px-3 py-3 text-[12px] text-[#9ba7ae] truncate max-w-[120px]">{p.curso_nombre}</td>
                                                <td className="px-3 py-3">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-[12px] text-[#4c616c] w-10 flex-shrink-0">
                                                            {pct(p.porcentaje_progreso)}
                                                        </span>
                                                        <div className="w-20 h-1.5 bg-[#f0f2f3] rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full rounded-full"
                                                                style={{
                                                                    width: `${Math.min(Number(p.porcentaje_progreso ?? 0), 100)}%`,
                                                                    backgroundColor: Number(p.porcentaje_progreso ?? 0) >= 60 ? '#4caf50' : Number(p.porcentaje_progreso ?? 0) >= 30 ? '#ffa726' : '#ef5350',
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-3 py-3 text-[12px] text-[#9ba7ae] hidden sm:table-cell">
                                                    {p.actividades_completadas ?? 0}/{p.total_actividades ?? 0}
                                                </td>
                                                <td className="px-3 py-3">
                                                    <Semaforo value={Number(p.porcentaje_progreso ?? 0)} />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="text-[13px] text-[#9ba7ae] text-center py-6">Sin proyectos en el periodo seleccionado.</p>
                        )}
                    </div>

                    {/* Riesgo por curso */}
                    {dashboard?.estudiantes_riesgo_por_curso?.length > 0 && (
                        <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">
                            <h2 className="text-[14px] font-bold text-[#191c1d] mb-4">Estudiantes en riesgo por curso</h2>
                            <div className="flex flex-col gap-2">
                                {dashboard.estudiantes_riesgo_por_curso.map((r, i) => {
                                    const pctRiesgo = r.total_estudiantes_con_avance > 0
                                        ? (r.estudiantes_en_riesgo / r.total_estudiantes_con_avance) * 100
                                        : 0
                                    return (
                                        <div key={i} className="flex items-center gap-3">
                                            <span className="text-[13px] text-[#4c616c] w-40 truncate">{r.curso_nombre}</span>
                                            <div className="flex-1 h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
                                                <div
                                                    className="h-full rounded-full bg-[#d32f2f]"
                                                    style={{ width: `${Math.min(pctRiesgo, 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-[12px] font-bold text-[#d32f2f] w-16 text-right">
                                                {r.estudiantes_en_riesgo} riesgo
                                            </span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}
                </>
            )}

            {!dashboard && !cargando && !error && (
                <div className="flex items-center justify-center py-16 text-[#9ba7ae] text-[13px]">
                    Cargando indicadores...
                </div>
            )}
        </div>
    )
}
