import { useState, useEffect } from 'react'
import { distribucionApi, getMiEquipo } from '../../services/liderEquipoApi'

const ESTADO_CONFIG = {
    pendiente:   { label: 'Pendiente',   color: 'bg-gray-100 text-gray-600' },
    en_progreso: { label: 'En Progreso', color: 'bg-blue-100 text-blue-700' },
    completada:  { label: 'Completada',  color: 'bg-green-100 text-green-700' },
    bloqueada:   { label: 'Bloqueada',   color: 'bg-red-100 text-red-700' },
}

function StatCard({ icon, iconBg, iconColor, label, value }) {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-lg ${iconBg} flex items-center justify-center ${iconColor}`}>
                    {icon}
                </div>
                <p className="text-[13px] font-semibold text-[#9ba7ae] uppercase tracking-wide">{label}</p>
            </div>
            <p className="text-[32px] font-extrabold text-[#191c1d]">{value}</p>
        </div>
    )
}

function ResponsablesBadges({ responsables }) {
    if (!responsables || responsables.length === 0) {
        return <span className="text-[12px] text-[#9ba7ae]">Sin asignar</span>
    }
    return (
        <div className="flex items-center gap-1 flex-wrap">
            {responsables.map(r => (
                <div key={r.id} className="flex items-center gap-1 bg-[#ffdad6] text-[#af101a] rounded-full px-2 py-0.5">
                    <span className="w-4 h-4 rounded-full bg-[#d32f2f] text-white text-[9px] font-bold flex items-center justify-center flex-shrink-0">
                        {r.nombre?.[0]?.toUpperCase()}
                    </span>
                    <span className="text-[11px] font-semibold max-w-[60px] truncate">{r.nombre}</span>
                </div>
            ))}
        </div>
    )
}

export default function DashboardLider() {
    const [loading, setLoading] = useState(true)
    const [equipoId, setEquipoId] = useState(null)
    const [stats, setStats] = useState({
        miembros: 0,
        actividadesTotal: 0,
        actividadesPendientes: 0,
        actividadesEnProgreso: 0,
        actividadesCompletadas: 0,
    })
    const [actividades, setActividades] = useState([])

    useEffect(() => { cargarDatos() }, [])

    async function cargarDatos() {
        setLoading(true)
        try {
            const miEquipo = await getMiEquipo()
            if (!miEquipo) return
            const id = miEquipo.equipo.id
            setEquipoId(id)
            const [progreso, acts] = await Promise.all([
                distribucionApi.obtenerPorEquipo(id),
                distribucionApi.obtenerActividades(id),
            ])
            setStats({
                miembros: progreso.miembros?.length ?? 0,
                actividadesTotal: progreso.total_actividades ?? 0,
                actividadesPendientes: progreso.actividades_pendientes ?? 0,
                actividadesEnProgreso: progreso.actividades_en_progreso ?? 0,
                actividadesCompletadas: progreso.actividades_completadas ?? 0,
            })
            setActividades(Array.isArray(acts) ? acts : [])
        } catch {
            // sin equipo asignado
        } finally {
            setLoading(false)
        }
    }

    // Agrupar actividades por fase ordenadas por fase_orden
    const fases = (() => {
        const mapa = new Map()
        for (const a of actividades) {
            const key = a.id_fase ?? 'sin-fase'
            if (!mapa.has(key)) {
                mapa.set(key, {
                    id: key,
                    nombre: a.fase_nombre ?? 'Sin fase',
                    orden: a.fase_orden ?? 0,
                    actividades: [],
                })
            }
            mapa.get(key).actividades.push(a)
        }
        return [...mapa.values()].sort((a, b) => a.orden - b.orden)
    })()

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Dashboard</h1>
            <p className="text-[14px] text-[#9ba7ae] mb-6">Resumen del estado de tu equipo y las actividades del proyecto.</p>

            {loading ? (
                <div className="text-center py-12 text-[#9ba7ae]">Cargando datos...</div>
            ) : !equipoId ? (
                <div className="text-center py-12 text-[#9ba7ae]">No tienes un equipo asignado.</div>
            ) : (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard
                            icon={<svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><circle cx="7" cy="7" r="3" /><path d="M1 17a6 6 0 0112 0" /><path d="M13 5a3 3 0 110 6" opacity="0.7" /><path d="M16 17a5 5 0 00-3-4.6" opacity="0.7" /></svg>}
                            iconBg="bg-blue-100" iconColor="text-blue-600"
                            label="Miembros" value={stats.miembros}
                        />
                        <StatCard
                            icon={<svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10h3l2-6 4 12 2-6h3" /></svg>}
                            iconBg="bg-purple-100" iconColor="text-purple-600"
                            label="Actividades" value={stats.actividadesTotal}
                        />
                        <StatCard
                            icon={<svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><circle cx="10" cy="10" r="7" /><path d="M10 5v5l3 3" /></svg>}
                            iconBg="bg-gray-100" iconColor="text-gray-600"
                            label="Pendientes" value={stats.actividadesPendientes}
                        />
                        <StatCard
                            icon={<svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 10l4 4 8-8" /></svg>}
                            iconBg="bg-green-100" iconColor="text-green-600"
                            label="Completadas" value={stats.actividadesCompletadas}
                        />
                    </div>

                    <div className="mt-6 bg-[#d32f2f] text-white rounded-xl p-6">
                        <h2 className="text-[15px] font-bold mb-1 uppercase tracking-wide">En Progreso</h2>
                        <p className="text-[36px] font-extrabold">{stats.actividadesEnProgreso}</p>
                        <p className="text-[13px] opacity-80">Actividades actualmente en ejecucion por el equipo.</p>
                    </div>

                    {fases.length > 0 && (
                        <div className="mt-6">
                            <h2 className="text-[20px] font-bold text-[#191c1d] mb-4">Actividades por Fase</h2>
                            <div className="space-y-4">
                                {fases.map(fase => (
                                    <div key={fase.id} className="bg-white border border-[#e1e3e4] rounded-xl overflow-hidden">
                                        <div className="px-4 py-3 bg-[#f8f9fa] border-b border-[#e1e3e4] flex items-center justify-between">
                                            <p className="text-[13px] font-bold text-[#191c1d]">{fase.nombre}</p>
                                            <span className="text-[11px] text-[#9ba7ae] font-semibold">
                                                {fase.actividades.length} actividad{fase.actividades.length !== 1 ? 'es' : ''}
                                            </span>
                                        </div>
                                        <table className="w-full">
                                            <thead>
                                                <tr className="border-b border-[#f0f2f3]">
                                                    <th className="px-4 py-2 text-left text-[10px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Actividad</th>
                                                    <th className="px-4 py-2 text-left text-[10px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Responsable(s)</th>
                                                    <th className="px-4 py-2 text-center text-[10px] font-semibold text-[#9ba7ae] uppercase tracking-wide w-32">Avance</th>
                                                    <th className="px-4 py-2 text-center text-[10px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {fase.actividades.map(a => {
                                                    const est = ESTADO_CONFIG[a.estado] ?? { label: a.estado, color: 'bg-gray-100 text-gray-600' }
                                                    const pct = a.ultimo_porcentaje_avance ?? 0
                                                    const barColor = pct >= 100 ? 'bg-green-500' : pct >= 60 ? 'bg-[#d32f2f]' : 'bg-amber-500'
                                                    return (
                                                        <tr key={a.id} className="border-b border-[#f0f2f3] last:border-0 hover:bg-[#fafafa] transition-colors">
                                                            <td className="px-4 py-3 text-[13px] font-semibold text-[#191c1d]">{a.nombre}</td>
                                                            <td className="px-4 py-3">
                                                                <ResponsablesBadges responsables={a.responsables_detalle} />
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <div className="flex items-center gap-2">
                                                                    <div className="flex-1 bg-[#e1e3e4] rounded-full h-1.5 overflow-hidden">
                                                                        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
                                                                    </div>
                                                                    <span className="text-[11px] font-bold text-[#191c1d] w-8 text-right flex-shrink-0">{pct}%</span>
                                                                </div>
                                                            </td>
                                                            <td className="px-4 py-3 text-center">
                                                                <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${est.color}`}>
                                                                    {est.label}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    )
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
