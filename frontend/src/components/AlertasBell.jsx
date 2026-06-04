import { useState, useEffect, useRef } from 'react'
import { alertasApi } from '../services/docenteApi'
import { notificacionesApi } from '../services/entregablesApi'

const TIPO_CONFIG = {
    entregable_enviado: {
        label: 'Entregable enviado',
        bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500', text: 'text-green-700', iconBg: 'bg-green-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-green-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M3 2h7l3 3v9H3V2z" /><path d="M10 2v3h3" /><path d="M6 10l2 2 3-3" />
            </svg>
        ),
    },
    actividad_vencida: {
        label: 'Actividad vencida',
        bg: 'bg-orange-50', border: 'border-orange-200', dot: 'bg-orange-500', text: 'text-orange-700', iconBg: 'bg-orange-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-orange-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <circle cx="8" cy="8" r="6" /><path d="M8 5v3.5l2 1.5" />
            </svg>
        ),
    },
    entregable_pendiente: {
        label: 'Entregable pendiente',
        bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-500', text: 'text-amber-700', iconBg: 'bg-amber-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-amber-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M4 2h5l4 4v8H4V2z" /><path d="M9 2v4h4" />
            </svg>
        ),
    },
    evaluacion_pendiente: {
        label: 'Evaluación pendiente',
        bg: 'bg-blue-50', border: 'border-blue-200', dot: 'bg-blue-500', text: 'text-blue-700', iconBg: 'bg-blue-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-blue-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5l3.5-.5L8 2z" />
            </svg>
        ),
    },
    bajo_rendimiento: {
        label: 'Bajo rendimiento',
        bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500', text: 'text-red-700', iconBg: 'bg-red-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-red-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M8 2L1.5 13h13L8 2z" /><path d="M8 6v3" /><circle cx="8" cy="11" r="0.5" fill="currentColor" />
            </svg>
        ),
    },
    // Tipos de notificaciones de entregables (para estudiantes)
    aprobado: {
        label: 'Entregable aprobado',
        bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500', text: 'text-green-700', iconBg: 'bg-green-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-green-600" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 8l3 3 7-7" />
            </svg>
        ),
    },
    rechazado: {
        label: 'Entregable rechazado',
        bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500', text: 'text-red-700', iconBg: 'bg-red-100',
        icon: (
            <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4 text-red-600" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
        ),
    },
}

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

// Normaliza una alerta al formato unificado
function normAlerta(a) {
    return {
        _id:      `a-${a.id}`,
        _src:     'alerta',
        _rawId:   a.id,
        tipo:     a.tipo,
        mensaje:  a.mensaje,
        leida:    a.estado === 'leida',
        fecha:    a.fecha_generacion,
    }
}

// Normaliza una notificación de entregable al formato unificado
function normNotif(n) {
    return {
        _id:    `n-${n.id}`,
        _src:   'notif',
        _rawId: n.id,
        tipo:   n.tipo,
        mensaje: n.mensaje,
        leida:  n.leida,
        fecha:  n.fecha_creacion,
    }
}

// pollingMinutos: intervalo de alertas del sistema (default 5)
// incluirNotificaciones: si true, también carga notificaciones de entregables (para estudiante)
export default function AlertasBell({ pollingMinutos = 5, incluirNotificaciones = false }) {
    const [open, setOpen] = useState(false)
    const [items, setItems] = useState([])
    const panelRef = useRef(null)

    const noLeidas = items.filter(i => !i.leida).length

    useEffect(() => {
        cargar()
        const ms = pollingMinutos * 60 * 1000
        const interval = setInterval(cargar, ms)
        return () => clearInterval(interval)
    }, [pollingMinutos, incluirNotificaciones])

    // Notificaciones de entregables se actualizan más seguido (30s)
    useEffect(() => {
        if (!incluirNotificaciones) return
        const interval = setInterval(cargarNotificaciones, 30000)
        return () => clearInterval(interval)
    }, [incluirNotificaciones])

    useEffect(() => {
        function handleClick(e) {
            if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false)
        }
        if (open) document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [open])

    async function cargarNotificaciones() {
        try {
            const data = await notificacionesApi.listar()
            const notifs = (Array.isArray(data) ? data : (data.results ?? [])).map(normNotif)
            setItems(prev => {
                const sinNotifs = prev.filter(i => i._src !== 'notif')
                return ordenar([...sinNotifs, ...notifs])
            })
        } catch { }
    }

    async function cargar() {
        try {
            const alertasData = alertasApi.listar('todas')
            const notifData = incluirNotificaciones ? notificacionesApi.listar() : Promise.resolve([])

            const [aRes, nRes] = await Promise.allSettled([alertasData, notifData])

            const alertas = aRes.status === 'fulfilled'
                ? (aRes.value.alertas ?? []).map(normAlerta)
                : []
            const notifs = nRes.status === 'fulfilled'
                ? (Array.isArray(nRes.value) ? nRes.value : (nRes.value.results ?? [])).map(normNotif)
                : []

            setItems(ordenar([...alertas, ...notifs]))
        } catch { }
    }

    function ordenar(lista) {
        return [...lista].sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    }

    async function marcarLeido(item) {
        if (item.leida) return
        try {
            if (item._src === 'alerta') {
                await alertasApi.marcarLeida(item._rawId)
            } else {
                await notificacionesApi.marcarLeida(item._rawId)
            }
            setItems(prev => prev.map(i => i._id === item._id ? { ...i, leida: true } : i))
        } catch { }
    }

    async function marcarTodasLeidas() {
        const pendientes = items.filter(i => !i.leida)
        await Promise.allSettled(pendientes.map(i => marcarLeido(i)))
        setItems(prev => prev.map(i => ({ ...i, leida: true })))
    }

    function formatFecha(iso) {
        if (!iso) return ''
        return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
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
                    className="absolute right-0 top-full mt-1 w-[340px] bg-white border border-[#e1e3e4] rounded-2xl shadow-xl z-50 overflow-hidden"
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
                                className="flex items-center gap-1 text-[11px] text-[#4c616c] hover:text-[#191c1d] transition-colors"
                            >
                                <IconCheck />
                                Marcar todas leídas
                            </button>
                        )}
                    </div>

                    <div className="max-h-[400px] overflow-y-auto">
                        {items.length === 0 ? (
                            <div className="py-10 text-center">
                                <div className="w-10 h-10 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-2 text-[#9ba7ae]">
                                    <IconBell />
                                </div>
                                <p className="text-[13px] text-[#9ba7ae]">Sin notificaciones</p>
                            </div>
                        ) : (
                            items.map(item => {
                                const cfg = TIPO_CONFIG[item.tipo] ?? TIPO_CONFIG.actividad_vencida
                                return (
                                    <div
                                        key={item._id}
                                        className={`px-4 py-3 border-b border-[#f0f2f3] last:border-0 transition-colors cursor-pointer ${!item.leida ? 'bg-[#fafafa] hover:bg-[#f5f5f5]' : 'bg-white hover:bg-[#f0f2f3]'}`}
                                        onClick={() => marcarLeido(item)}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`w-7 h-7 rounded-full ${cfg.iconBg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                                                {cfg.icon}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <span className={`text-[11px] font-bold ${cfg.text}`}>{cfg.label}</span>
                                                    {!item.leida && <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} flex-shrink-0`} />}
                                                </div>
                                                <p className="text-[12px] text-[#4c616c] leading-relaxed line-clamp-2">{item.mensaje}</p>
                                                <p className="text-[11px] text-[#9ba7ae] mt-1">{formatFecha(item.fecha)}</p>
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
