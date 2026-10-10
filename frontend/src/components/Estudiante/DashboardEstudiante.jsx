import { useState, useEffect } from 'react'
import { misEquiposApi } from '../../services/estudianteApi'
import PendientesDashboard from '../Compartidos/PendientesDashboard'
import SemaforoPersonal from './SemaforoPersonal'

// ── Inicio del estudiante y del líder ─────────────────────────────────────────
// Pendientes y semáforo de rendimiento. Los proyectos están en "Mis proyectos".

export default function DashboardEstudiante() {
    const [equipos, setEquipos] = useState([])

    // Solo se necesitan para el selector de proyecto del semáforo
    useEffect(() => {
        let activo = true
        misEquiposApi.listar()
            .then(data => { if (activo) setEquipos(Array.isArray(data) ? data : []) })
            .catch(() => { /* sin proyectos el semáforo muestra el general */ })
        return () => { activo = false }
    }, [])

    const proyectosSemaforo = [...new Map(
        equipos.map(e => [e.proyecto.id, { id: e.proyecto.id, nombre: e.proyecto.nombre, curso: e.curso?.nombre }])
    ).values()]

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight mb-1">Inicio</h1>
                <p className="text-[13px] text-[#9ba7ae]">Tus pendientes y tu semáforo de rendimiento.</p>
            </div>

            <PendientesDashboard className="mb-6" />

            <SemaforoPersonal proyectos={proyectosSemaforo} className="mb-6" />
        </div>
    )
}
