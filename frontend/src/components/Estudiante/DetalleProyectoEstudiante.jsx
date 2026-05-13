import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { estudianteProyectosApi } from '../../services/estudianteApi'

export default function DetalleProyectoEstudiante() {
    const { proyectoId } = useParams()
    const [proyecto, setProyecto] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        cargarProyecto()
    }, [proyectoId])

    async function cargarProyecto() {
        setLoading(true)
        try {
            const data = await estudianteProyectosApi.obtener(proyectoId)
            setProyecto(data)
        } catch (err) {
            console.error('Error al cargar proyecto:', err)
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

    if (!proyecto) {
        return (
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-5xl mx-auto text-center py-12">
                    <p className="text-[#9ba7ae]">Proyecto no encontrado.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
                <div className="mb-4">
                    <Link to="/estudiante/dashboard" className="text-[13px] text-[#d32f2f] hover:text-[#ba1a1a] font-medium transition-colors">
                        ← Volver al inicio
                    </Link>
                </div>

                <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-2">{proyecto.nombre}</h1>
                <p className="text-[14px] text-[#9ba7ae] mb-6">{proyecto.descripcion}</p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white border border-[#e1e3e4] rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-1">Fecha Inicio</p>
                        <p className="text-[15px] font-bold text-[#191c1d]">
                            {new Date(proyecto.fecha_inicio).toLocaleDateString('es-CO')}
                        </p>
                    </div>
                    <div className="bg-white border border-[#e1e3e4] rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-1">Fecha Fin Estimada</p>
                        <p className="text-[15px] font-bold text-[#191c1d]">
                            {proyecto.fecha_fin_estimada ? new Date(proyecto.fecha_fin_estimada).toLocaleDateString('es-CO') : 'Sin definir'}
                        </p>
                    </div>
                    <div className="bg-white border border-[#e1e3e4] rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase mb-1">Equipo</p>
                        <p className="text-[15px] font-bold text-[#191c1d]">{proyecto.equipo?.nombre || 'Sin asignar'}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Link to={`/estudiante/proyectos/${proyectoId}/kanban`}
                        className="bg-white border border-[#e1e3e4] rounded-xl p-6 hover:shadow-lg transition-shadow">
                        <h3 className="text-[17px] font-bold text-[#191c1d] mb-2">📋 Tablero Kanban</h3>
                        <p className="text-[13px] text-[#9ba7ae]">Ver y gestionar actividades del proyecto</p>
                    </Link>
                    <Link to={`/estudiante/proyectos/${proyectoId}/progreso`}
                        className="bg-white border border-[#e1e3e4] rounded-xl p-6 hover:shadow-lg transition-shadow">
                        <h3 className="text-[17px] font-bold text-[#191c1d] mb-2">📊 Dashboard</h3>
                        <p className="text-[13px] text-[#9ba7ae]">Ver progreso y métricas del proyecto</p>
                    </Link>
                </div>
            </div>
        </div>
    )
}