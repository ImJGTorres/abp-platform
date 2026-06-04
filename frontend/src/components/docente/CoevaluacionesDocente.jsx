import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { evaluacionesEstudiantesApi } from '../../services/docenteApi'

const NIVEL_STYLES = {
    insuficiente:  { bg: 'bg-[#ffebee]', border: 'border-[#ef9a9a]', text: 'text-[#c62828]' },
    basico:        { bg: 'bg-[#fff8e1]', border: 'border-[#ffe082]', text: 'text-[#e65100]' },
    satisfactorio: { bg: 'bg-[#e3f2fd]', border: 'border-[#90caf9]', text: 'text-[#1565c0]' },
    excelente:     { bg: 'bg-[#e8f5e9]', border: 'border-[#a5d6a7]', text: 'text-[#2e7d32]' },
}

const ETIQUETA_DISPLAY = {
    insuficiente:  'Insuficiente',
    basico:        'Básico',
    satisfactorio: 'Satisfactorio',
    excelente:     'Excelente',
}

function formatFecha(fecha) {
    if (!fecha) return '—'
    return new Date(fecha).toLocaleDateString('es-CO', {
        day: '2-digit', month: 'short', year: 'numeric',
    })
}

function IconPeers() {
    return (
        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="7" r="3" />
            <path d="M3 20a6 6 0 0112 0" />
            <circle cx="17" cy="8" r="2.5" />
            <path d="M17 14c2.5 0 4 1.5 4 4" />
        </svg>
    )
}

function IconEmpty() {
    return (
        <svg viewBox="0 0 48 48" fill="none" className="w-16 h-16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="24" cy="24" r="20" strokeDasharray="4 3" />
            <path d="M24 16v8M24 28v2" strokeWidth="2" />
        </svg>
    )
}

function IconArrow() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4 text-[#9ba7ae]" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 10h12M12 5l5 5-5 5" />
        </svg>
    )
}

function IconChevron({ open }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" className={`w-4 h-4 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 7l5 5 5-5" />
        </svg>
    )
}

function BadgeEstado({ estado }) {
    const esEnviada = estado === 'enviada'
    return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
            esEnviada ? 'bg-[#e8f5e9] text-[#2e7d32]' : 'bg-[#fff8e1] text-[#e65100]'
        }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${esEnviada ? 'bg-[#2e7d32]' : 'bg-[#e65100]'}`} />
            {esEnviada ? 'Enviada' : 'Borrador'}
        </span>
    )
}

function TarjetaCoevaluacion({ item }) {
    const [expandida, setExpandida] = useState(false)

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 hover:border-[#d0d4d6] transition-colors">
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[14px] font-bold text-[#191c1d]">{item.evaluador_nombre}</span>
                        <IconArrow />
                        <span className="text-[14px] font-bold text-[#191c1d]">{item.evaluado_nombre}</span>
                    </div>
                    <p className="text-[12px] text-[#9ba7ae] mt-0.5">
                        {item.rubrica_nombre} · Período {item.periodo_evaluacion} · {formatFecha(item.fecha_registro)}
                    </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <BadgeEstado estado={item.estado} />
                    <span className="text-[18px] font-extrabold text-[#d32f2f]">
                        {parseFloat(item.puntuacion_total ?? 0).toFixed(1)}
                        <span className="text-[12px] font-normal text-[#9ba7ae] ml-0.5">pts</span>
                    </span>
                </div>
            </div>

            {item.comentario && (
                <div className="bg-[#f8f9fa] rounded-xl p-3 mb-3 border border-[#e1e3e4]">
                    <p className="text-[12px] font-semibold text-[#4c616c] mb-1">Comentario</p>
                    <p className="text-[13px] text-[#191c1d] leading-relaxed">{item.comentario}</p>
                </div>
            )}

            {item.detalles?.length > 0 && (
                <>
                    <button
                        onClick={() => setExpandida(e => !e)}
                        className="flex items-center gap-1.5 text-[12px] font-semibold text-[#4c616c] hover:text-[#191c1d] transition-colors mb-2"
                    >
                        <IconChevron open={expandida} />
                        {expandida ? 'Ocultar criterios' : `Ver ${item.detalles.length} criterio(s)`}
                    </button>

                    {expandida && (
                        <div className="space-y-2 mt-2">
                            {item.detalles.map((detalle, i) => {
                                const etq = detalle.nivel_etiqueta
                                const style = NIVEL_STYLES[etq] ?? NIVEL_STYLES.satisfactorio
                                return (
                                    <div key={i} className={`flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl border ${style.bg} ${style.border}`}>
                                        <span className="text-[13px] font-medium text-[#191c1d]">{detalle.criterio_nombre}</span>
                                        <div className="flex items-center gap-2 flex-shrink-0">
                                            <span className={`text-[11px] font-semibold ${style.text}`}>
                                                {ETIQUETA_DISPLAY[etq] ?? etq}
                                            </span>
                                            <span className="text-[12px] font-bold text-[#191c1d]">
                                                {parseFloat(detalle.puntos_obtenidos ?? 0).toFixed(1)} pts
                                            </span>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default function CoevaluacionesDocente() {
    const { proyectoId } = useParams()
    const [coevaluaciones, setCoevaluaciones] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [filtroEvaluado, setFiltroEvaluado] = useState('todos')

    useEffect(() => {
        setLoading(true)
        evaluacionesEstudiantesApi.listarCoevaluaciones(proyectoId)
            .then(data => setCoevaluaciones(data))
            .catch(err => setError(err?.data?.detail ?? 'Error al cargar las coevaluaciones.'))
            .finally(() => setLoading(false))
    }, [proyectoId])

    const evaluados = useMemo(() => {
        const mapa = new Map()
        coevaluaciones.forEach(c => {
            if (!mapa.has(c.id_evaluado)) {
                mapa.set(c.id_evaluado, c.evaluado_nombre)
            }
        })
        return Array.from(mapa.entries()).map(([id, nombre]) => ({ id, nombre }))
    }, [coevaluaciones])

    const filtradas = useMemo(() => {
        if (filtroEvaluado === 'todos') return coevaluaciones
        return coevaluaciones.filter(c => String(c.id_evaluado) === String(filtroEvaluado))
    }, [coevaluaciones, filtroEvaluado])

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <div className="max-w-3xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-[#ffdad6] rounded-xl flex items-center justify-center text-[#d32f2f]">
                        <IconPeers />
                    </div>
                    <div>
                        <h1 className="text-[20px] font-extrabold text-[#191c1d]">Coevaluaciones</h1>
                        <p className="text-[13px] text-[#9ba7ae]">Evaluaciones entre compañeros registradas en este proyecto</p>
                    </div>
                </div>

                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <div className="w-8 h-8 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                    </div>
                )}

                {!loading && error && (
                    <div className="bg-[#fff1f0] border border-[#ffdad6] rounded-2xl p-5 text-[#ba1a1a] text-[14px]">
                        {error}
                    </div>
                )}

                {!loading && !error && coevaluaciones.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-[#9ba7ae]">
                        <IconEmpty />
                        <p className="mt-4 text-[14px] font-medium">No hay coevaluaciones registradas aún.</p>
                        <p className="text-[12px] mt-1">Los estudiantes aún no han enviado coevaluaciones.</p>
                    </div>
                )}

                {!loading && !error && coevaluaciones.length > 0 && (
                    <>
                        {evaluados.length > 1 && (
                            <div className="flex flex-wrap gap-2 mb-5">
                                <button
                                    onClick={() => setFiltroEvaluado('todos')}
                                    className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-colors ${
                                        filtroEvaluado === 'todos'
                                            ? 'bg-[#d32f2f] text-white'
                                            : 'bg-white border border-[#e1e3e4] text-[#4c616c] hover:bg-[#f0f2f3]'
                                    }`}
                                >
                                    Todos ({coevaluaciones.length})
                                </button>
                                {evaluados.map(ev => (
                                    <button
                                        key={ev.id}
                                        onClick={() => setFiltroEvaluado(String(ev.id))}
                                        className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-colors ${
                                            String(filtroEvaluado) === String(ev.id)
                                                ? 'bg-[#d32f2f] text-white'
                                                : 'bg-white border border-[#e1e3e4] text-[#4c616c] hover:bg-[#f0f2f3]'
                                        }`}
                                    >
                                        {ev.nombre}
                                    </button>
                                ))}
                            </div>
                        )}

                        <p className="text-[13px] text-[#9ba7ae] mb-3">
                            {filtradas.length} coevaluación(es)
                        </p>

                        <div className="space-y-4">
                            {filtradas.map(item => (
                                <TarjetaCoevaluacion key={item.id} item={item} />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
