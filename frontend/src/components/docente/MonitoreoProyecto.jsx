import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { monitoreoApi } from '../../services/docenteApi'

// ── Icons ─────────────────────────────────────────────────────────────────────

function IconRefresh({ spinning }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" className={`w-4 h-4 ${spinning ? 'animate-spin' : ''}`} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4a8 8 0 0112 0M16 16a8 8 0 01-12 0" />
            <path d="M16 4v4h-4M4 16v-4h4" />
        </svg>
    )
}

function IconFilter() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 5h14M6 10h8M9 15h2" />
        </svg>
    )
}

function IconAlert() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 3L2 17h16L10 3z" /><path d="M10 9v4M10 15h.01" />
        </svg>
    )
}

function IconUsers() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="6" r="3" /><path d="M1 17a7 7 0 0114 0" />
            <circle cx="15" cy="7" r="2.5" /><path d="M15 13c2.5 0 4 1.5 4 4" />
        </svg>
    )
}

function IconX() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 4l12 12M16 4L4 16" />
        </svg>
    )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const ESTADO_META = {
    completada:  { label: 'Completada',  color: '#2e7d32', bg: '#f1f8e9', bar: '#4caf50' },
    en_progreso: { label: 'En progreso', color: '#1565c0', bg: '#e3f2fd', bar: '#42a5f5' },
    pendiente:   { label: 'Pendiente',   color: '#6b7b83', bg: '#f0f2f3', bar: '#b0bec5' },
    bloqueada:   { label: 'Bloqueada',   color: '#c62828', bg: '#ffebee', bar: '#ef5350' },
}

const PRIORIDAD_META = {
    alta:   { label: 'Alta',   color: '#c62828', bg: '#ffebee' },
    media:  { label: 'Media',  color: '#e65100', bg: '#fff3e0' },
    baja:   { label: 'Baja',   color: '#2e7d32', bg: '#f1f8e9' },
}

function semaforo(porcentaje, bloqueadas) {
    if (bloqueadas > 0) return 'rojo'
    if (porcentaje >= 60) return 'verde'
    if (porcentaje >= 30) return 'amarillo'
    return 'rojo'
}

const SEMAFORO = {
    verde:    { color: '#2e7d32', bg: '#f1f8e9', label: 'En buen camino' },
    amarillo: { color: '#f9a825', bg: '#fffde7', label: 'Requiere atención' },
    rojo:     { color: '#c62828', bg: '#ffebee', label: 'En riesgo' },
}

function estadoBadge(estado) {
    const m = ESTADO_META[estado] ?? ESTADO_META.pendiente
    return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg" style={{ color: m.color, backgroundColor: m.bg }}>
            {m.label}
        </span>
    )
}

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function StatCard({ label, value, color, bg }) {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 flex flex-col gap-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.7px] text-[#9ba7ae]">{label}</p>
            <p className="text-[32px] font-extrabold leading-none" style={{ color }}>{value}</p>
        </div>
    )
}

function BarraFase({ fase, filtroEquipo, actividades }) {
    const total = fase.total_actividades
    if (total === 0) return null

    // Si hay filtro de equipo, recalcular desde actividades filtradas
    let completadas = fase.actividades_completadas
    let enProgreso  = fase.actividades_en_progreso
    let bloqueadas  = fase.actividades_bloqueadas
    let pendientes  = fase.actividades_pendientes

    if (filtroEquipo) {
        const acts = actividades.filter(a => a.equipo?.id === filtroEquipo)
        completadas = acts.filter(a => a.estado === 'completada').length
        enProgreso  = acts.filter(a => a.estado === 'en_progreso').length
        bloqueadas  = acts.filter(a => a.estado === 'bloqueada').length
        pendientes  = acts.filter(a => a.estado === 'pendiente').length
        const tot = acts.length
        if (tot === 0) return null

        const pct = total > 0 ? Math.round(completadas / tot * 100) : 0
        return <BarraFaseInner fase={fase} total={tot} completadas={completadas} enProgreso={enProgreso} bloqueadas={bloqueadas} pendientes={pendientes} pct={pct} />
    }

    const pct = fase.porcentaje_completado
    return <BarraFaseInner fase={fase} total={total} completadas={completadas} enProgreso={enProgreso} bloqueadas={bloqueadas} pendientes={pendientes} pct={pct} />
}

function BarraFaseInner({ fase, total, completadas, enProgreso, bloqueadas, pendientes, pct }) {
    const seg = (n) => total > 0 ? (n / total * 100) : 0
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl px-5 py-4">
            <div className="flex items-center justify-between mb-3 gap-4 flex-wrap">
                <div>
                    <p className="text-[14px] font-bold text-[#191c1d]">{fase.nombre}</p>
                    <p className="text-[11px] text-[#9ba7ae] mt-0.5">{total} actividad{total !== 1 ? 'es' : ''}</p>
                </div>
                <div className="flex items-baseline gap-1">
                    <span className="text-[26px] font-extrabold text-[#191c1d] leading-none">{pct}</span>
                    <span className="text-[13px] font-bold text-[#9ba7ae]">%</span>
                </div>
            </div>

            {/* Barra apilada */}
            <div className="h-3 rounded-full overflow-hidden flex bg-[#f0f2f3]">
                {completadas > 0 && (
                    <div className="h-full transition-all duration-500" style={{ width: `${seg(completadas)}%`, backgroundColor: ESTADO_META.completada.bar }} />
                )}
                {enProgreso > 0 && (
                    <div className="h-full transition-all duration-500" style={{ width: `${seg(enProgreso)}%`, backgroundColor: ESTADO_META.en_progreso.bar }} />
                )}
                {bloqueadas > 0 && (
                    <div className="h-full transition-all duration-500" style={{ width: `${seg(bloqueadas)}%`, backgroundColor: ESTADO_META.bloqueada.bar }} />
                )}
            </div>

            {/* Leyenda */}
            <div className="flex items-center gap-4 mt-2.5 flex-wrap">
                {[
                    ['completada', completadas],
                    ['en_progreso', enProgreso],
                    ['pendiente', pendientes],
                    ['bloqueada', bloqueadas],
                ].map(([key, n]) => n > 0 && (
                    <div key={key} className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: ESTADO_META[key].bar }} />
                        <span className="text-[11px] text-[#6b7b83]">
                            {ESTADO_META[key].label}: <strong>{n}</strong>
                        </span>
                    </div>
                ))}
            </div>
        </div>
    )
}

function TarjetaEquipo({ equipo }) {
    const sig = semaforo(equipo.porcentaje_progreso, equipo.actividades_bloqueadas)
    const s = SEMAFORO[sig]
    const pct = equipo.porcentaje_progreso
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <p className="text-[14px] font-bold text-[#191c1d] truncate">{equipo.nombre}</p>
                    <div className="flex items-center gap-1 mt-0.5 text-[#9ba7ae]">
                        <IconUsers />
                        <span className="text-[12px]">{equipo.num_miembros} miembro{equipo.num_miembros !== 1 ? 's' : ''}</span>
                    </div>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl flex-shrink-0" style={{ backgroundColor: s.bg }}>
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                    <span className="text-[10px] font-bold" style={{ color: s.color }}>{s.label}</span>
                </div>
            </div>

            {/* Progreso */}
            <div>
                <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-[#9ba7ae]">Progreso</span>
                    <span className="text-[13px] font-extrabold" style={{ color: s.color }}>{pct}%</span>
                </div>
                <div className="h-2 bg-[#f0f2f3] rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: s.color }}
                    />
                </div>
            </div>

            {/* Contadores */}
            <div className="grid grid-cols-2 gap-1.5">
                {[
                    ['completada', equipo.actividades_completadas],
                    ['en_progreso', equipo.actividades_en_progreso],
                    ['pendiente', equipo.actividades_pendientes],
                    ['bloqueada', equipo.actividades_bloqueadas],
                ].map(([key, n]) => {
                    const m = ESTADO_META[key]
                    return (
                        <div key={key} className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg" style={{ backgroundColor: m.bg }}>
                            <div className="w-2 h-2 rounded-sm flex-shrink-0" style={{ backgroundColor: m.bar }} />
                            <span className="text-[10px] font-semibold truncate" style={{ color: m.color }}>
                                {n} {m.label.toLowerCase()}
                            </span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function MonitoreoProyecto() {
    const { proyectoId } = useParams()

    const [data,    setData]    = useState(null)
    const [loading, setLoading] = useState(true)
    const [error,   setError]   = useState(null)
    const [spinning, setSpinning] = useState(false)

    const [filtroEquipo, setFiltroEquipo] = useState(null)  // id | null
    const [filtroFase,   setFiltroFase]   = useState(null)  // id | null

    const cargar = useCallback(async (isRefresh = false) => {
        if (isRefresh) setSpinning(true)
        else setLoading(true)
        setError(null)
        try {
            const res = await monitoreoApi.progreso(proyectoId)
            setData(res)
        } catch {
            setError('No se pudo cargar la información de monitoreo.')
        } finally {
            setLoading(false)
            setSpinning(false)
        }
    }, [proyectoId])

    useEffect(() => { cargar() }, [cargar])

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <p className="text-[13px] text-[#9ba7ae]">Cargando monitoreo...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex-1 flex items-center justify-center p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="text-center">
                    <p className="text-[14px] font-semibold text-[#c62828]">{error}</p>
                    <button onClick={() => cargar()} className="mt-3 px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors">
                        Reintentar
                    </button>
                </div>
            </div>
        )
    }

    const { fases = [], equipos = [], actividades_por_estado: totales = {}, porcentaje_progreso = 0 } = data ?? {}

    // Todas las actividades de todas las fases (aplanadas)
    const todasActividades = fases.flatMap(f => (f.actividades ?? []).map(a => ({ ...a, fase_nombre: f.nombre, fase_id: f.id })))

    // Fases filtradas
    const fasesFiltradas = filtroFase ? fases.filter(f => f.id === filtroFase) : fases

    // Equipos filtrados
    const equiposFiltrados = filtroEquipo ? equipos.filter(e => e.id === filtroEquipo) : equipos

    // Actividades que requieren atención (bloqueadas o sin avance y pendiente), aplicando filtros
    const actsPendientes = todasActividades.filter(a => {
        if (filtroEquipo && a.equipo?.id !== filtroEquipo) return false
        if (filtroFase && a.fase_id !== filtroFase) return false
        return a.estado === 'bloqueada' || (a.estado === 'pendiente' && !a.ultimo_avance)
    })

    const hayFiltros = filtroEquipo || filtroFase

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* ── Cabecera ─────────────────────────────────────────────────── */}
            <div className="flex items-start justify-between gap-4 mb-6">
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Monitoreo</h1>
                    <p className="text-[13px] text-[#6b7b83] mt-0.5">
                        Progreso en tiempo real por equipo y por fase.
                    </p>
                </div>
                <button
                    onClick={() => cargar(true)}
                    disabled={spinning}
                    className="flex items-center gap-2 px-3.5 py-2 text-[13px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors disabled:opacity-50"
                >
                    <IconRefresh spinning={spinning} />
                    Actualizar
                </button>
            </div>

            {/* ── Progreso global + stats ───────────────────────────────────── */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <div className="col-span-2 sm:col-span-1 bg-[#d32f2f] rounded-2xl p-4 flex flex-col justify-between">
                    <p className="text-[11px] font-bold uppercase tracking-[0.7px] text-white/70">Progreso global</p>
                    <div className="mt-2">
                        <div className="flex items-baseline gap-1">
                            <span className="text-[40px] font-extrabold text-white leading-none">{porcentaje_progreso}</span>
                            <span className="text-[18px] font-bold text-white/70">%</span>
                        </div>
                        <div className="mt-2 h-1.5 bg-white/30 rounded-full overflow-hidden">
                            <div className="h-full bg-white rounded-full transition-all duration-700" style={{ width: `${porcentaje_progreso}%` }} />
                        </div>
                    </div>
                </div>
                <StatCard label="Completadas"  value={totales.completada  ?? 0} color="#2e7d32" />
                <StatCard label="En progreso"  value={totales.en_progreso ?? 0} color="#1565c0" />
                <StatCard label="Bloqueadas"   value={totales.bloqueada   ?? 0} color="#c62828" />
            </div>

            {/* ── Filtros ───────────────────────────────────────────────────── */}
            <div className="flex items-center gap-3 mb-6 flex-wrap">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-[#9ba7ae]">
                    <IconFilter />
                    Filtrar por:
                </div>

                <select
                    value={filtroEquipo ?? ''}
                    onChange={e => setFiltroEquipo(e.target.value ? Number(e.target.value) : null)}
                    className="px-3 py-1.5 text-[13px] text-[#191c1d] bg-white border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] transition-colors cursor-pointer"
                >
                    <option value="">Todos los equipos</option>
                    {equipos.map(e => <option key={e.id} value={e.id}>{e.nombre}</option>)}
                </select>

                <select
                    value={filtroFase ?? ''}
                    onChange={e => setFiltroFase(e.target.value ? Number(e.target.value) : null)}
                    className="px-3 py-1.5 text-[13px] text-[#191c1d] bg-white border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] transition-colors cursor-pointer"
                >
                    <option value="">Todas las fases</option>
                    {fases.map(f => <option key={f.id} value={f.id}>{f.nombre}</option>)}
                </select>

                {hayFiltros && (
                    <button
                        onClick={() => { setFiltroEquipo(null); setFiltroFase(null) }}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-[#9ba7ae] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors"
                    >
                        <IconX />
                        Limpiar filtros
                    </button>
                )}
            </div>

            {/* ── Progreso por fase ─────────────────────────────────────────── */}
            <section className="mb-8">
                <h2 className="text-[15px] font-bold text-[#191c1d] mb-3">Progreso por fase</h2>
                {fasesFiltradas.length === 0 ? (
                    <p className="text-[13px] text-[#9ba7ae] py-4">No hay fases para mostrar.</p>
                ) : (
                    <div className="flex flex-col gap-3">
                        {fasesFiltradas.map(f => (
                            <BarraFase
                                key={f.id}
                                fase={f}
                                filtroEquipo={filtroEquipo}
                                actividades={f.actividades ?? []}
                            />
                        ))}
                    </div>
                )}
            </section>

            {/* ── Tarjetas de equipos ───────────────────────────────────────── */}
            <section className="mb-8">
                <h2 className="text-[15px] font-bold text-[#191c1d] mb-3">Resumen por equipo</h2>
                {equiposFiltrados.length === 0 ? (
                    <p className="text-[13px] text-[#9ba7ae] py-4">No hay equipos para mostrar.</p>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {equiposFiltrados.map(eq => <TarjetaEquipo key={eq.id} equipo={eq} />)}
                    </div>
                )}
            </section>

            {/* ── Acciones pendientes ───────────────────────────────────────── */}
            <section>
                <div className="flex items-center gap-2 mb-3">
                    <h2 className="text-[15px] font-bold text-[#191c1d]">Actividades que requieren atención</h2>
                    {actsPendientes.length > 0 && (
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded-lg bg-[#ffebee] text-[#c62828]">
                            {actsPendientes.length}
                        </span>
                    )}
                </div>

                {actsPendientes.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center gap-2">
                        <div className="w-12 h-12 bg-[#f1f8e9] rounded-2xl flex items-center justify-center">
                            <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-[#4caf50]" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M20 6L9 17l-5-5" />
                            </svg>
                        </div>
                        <p className="text-[13px] font-semibold text-[#2e7d32]">Sin acciones pendientes</p>
                        <p className="text-[12px] text-[#9ba7ae]">Todo el progreso está al día
                            {hayFiltros ? ' para los filtros seleccionados' : ''}.
                        </p>
                    </div>
                ) : (
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full min-w-[560px]">
                                <thead>
                                    <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Actividad</th>
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Fase</th>
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Equipo</th>
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Estado</th>
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Fecha límite</th>
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83]">Último avance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {actsPendientes.map((a, i) => {
                                        const pri = PRIORIDAD_META[a.prioridad] ?? PRIORIDAD_META.baja
                                        return (
                                            <tr key={a.id} className={`border-b border-[#f0f2f3] last:border-0 ${i % 2 === 1 ? 'bg-[#fafafa]' : ''}`}>
                                                <td className="px-4 py-3 align-top">
                                                    <p className="text-[13px] font-semibold text-[#191c1d]">{a.nombre}</p>
                                                    {a.prioridad && (
                                                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-0.5 inline-block" style={{ color: pri.color, backgroundColor: pri.bg }}>
                                                            {pri.label}
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 align-top">
                                                    <span className="text-[12px] text-[#6b7b83]">{a.fase_nombre}</span>
                                                </td>
                                                <td className="px-4 py-3 align-top">
                                                    <span className="text-[12px] text-[#191c1d] font-medium">{a.equipo?.nombre ?? '—'}</span>
                                                </td>
                                                <td className="px-4 py-3 align-top">
                                                    {estadoBadge(a.estado)}
                                                </td>
                                                <td className="px-4 py-3 align-top">
                                                    <span className={`text-[12px] ${!a.fecha_limite ? 'text-[#9ba7ae]' : ''}`}>
                                                        {formatFecha(a.fecha_limite)}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 align-top">
                                                    {a.ultimo_avance ? (
                                                        <div>
                                                            <p className="text-[12px] font-semibold text-[#191c1d]">{a.ultimo_avance.porcentaje_completado ?? a.ultimo_avance.porcentaje}%</p>
                                                            <p className="text-[11px] text-[#9ba7ae] mt-0.5">{formatFecha(a.ultimo_avance.fecha_registro ?? a.ultimo_avance.fecha)}</p>
                                                        </div>
                                                    ) : (
                                                        <span className="text-[12px] text-[#9ba7ae] italic">Sin registro</span>
                                                    )}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </section>
        </div>
    )
}