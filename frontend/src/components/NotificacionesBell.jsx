import { useState, useEffect, useRef } from 'react'
import { notificacionesApi } from '../services/entregablesApi'

function IconBell() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 2a6 6 0 00-6 6v3l-1.5 2.5h15L16 11V8a6 6 0 00-6-6z" />
            <path d="M8 16a2 2 0 004 0" />
        </svg>
    )
}

function IconCheck() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 8l3 3 7-7" />
        </svg>
    )
}

const TIPO_CONFIG = {
    aprobado: {
        label: 'Aprobado',
        bg: 'bg-green-50',
        border: 'border-green-200',
        dot: 'bg-green-500',
        text: 'text-green-700',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-green-600" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 8l3 3 7-7" />
            </svg>
        ),
    },
    rechazado: {
        label: 'Rechazado',
        bg: 'bg-red-50',
        border: 'border-red-200',
        dot: 'bg-red-500',
        text: 'text-red-700',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-red-600" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
        ),
    },
}

export default function NotificacionesBell() {
    const [open, setOpen] = useState(false)
    const [notificaciones, setNotificaciones] = useState([])
    const [cargando, setCargando] = useState(false)
    const panelRef = useRef(null)

    const noLeidas = notificaciones.filter(n => !n.leida).length

    useEffect(() => {
        cargarNotificaciones()
        const interval = setInterval(cargarNotificaciones, 30000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        function handleClick(e) {
            if (panelRef.current && !panelRef.current.contains(e.target)) {
                setOpen(false)
            }
        }
        if (open) document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [open])

    async function cargarNotificaciones() {
        try {
            const data = await notificacionesApi.listar()
            setNotificaciones(data)
        } catch {
            // silenciar
        }
    }

    async function marcarLeida(id) {
        try {
            await notificacionesApi.marcarLeida(id)
            setNotificaciones(prev => prev.map(n => n.id === id ? { ...n, leida: true } : n))
        } catch { }
    }

    async function marcarTodasLeidas() {
        setCargando(true)
        try {
            await notificacionesApi.marcarTodasLeidas()
            setNotificaciones(prev => prev.map(n => ({ ...n, leida: true })))
        } catch { }
        finally { setCargando(false) }
    }

    function formatFecha(iso) {
        if (!iso) return ''
        const d = new Date(iso)
        return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
    }

    return (
        <div className="relative" ref={panelRef}>
            <button
                onClick={e => { e.stopPropagation(); setOpen(o => !o) }}
                className="relative flex items-center justify-center w-9 h-9 rounded-xl hover:bg-[#f0f2f3] transition-colors text-[#4c616c]"
                title="Notificaciones"
            >
                <IconBell />
                {noLeidas > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 bg-[#d32f2f] text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                        {noLeidas > 9 ? '9+' : noLeidas}
                    </span>
                )}
            </button>

            {open && (
                <div
                    className="absolute right-0 top-full mt-1 w-80 bg-white border border-[#e1e3e4] rounded-2xl shadow-xl z-50 overflow-hidden"
                    onClick={e => e.stopPropagation()}
                >
                    <div className="flex items-center justify-between px-4 py-3 border-b border-[#e1e3e4]">
                        <h3 className="text-[14px] font-bold text-[#191c1d]">
                            Notificaciones
                            {noLeidas > 0 && (
                                <span className="ml-2 px-1.5 py-0.5 bg-[#d32f2f] text-white text-[10px] font-bold rounded-full">
                                    {noLeidas}
                                </span>
                            )}
                        </h3>
                        {noLeidas > 0 && (
                            <button
                                onClick={marcarTodasLeidas}
                                disabled={cargando}
                                className="flex items-center gap-1 text-[11px] text-[#4c616c] hover:text-[#191c1d] transition-colors disabled:opacity-50"
                            >
                                <IconCheck />
                                Marcar todas leídas
                            </button>
                        )}
                    </div>

                    <div className="max-h-[360px] overflow-y-auto">
                        {notificaciones.length === 0 ? (
                            <div className="py-10 text-center">
                                <div className="w-10 h-10 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-2 text-[#9ba7ae]">
                                    <IconBell />
                                </div>
                                <p className="text-[13px] text-[#9ba7ae]">Sin notificaciones</p>
                            </div>
                        ) : (
                            notificaciones.map(n => {
                                const cfg = TIPO_CONFIG[n.tipo] || TIPO_CONFIG.aprobado
                                return (
                                    <div
                                        key={n.id}
                                        className={`px-4 py-3 border-b border-[#f0f2f3] last:border-0 cursor-pointer transition-colors ${n.leida ? 'bg-white' : 'bg-[#fafafa]'} hover:bg-[#f0f2f3]`}
                                        onClick={() => !n.leida && marcarLeida(n.id)}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`w-7 h-7 rounded-full ${n.tipo === 'aprobado' ? 'bg-green-100' : 'bg-red-100'} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                                                {cfg.icon}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <span className={`text-[11px] font-bold ${cfg.text}`}>{cfg.label}</span>
                                                    {!n.leida && (
                                                        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} flex-shrink-0`} />
                                                    )}
                                                </div>
                                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{n.titulo_entregable}</p>
                                                {n.retroalimentacion && (
                                                    <p className="text-[12px] text-[#4c616c] mt-0.5 line-clamp-2">{n.retroalimentacion}</p>
                                                )}
                                                <p className="text-[11px] text-[#9ba7ae] mt-1">{formatFecha(n.fecha_creacion)}</p>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
