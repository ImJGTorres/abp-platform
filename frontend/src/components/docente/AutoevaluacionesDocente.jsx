import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { evaluacionesEstudiantesApi } from '../../services/docenteApi'

const NIVEL_STYLES = {
    insuficiente:  { bg: 'bg-[#ffebee]', border: 'border-[#ef9a9a]', text: 'text-[#c62828]', dot: 'bg-[#ef9a9a]' },
    basico:        { bg: 'bg-[#fff8e1]', border: 'border-[#ffe082]', text: 'text-[#e65100]', dot: 'bg-[#ffe082]' },
    satisfactorio: { bg: 'bg-[#e3f2fd]', border: 'border-[#90caf9]', text: 'text-[#1565c0]', dot: 'bg-[#90caf9]' },
    excelente:     { bg: 'bg-[#e8f5e9]', border: 'border-[#a5d6a7]', text: 'text-[#2e7d32]', dot: 'bg-[#a5d6a7]' },
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

function IconSelf() {
    return (
        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20a8 8 0 0116 0" />
            <path d="M16 11l2 2 4-4" strokeWidth="2" />
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

function TarjetaAutoevaluacion({ item }) {
    const [expandida, setExpandida] = useState(false)

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 hover:border-[#d0d4d6] transition-colors">
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="min-w-0 flex-1">
                    <h3 className="text-[15px] font-bold text-[#191c1d] leading-tight">
                        {item.estudiante_nombre}
                    </h3>
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

            {item.reflexion_texto && (
                <div className="bg-[#f8f9fa] rounded-xl p-3 mb-3 border border-[#e1e3e4]">
                    <p className="text-[12px] font-semibold text-[#4c616c] mb-1">Reflexión del estudiante</p>
                    <p className="text-[13px] text-[#191c1d] leading-relaxed">{item.reflexion_texto}</p>
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

export default function AutoevaluacionesDocente() {
    const { proyectoId } = useParams()
    const [autoevaluaciones, setAutoevaluaciones] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        setLoading(true)
        evaluacionesEstudiantesApi.listarAutoevaluaciones(proyectoId)
            .then(data => setAutoevaluaciones(data))
            .catch(err => setError(err?.data?.detail ?? 'Error al cargar las autoevaluaciones.'))
            .finally(() => setLoading(false))
    }, [proyectoId])

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            <div className="max-w-3xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-[#ffdad6] rounded-xl flex items-center justify-center text-[#d32f2f]">
                        <IconSelf />
                    </div>
                    <div>
                        <h1 className="text-[20px] font-extrabold text-[#191c1d]">Autoevaluaciones</h1>
                        <p className="text-[13px] text-[#9ba7ae]">Autoevaluaciones enviadas por los estudiantes en este proyecto</p>
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

                {!loading && !error && autoevaluaciones.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-[#9ba7ae]">
                        <IconEmpty />
                        <p className="mt-4 text-[14px] font-medium">No hay autoevaluaciones registradas aún.</p>
                        <p className="text-[12px] mt-1">Los estudiantes aún no han enviado su autoevaluación.</p>
                    </div>
                )}

                {!loading && !error && autoevaluaciones.length > 0 && (
                    <div className="space-y-4">
                        <p className="text-[13px] text-[#9ba7ae] mb-2">
                            {autoevaluaciones.length} autoevaluación(es) registrada(s)
                        </p>
                        {autoevaluaciones.map(item => (
                            <TarjetaAutoevaluacion key={item.id} item={item} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
