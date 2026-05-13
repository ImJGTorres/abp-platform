import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { estudianteProyectosApi, progresoApi } from '../../services/estudianteApi'

function IconTrend() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 14l4-4 4 4 6-6M17 8v-4h-4" />
        </svg>
    )
}

function IconTarget() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <circle cx="10" cy="10" r="4" />
            <circle cx="10" cy="10" r="1" fill="currentColor" />
        </svg>
    )
}

export default function DashboardProgreso() {
    const { proyectoId } = useParams()
    const [loading, setLoading] = useState(true)
    const [progreso, setProgreso] = useState(null)

    useEffect(() => {
        if (proyectoId) cargarProgreso()
        else setLoading(false)
    }, [proyectoId])

    async function cargarProgreso() {
        setLoading(true)
        try {
            const proyecto = await estudianteProyectosApi.obtener(proyectoId)
            const equipoId = proyecto.equipo?.id
            if (!equipoId) throw new Error('sin equipo')

            const [dataProyecto, dataEquipo] = await Promise.all([
                progresoApi.obtenerProyecto(proyectoId),
                progresoApi.obtenerEquipo(equipoId),
            ])
            setProgreso({
                fases: dataProyecto.fases || [],
                actividades_por_estado: dataProyecto.actividades_por_estado || {},
                progreso_equipo: dataEquipo.porcentaje_progreso ?? 0,
                progreso_general: dataProyecto.porcentaje_progreso ?? 0,
            })
        } catch {
            // error de red o permisos
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
            </div>
        )
    }

    if (!progreso) {
        return (
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-6xl mx-auto text-center py-16 text-[#9ba7ae]">
                    <p className="text-[16px]">Accede al detalle de tu proyecto para ver el progreso.</p>
                </div>
            </div>
        )
    }

    const { fases, actividades_por_estado, progreso_equipo, progreso_general } = progreso

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto">
                <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Dashboard de Progreso</h1>
                <p className="text-[14px] text-[#9ba7ae] mb-6">Panel con barras de progreso animadas por fase, resumen de actividades por estado y progreso del equipo.</p>

                {/* Cards de resumen */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-white border border-[#e1e3e4] rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                                <IconTrend />
                            </div>
                            <div className="flex-1">
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Progreso General</p>
                                <p className="text-[28px] font-extrabold text-[#191c1d] leading-tight">{progreso_general}%</p>
                            </div>
                        </div>
                        <div className="w-full bg-[#e1e3e4] rounded-full h-2 overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${progreso_general}%` }} />
                        </div>
                    </div>

                    <div className="bg-white border border-[#e1e3e4] rounded-xl p-5">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-green-600">
                                <IconTarget />
                            </div>
                            <div className="flex-1">
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Progreso del Equipo</p>
                                <p className="text-[28px] font-extrabold text-[#191c1d] leading-tight">{progreso_equipo}%</p>
                            </div>
                        </div>
                        <div className="w-full bg-[#e1e3e4] rounded-full h-2 overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${progreso_equipo}%` }} />
                        </div>
                    </div>
                </div>

                {/* Progreso por Fase */}
                <div className="bg-white border border-[#e1e3e4] rounded-xl p-5 mb-6">
                    <h2 className="text-[17px] font-bold text-[#191c1d] mb-4">Progreso por Fase</h2>
                    {fases.length === 0 ? (
                        <p className="text-[13px] text-[#9ba7ae] text-center py-4">No hay fases definidas.</p>
                    ) : (
                        <div className="space-y-4">
                            {fases.map(fase => (
                                <div key={fase.id}>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-[14px] font-semibold text-[#191c1d]">{fase.nombre}</span>
                                        <span className="text-[15px] font-bold text-[#d32f2f]">{fase.porcentaje_completado}%</span>
                                    </div>
                                    <div className="w-full bg-[#e1e3e4] rounded-full h-3 overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-[#d32f2f] to-[#ba1a1a] rounded-full transition-all duration-1000 ease-out"
                                            style={{ width: `${fase.porcentaje_completado}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Actividades por Estado */}
                <div className="bg-white border border-[#e1e3e4] rounded-xl p-5">
                    <h2 className="text-[17px] font-bold text-[#191c1d] mb-4">Actividades por Estado</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-xl">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Pendientes</p>
                            <p className="text-[32px] font-extrabold text-gray-600">{actividades_por_estado.pendiente || 0}</p>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-xl">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">En Progreso</p>
                            <p className="text-[32px] font-extrabold text-blue-600">{actividades_por_estado.en_progreso || 0}</p>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-xl">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Completadas</p>
                            <p className="text-[32px] font-extrabold text-green-600">{actividades_por_estado.completada || 0}</p>
                        </div>
                        <div className="text-center p-4 bg-red-50 rounded-xl">
                            <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Bloqueadas</p>
                            <p className="text-[32px] font-extrabold text-red-600">{actividades_por_estado.bloqueada || 0}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}