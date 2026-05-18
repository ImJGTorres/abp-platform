import { useState, useEffect } from 'react'
import { avancesApi } from '../../services/estudianteApi'

function IconClock() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 5v5l3 3" />
        </svg>
    )
}

function IconLink() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 11a4 4 0 005.66 0l2-2a4 4 0 00-5.66-5.66l-1 1" />
            <path d="M13 9a4 4 0 00-5.66 0l-2 2a4 4 0 005.66 5.66l1-1" />
        </svg>
    )
}

export default function LineaTiempoAvances({ actividadId, refreshKey }) {
    const [avances, setAvances] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (actividadId) cargarAvances()
    }, [actividadId, refreshKey])

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
        return <div className="text-center py-6 text-[14px] text-[#9ba7ae]">Cargando avances...</div>
    }

    if (avances.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="w-10 h-10 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-2">
                    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5 text-[#9ba7ae]" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <path d="M3 10h3l2-6 4 12 2-6h3" />
                    </svg>
                </div>
                <p className="text-[13px] font-semibold text-[#4c616c] mb-0.5">Sin avances registrados</p>
                <p className="text-[12px] text-[#9ba7ae]">Los avances que registres aparecerán aquí.</p>
            </div>
        )
    }

    return (
        <div className="space-y-3">
            {avances.map((avance, idx) => {
                const nombreAutor = avance.autor
                    ? `${avance.autor.nombre ?? ''} ${avance.autor.apellido ?? ''}`.trim() || 'Sin nombre'
                    : 'Sin nombre'

                return (
                    <div key={avance.id} className="flex gap-3">
                        <div className="flex flex-col items-center flex-shrink-0">
                            <div className="w-9 h-9 rounded-full bg-[#d32f2f] flex items-center justify-center text-white font-extrabold text-[11px] shadow-sm">
                                {avance.porcentaje_completado}%
                            </div>
                            {idx < avances.length - 1 && (
                                <div className="w-0.5 flex-1 bg-[#e1e3e4] my-1.5 min-h-[12px]" />
                            )}
                        </div>

                        <div className="flex-1 pb-3">
                            <div className="bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl p-3">
                                <div className="flex items-start justify-between gap-2 mb-1.5">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[13px] font-semibold text-[#191c1d] truncate">{nombreAutor}</p>
                                        <div className="flex items-center gap-1 text-[11px] text-[#9ba7ae] mt-0.5">
                                            <IconClock />
                                            <span>
                                                {new Date(avance.fecha_registro).toLocaleDateString('es-CO', {
                                                    day: 'numeric', month: 'short', year: 'numeric',
                                                    hour: '2-digit', minute: '2-digit',
                                                })}
                                            </span>
                                        </div>
                                    </div>
                                    <span className="px-2 py-0.5 rounded-lg bg-[#ffdad6] text-[#d32f2f] text-[11px] font-bold flex-shrink-0">
                                        {avance.porcentaje_completado}%
                                    </span>
                                </div>

                                <p className="text-[13px] text-[#4c616c] leading-relaxed">{avance.descripcion}</p>

                                {avance.url_referencia && (
                                    <a href={avance.url_referencia} target="_blank" rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1.5 text-[12px] text-[#d32f2f] hover:text-[#ba1a1a] font-medium transition-colors mt-2">
                                        <IconLink />
                                        Ver referencia
                                    </a>
                                )}
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
