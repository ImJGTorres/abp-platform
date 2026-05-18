import { useState, useEffect } from 'react'
import { distribucionApi, getMiEquipo } from '../../services/liderEquipoApi'
import RegistroAvance from '../Estudiante/RegistroAvances'

const ESTADO_CONFIG = {
    pendiente:   { label: 'Pendiente',   color: 'bg-gray-100 text-gray-600' },
    en_progreso: { label: 'En Progreso', color: 'bg-blue-100 text-blue-700' },
    completada:  { label: 'Completada',  color: 'bg-green-100 text-green-700' },
    bloqueada:   { label: 'Bloqueada',   color: 'bg-red-100 text-red-700' },
}

export default function DistribucionTrabajo() {
    const [loading, setLoading] = useState(true)
    const [equipoId, setEquipoId] = useState(null)
    const [miembros, setMiembros] = useState([])
    const [actividades, setActividades] = useState([])
    const [totalActividades, setTotalActividades] = useState(0)
    const [avancesModal, setAvancesModal] = useState(null)

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
            setMiembros(progreso.miembros || [])
            setTotalActividades(progreso.total_actividades || 0)
            setActividades(acts)
        } catch {
            // sin equipo asignado o error de red
        } finally {
            setLoading(false)
        }
    }

    function getCargaPorcentaje(miembro) {
        // actividades_asignadas viene directo del endpoint de progreso
        return totalActividades > 0
            ? Math.round((miembro.actividades_asignadas / totalActividades) * 100)
            : 0
    }

    function getEstadoCarga(porcentaje) {
        if (porcentaje > 80) return { label: 'Carga Critica', color: 'text-red-600 bg-red-100' }
        if (porcentaje > 50) return { label: 'Carga Alta',    color: 'text-yellow-600 bg-yellow-100' }
        return { label: 'Carga Ligera', color: 'text-green-600 bg-green-100' }
    }

    const capacidadGlobal = miembros.length > 0
        ? Math.round(miembros.reduce((acc, m) => acc + getCargaPorcentaje(m), 0) / miembros.length)
        : 0

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Distribucion de Trabajo</h1>
            <p className="text-[14px] text-[#9ba7ae] mb-6">Supervise la carga de actividades de cada miembro del equipo.</p>

            {loading ? (
                <div className="text-center py-12 text-[#9ba7ae]">Cargando distribucion...</div>
            ) : !equipoId ? (
                <div className="text-center py-12 text-[#9ba7ae]">No tienes un equipo asignado.</div>
            ) : miembros.length === 0 ? (
                <div className="text-center py-12 text-[#9ba7ae]">No hay miembros en el equipo.</div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {miembros.map(m => {
                            const porcentaje = getCargaPorcentaje(m)
                            const { label, color } = getEstadoCarga(porcentaje)
                            return (
                                <div key={m.id_usuario} className="bg-white border border-[#e1e3e4] rounded-xl p-5 hover:shadow-md transition-shadow">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="w-12 h-12 rounded-full bg-[#ffdad6] flex items-center justify-center flex-shrink-0">
                                            <span className="text-[14px] font-bold text-[#af101a]">{m.nombre?.[0]?.toUpperCase()}</span>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[15px] font-bold text-[#191c1d] truncate">{m.nombre}</p>
                                            <p className="text-[12px] text-[#9ba7ae] truncate">{m.rol_interno || 'Miembro'}</p>
                                        </div>
                                        <div className="bg-[#f8f9fa] rounded-lg p-2 text-center flex-shrink-0">
                                            <p className="text-[9px] text-[#9ba7ae] uppercase mb-0.5">Total</p>
                                            <p className="text-[15px] font-extrabold text-[#191c1d]">{m.actividades_asignadas ?? 0}</p>
                                        </div>
                                    </div>

                                    <div className="mb-3">
                                        <div className="flex items-center justify-between mb-1.5">
                                            <span className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Carga</span>
                                            <span className="text-[15px] font-extrabold text-[#191c1d]">{porcentaje}%</span>
                                        </div>
                                        <div className="w-full bg-[#e1e3e4] rounded-full h-2 overflow-hidden">
                                            <div className={`h-full rounded-full transition-all duration-500 ${porcentaje > 80 ? 'bg-red-500' : porcentaje > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                                                style={{ width: `${porcentaje}%` }} />
                                        </div>
                                    </div>

                                    <div className={`px-3 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-wide text-center mb-3 ${color}`}>
                                        {label}
                                    </div>

                                    <div className="grid grid-cols-3 gap-1.5 text-center border-t border-[#f0f2f3] pt-3">
                                        <div className="bg-gray-50 rounded-lg p-2">
                                            <p className="text-[9px] text-[#9ba7ae] uppercase mb-0.5">Pendiente</p>
                                            <p className="text-[15px] font-bold text-gray-600">{m.actividades_pendientes ?? 0}</p>
                                        </div>
                                        <div className="bg-blue-50 rounded-lg p-2">
                                            <p className="text-[9px] text-[#9ba7ae] uppercase mb-0.5">En Progreso</p>
                                            <p className="text-[15px] font-bold text-blue-600">{m.actividades_en_progreso ?? 0}</p>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-2">
                                            <p className="text-[9px] text-[#9ba7ae] uppercase mb-0.5">Completado</p>
                                            <p className="text-[15px] font-bold text-green-600">{m.actividades_completadas ?? 0}</p>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    <div className="mt-6 bg-[#d32f2f] text-white rounded-xl p-6">
                        <h2 className="text-[15px] font-bold mb-1 uppercase tracking-wide">Capacidad Global</h2>
                        <p className="text-[36px] font-extrabold">{capacidadGlobal}%</p>
                        <p className="text-[13px] opacity-80">Promedio de carga de trabajo del equipo.</p>
                    </div>

                    {actividades.length > 0 && (
                        <div className="mt-6">
                            <h2 className="text-[20px] font-bold text-[#191c1d] mb-4">Registro de Actividades</h2>
                            <div className="bg-white border border-[#e1e3e4] rounded-xl overflow-hidden">
                                <table className="w-full">
                                    <thead className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Actividad</th>
                                            <th className="px-4 py-3 text-center text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Entrega</th>
                                            <th className="px-4 py-3 text-center text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Estado</th>
                                            <th className="px-4 py-3 text-center text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide">Avances</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {actividades.slice(0, 10).map(a => {
                                            const est = ESTADO_CONFIG[a.estado] ?? { label: a.estado, color: 'bg-gray-100 text-gray-600' }
                                            return (
                                                <tr key={a.id} className="border-b border-[#e1e3e4] last:border-0 hover:bg-[#f8f9fa] transition-colors">
                                                    <td className="px-4 py-3 text-[14px] font-semibold text-[#191c1d]">{a.nombre}</td>
                                                    <td className="px-4 py-3 text-center text-[13px] text-[#4c616c]">
                                                        {a.fecha_limite ? new Date(a.fecha_limite).toLocaleDateString('es-CO') : '—'}
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${est.color}`}>
                                                            {est.label}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <button
                                                            onClick={() => setAvancesModal({ actividadId: a.id, actividadNombre: a.nombre })}
                                                            className="px-2.5 py-1 bg-[#d32f2f]/10 border border-[#d32f2f]/30 text-[#d32f2f] rounded-lg text-[11px] font-semibold hover:bg-[#d32f2f]/20 transition-colors">
                                                            Ver avances
                                                        </button>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                    <RegistroAvance
                        open={!!avancesModal}
                        actividadId={avancesModal?.actividadId}
                        actividadNombre={avancesModal?.actividadNombre ?? ''}
                        onClose={() => setAvancesModal(null)}
                        modoLectura={true}
                    />
                </>
            )}
        </div>
    )
}