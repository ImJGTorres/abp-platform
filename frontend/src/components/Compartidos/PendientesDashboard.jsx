import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardApi } from '../../services/api'

// HU-038 — Pendientes priorizados del usuario (GET /api/dashboard/pendientes/).
// El backend ya devuelve la lista ordenada por urgencia desc y fecha asc.

const TIPO_CONFIG = {
    vencido: {
        label: 'Vencidos',
        badge: 'Vencido',
        bg: 'bg-[#fff1f0]', border: 'border-[#ffc9c5]', text: 'text-[#ba1a1a]', dot: 'bg-[#d32f2f]',
    },
    sin_calificar: {
        label: 'Sin calificar',
        badge: 'Sin calificar',
        bg: 'bg-[#fff8e1]', border: 'border-[#ffe082]', text: 'text-[#e65100]', dot: 'bg-[#f57c00]',
    },
    proximo: {
        label: 'Próximos',
        badge: 'Próximo',
        bg: 'bg-[#fffde7]', border: 'border-[#fff59d]', text: 'text-[#f57f17]', dot: 'bg-[#fbc02d]',
    },
    alerta: {
        label: 'Alertas',
        badge: 'Alerta',
        bg: 'bg-[#e3f2fd]', border: 'border-[#bbdefb]', text: 'text-[#1565c0]', dot: 'bg-[#1e88e5]',
    },
}

const ORDEN_RESUMEN = ['vencido', 'sin_calificar', 'proximo', 'alerta']

function formatearFecha(iso) {
    if (!iso) return ''
    // 'YYYY-MM-DD' → fecha local, sin desfase por zona horaria
    const [y, m, d] = iso.split('-').map(Number)
    return new Date(y, m - 1, d).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
}

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconCheck() {
    return <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12l5 5L19 7" /></svg>
}
function IconChevron() {
    return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3l5 5-5 5" /></svg>
}
function IconRefresh({ spinning }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" className={`w-4 h-4 ${spinning ? 'animate-spin' : ''}`} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4a8 8 0 0112 0M16 16a8 8 0 01-12 0" />
            <path d="M16 4v4h-4M4 16v-4h4" />
        </svg>
    )
}

// ── Item ──────────────────────────────────────────────────────────────────────

function PendienteItem({ item, onIr }) {
    const cfg = TIPO_CONFIG[item.tipo] ?? TIPO_CONFIG.alerta
    const clickable = !!item.enlace

    const contenido = (
        <>
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}`} />
            <div className="min-w-0 flex-1">
                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{item.titulo}</p>
                <div className="flex items-center gap-2 mt-0.5">
                    <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${cfg.bg} ${cfg.text}`}>{cfg.badge}</span>
                    {item.fecha && <span className="text-[11px] text-[#9ba7ae]">{formatearFecha(item.fecha)}</span>}
                </div>
            </div>
            {clickable && <span className="text-[#9ba7ae] group-hover:text-[#d32f2f] transition-colors"><IconChevron /></span>}
        </>
    )

    if (!clickable) {
        return <li className="flex items-center gap-3 px-4 py-3">{contenido}</li>
    }
    return (
        <li>
            <button
                onClick={() => onIr(item.enlace)}
                className="group w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[#f8f9fa] transition-colors"
            >
                {contenido}
            </button>
        </li>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function PendientesDashboard({ className = '' }) {
    const navigate = useNavigate()
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => { cargar() }, [])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            setData(await dashboardApi.pendientes())
        } catch (err) {
            setError(err?.data?.detail || err?.message || 'No se pudieron cargar tus pendientes.')
        } finally {
            setLoading(false)
        }
    }

    const pendientes = data?.pendientes ?? []
    const resumen = data?.resumen ?? {}
    const alDia = data?.al_dia ?? pendientes.length === 0

    return (
        <section className={`bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden ${className}`} style={{ fontFamily: "'Manrope', sans-serif" }}>
            {/* Cabecera */}
            <div className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
                <div>
                    <h2 className="text-[15px] font-extrabold text-[#191c1d]">Mis pendientes</h2>
                    <p className="text-[12px] text-[#9ba7ae]">Ordenados por urgencia</p>
                </div>
                <button
                    onClick={cargar}
                    disabled={loading}
                    title="Actualizar"
                    className="p-2 rounded-xl border border-[#e1e3e4] text-[#4c616c] hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                >
                    <IconRefresh spinning={loading} />
                </button>
            </div>

            {loading && !data ? (
                <div className="px-5 pb-5 text-[13px] text-[#9ba7ae]">Cargando pendientes...</div>
            ) : error ? (
                <div className="mx-5 mb-5 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                    {error}
                </div>
            ) : alDia ? (
                <div className="flex items-center gap-3 mx-5 mb-5 px-4 py-4 rounded-xl bg-[#e8f5e9] border border-[#c8e6c9]">
                    <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-[#2e7d32] flex-shrink-0">
                        <IconCheck />
                    </div>
                    <div>
                        <p className="text-[14px] font-bold text-[#2e7d32]">¡Estás al día!</p>
                        <p className="text-[12px] text-[#4c616c]">No tienes pendientes por ahora.</p>
                    </div>
                </div>
            ) : (
                <>
                    {/* Tarjetas de resumen por tipo */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 px-5 pb-4">
                        {ORDEN_RESUMEN.map(tipo => {
                            const cfg = TIPO_CONFIG[tipo]
                            const n = Number(resumen[tipo] ?? 0)
                            return (
                                <div key={tipo} className={`rounded-xl border px-3 py-2.5 ${n > 0 ? `${cfg.bg} ${cfg.border}` : 'bg-[#f8f9fa] border-[#f0f2f3]'}`}>
                                    <p className={`text-[22px] font-extrabold leading-none ${n > 0 ? cfg.text : 'text-[#c4c9cc]'}`}>{n}</p>
                                    <p className="text-[11px] font-semibold text-[#4c616c] mt-1">{cfg.label}</p>
                                </div>
                            )
                        })}
                    </div>

                    {/* Lista priorizada */}
                    <ul className="border-t border-[#f0f2f3] divide-y divide-[#f0f2f3] max-h-[360px] overflow-y-auto">
                        {pendientes.map((p, i) => (
                            <PendienteItem key={`${p.tipo}-${p.enlace}-${i}`} item={p} onIr={navigate} />
                        ))}
                    </ul>
                </>
            )}
        </section>
    )
}
