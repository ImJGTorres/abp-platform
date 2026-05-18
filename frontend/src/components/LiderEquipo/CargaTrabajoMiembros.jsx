import { useState, useEffect } from 'react'
import { distribucionApi, getMiEquipo } from '../../services/liderEquipoApi'

export default function CargaTrabajoMiembros() {
    const [loading, setLoading] = useState(true)
    const [equipoId, setEquipoId] = useState(null)
    const [miembros, setMiembros] = useState([])

    useEffect(() => { cargarCarga() }, [])

    async function cargarCarga() {
        setLoading(true)
        try {
            const miEquipo = await getMiEquipo()
            if (!miEquipo) return
            const id = miEquipo.equipo.id
            setEquipoId(id)
            const data = await distribucionApi.obtenerCargaMiembros(id)
            setMiembros(data.miembros || [])
        } catch {
            // sin equipo asignado
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto">
                <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Carga de Trabajo por Miembro</h1>
                <p className="text-[14px] text-[#9ba7ae] mb-6">Resumen visual que muestra cuantas actividades tiene asignadas cada miembro del equipo.</p>

                {loading ? (
                    <div className="text-center py-12 text-[#9ba7ae]">Cargando carga de trabajo...</div>
                ) : !equipoId ? (
                    <div className="text-center py-12 text-[#9ba7ae]">No tienes un equipo asignado.</div>
                ) : miembros.length === 0 ? (
                    <div className="text-center py-12 text-[#9ba7ae]">No hay miembros en el equipo.</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {miembros.map(m => (
                            <div key={m.id_usuario} className="bg-white border border-[#e1e3e4] rounded-xl p-5 hover:shadow-md transition-shadow">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-12 h-12 rounded-full bg-[#ffdad6] flex items-center justify-center flex-shrink-0">
                                        <span className="text-[14px] font-bold text-[#af101a]">{m.nombre?.[0]?.toUpperCase()}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[15px] font-bold text-[#191c1d] truncate">{m.nombre}</p>
                                        <p className="text-[12px] text-[#9ba7ae] truncate">{m.rol_interno || 'Miembro'}</p>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-[11px] font-semibold text-[#9ba7ae] uppercase">Total</span>
                                            <span className="text-[18px] font-extrabold text-[#191c1d]">{m.actividades_asignadas}</span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-3 gap-2 text-center">
                                        <div className="bg-gray-50 rounded-lg p-2">
                                            <p className="text-[10px] text-[#9ba7ae] uppercase mb-0.5">Pendientes</p>
                                            <p className="text-[16px] font-bold text-gray-600">{m.actividades_pendientes || 0}</p>
                                        </div>
                                        <div className="bg-blue-50 rounded-lg p-2">
                                            <p className="text-[10px] text-[#9ba7ae] uppercase mb-0.5">En progreso</p>
                                            <p className="text-[16px] font-bold text-blue-600">{m.actividades_en_progreso || 0}</p>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-2">
                                            <p className="text-[10px] text-[#9ba7ae] uppercase mb-0.5">Completadas</p>
                                            <p className="text-[16px] font-bold text-green-600">{m.actividades_completadas || 0}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
