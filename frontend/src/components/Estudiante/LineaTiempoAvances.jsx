import { useState, useEffect } from 'react'
import { avancesApi } from '../../services/estudianteApi'

function IconClock() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 5v5l3 3" />
        </svg>
    )
}

function IconLink() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 7h6M9 11h6M9 15h6M5 7h.01M5 11h.01M5 15h.01" />
        </svg>
    )
}

export default function LineaTiempoAvances({ actividadId }) {
    const [avances, setAvances] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        cargarAvances()
    }, [actividadId])

    async function cargarAvances() {
        setLoading(true)
        try {
            const data = await avancesApi.listarPorActividad(actividadId)
            setAvances(data.sort((a, b) => new Date(b.fecha_registro) - new Date(a.fecha_registro)))
        } catch (err) {
            console.error('Error al cargar avances:', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="text-center py-6 text-[#9ba7ae]">Cargando avances...</div>
    }

    if (avances.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-[13px] text-[#9ba7ae]">No hay avances registrados para esta actividad.</p>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {avances.map((avance, idx) => (
                <div key={avance.id} className="flex gap-4">
                    {/* Timeline */}
                    <div className="flex flex-col items-center">
                        <div className="w-10 h-10 rounded-full bg-[#d32f2f] flex items-center justify-center text-white font-bold text-[14px] flex-shrink-0">
                            {avance.porcentaje}%
                        </div>
                        {idx < avances.length - 1 && (
                            <div className="w-0.5 flex-1 bg-[#e1e3e4] my-2" />
                        )}
                    </div>

                    {/* Contenido */}
                    <div className="flex-1 pb-6">
                        <div className="bg-white border border-[#e1e3e4] rounded-xl p-4">
                            <div className="flex items-start justify-between gap-3 mb-2">
                                <div className="flex-1">
                                    <p className="text-[13px] font-semibold text-[#191c1d] mb-0.5">{avance.autor?.nombre || 'Autor'}</p>
                                    <div className="flex items-center gap-1.5 text-[11px] text-[#9ba7ae]">
                                        <IconClock />
                                        {new Date(avance.fecha_registro).toLocaleDateString('es-CO', {
                                            day: 'numeric',
                                            month: 'short',
                                            year: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </div>
                                </div>
                                <span className="px-2.5 py-1 rounded-lg bg-[#ffdad6] text-[#d32f2f] text-[11px] font-bold">
                                    +{avance.porcentaje}%
                                </span>
                            </div>

                            <p className="text-[14px] text-[#4c616c] leading-relaxed mb-3">{avance.descripcion}</p>

                            {avance.url_referencia && (
                                <a href={avance.url_referencia} target="_blank" rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1.5 text-[12px] text-[#d32f2f] hover:text-[#ba1a1a] font-medium transition-colors">
                                    <IconLink />
                                    Ver referencia
                                </a>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}