import { useState, useEffect } from 'react'
import { distribucionApi } from '../../services/liderEquipoApi'
import { session } from '../../services/api'

function IconTeam() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="7" cy="7" r="3" />
            <path d="M1 17a6 6 0 0112 0" />
            <path d="M13 5a3 3 0 110 6" opacity="0.7" />
            <path d="M16 17a5 5 0 00-3-4.6" opacity="0.7" />
        </svg>
    )
}

function IconActivity() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 10h3l2-6 4 12 2-6h3" />
        </svg>
    )
}

function IconClock() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 5v5l3 3" />
        </svg>
    )
}

function IconCheck() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10l4 4 8-8" />
        </svg>
    )
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

export default function DashboardLider() {
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState({
        miembros: 0,
        actividadesTotal: 0,
        actividadesPendientes: 0,
        actividadesEnProgreso: 0,
        actividadesCompletadas: 0,
    })
    const user = session.getUser()

    useEffect(() => {
        cargarDatos()
    }, [])

    async function cargarDatos() {
        setLoading(true)
        try {
            const equipoId = user?.equipo_id
            if (!equipoId) return
            const distribucion = await distribucionApi.obtenerPorEquipo(equipoId)
            setStats({
                miembros: distribucion.miembros?.length ?? 0,
                actividadesTotal: distribucion.total_actividades ?? 0,
                actividadesPendientes: distribucion.pendientes ?? 0,
                actividadesEnProgreso: distribucion.en_progreso ?? 0,
                actividadesCompletadas: distribucion.completadas ?? 0,
            })
        } catch {
            // backend not yet implemented — keep zeros
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Dashboard</h1>
            <p className="text-[14px] text-[#9ba7ae] mb-6">Resumen del estado de tu equipo y las actividades del proyecto.</p>

            {loading ? (
                <div className="text-center py-12 text-[#9ba7ae]">Cargando datos...</div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                        icon={<IconTeam />}
                        iconBg="bg-blue-100"
                        iconColor="text-blue-600"
                        label="Miembros"
                        value={stats.miembros}
                    />
                    <StatCard
                        icon={<IconActivity />}
                        iconBg="bg-purple-100"
                        iconColor="text-purple-600"
                        label="Actividades"
                        value={stats.actividadesTotal}
                    />
                    <StatCard
                        icon={<IconClock />}
                        iconBg="bg-gray-100"
                        iconColor="text-gray-600"
                        label="Pendientes"
                        value={stats.actividadesPendientes}
                    />
                    <StatCard
                        icon={<IconCheck />}
                        iconBg="bg-green-100"
                        iconColor="text-green-600"
                        label="Completadas"
                        value={stats.actividadesCompletadas}
                    />
                </div>
            )}

            {!loading && (
                <div className="mt-6 bg-[#d32f2f] text-white rounded-xl p-6">
                    <h2 className="text-[15px] font-bold mb-1 uppercase tracking-wide">En Progreso</h2>
                    <p className="text-[36px] font-extrabold">{stats.actividadesEnProgreso}</p>
                    <p className="text-[13px] opacity-80">Actividades actualmente en ejecucion por el equipo.</p>
                </div>
            )}
        </div>
    )
}