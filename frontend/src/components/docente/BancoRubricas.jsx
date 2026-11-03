import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { reportesApi, rubricasApi } from '../../services/docenteApi'
import CatalogoPlantillas from './CatalogoPlantillas'
import MigasDePan from '../Compartidos/MigasDePan'

// ── Banco de rúbricas (HU-044) ───────────────────────────────────────────────
// Acceso directo al catálogo de plantillas desde el menú del docente: se elige el
// proyecto destino, se escoge una plantilla y se clona en ese proyecto.
// Los proyectos salen del panel de semáforos (mismos proyectos activos del docente).

export default function BancoRubricas() {
    const navigate = useNavigate()
    const [proyectoId, setProyectoId] = useState('')
    const [catalogoAbierto, setCatalogoAbierto] = useState(false)
    const [clonando, setClonando] = useState(false)

    const { data, isLoading, isError } = useQuery({
        queryKey: ['semaforos-docente', ''],
        queryFn: () => reportesApi.semaforosDocente(),
    })
    const proyectos = Array.isArray(data) ? data : []
    const proyecto = proyectos.find(p => String(p.proyecto_id) === proyectoId)

    async function usarPlantilla(plantilla) {
        if (!proyecto || clonando) return
        setClonando(true)
        try {
            await rubricasApi.clonar(plantilla.id, proyecto.proyecto_id)
            toast.success('Rúbrica creada desde la plantilla. Ya puedes editarla.')
            navigate(`/docente/proyectos/${proyecto.proyecto_id}/rubricas`, {
                state: { nombre: proyecto.nombre, cursoId: proyecto.curso_id, cursoNombre: proyecto.curso_nombre },
            })
        } catch (err) {
            toast.error(err?.data?.detail || err?.data?.error || 'No se pudo clonar la plantilla.')
        } finally {
            setClonando(false)
        }
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <MigasDePan items={[
                { label: 'Mis cursos', to: '/docente/cursos' },
                { label: 'Banco de rúbricas' },
            ]} />

            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Banco de rúbricas</h1>
                <p className="text-[13px] text-[#6b7b83] mt-0.5">
                    Reutiliza una plantilla en cualquiera de tus proyectos. Para guardar una rúbrica como plantilla,
                    ábrela desde el menú del proyecto → Rúbricas.
                </p>
            </div>

            <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 max-w-xl flex flex-col gap-4">
                <div>
                    <label htmlFor="banco-proyecto" className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#6b7b83] block mb-1.5">
                        Proyecto destino
                    </label>
                    <select
                        id="banco-proyecto"
                        value={proyectoId}
                        onChange={e => setProyectoId(e.target.value)}
                        disabled={isLoading || isError || proyectos.length === 0}
                        className="w-full px-3 py-2 text-[13px] text-[#191c1d] bg-white border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] disabled:opacity-60"
                    >
                        <option value="">
                            {isLoading ? 'Cargando proyectos…'
                                : isError ? 'No se pudieron cargar tus proyectos'
                                : proyectos.length === 0 ? 'No tienes proyectos activos'
                                : 'Selecciona un proyecto'}
                        </option>
                        {proyectos.map(p => (
                            <option key={p.proyecto_id} value={p.proyecto_id}>{p.nombre} — {p.curso_nombre}</option>
                        ))}
                    </select>
                </div>

                <div className="flex flex-wrap gap-2">
                    <button
                        type="button"
                        onClick={() => setCatalogoAbierto(true)}
                        disabled={!proyecto}
                        className="px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-50"
                    >
                        Crear desde plantilla
                    </button>
                    <button
                        type="button"
                        onClick={() => navigate(`/docente/proyectos/${proyecto.proyecto_id}/rubricas`, {
                            state: { nombre: proyecto.nombre, cursoId: proyecto.curso_id, cursoNombre: proyecto.curso_nombre },
                        })}
                        disabled={!proyecto}
                        className="px-4 py-2 bg-[#f0f2f3] text-[#4c616c] text-[13px] font-semibold rounded-xl hover:bg-[#e1e3e4] transition-colors disabled:opacity-50"
                    >
                        Ver rúbricas del proyecto
                    </button>
                </div>
            </div>

            {catalogoAbierto && (
                <CatalogoPlantillas
                    onSeleccionar={usarPlantilla}
                    onCerrar={() => setCatalogoAbierto(false)}
                    procesando={clonando}
                />
            )}
        </div>
    )
}
