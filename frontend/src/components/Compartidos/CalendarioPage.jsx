import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { calendarioApi, session } from '../../services/api'
import CalendarioUnificado from './CalendarioUnificado'
import FichaEvento from './FichaEvento'
import {
    URGENCIA, TIPO_EVENTO, aISO, desdeISO, inicioMes, finMes, mismoMes, fechaLarga,
} from '../../utils/calendario'

// ── Página del calendario unificado (HU-040) ──────────────────────────────────
// Ruta /<rol>/calendario. Pide al backend solo el mes visible.

// El backend envía recordatorios de actividades a sus responsables (estudiante / líder)
const ROLES_CON_RECORDATORIO = ['estudiante', 'lider_equipo']

function Insignia({ urgencia }) {
    const u = URGENCIA[urgencia] ?? URGENCIA.normal
    return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md" style={{ color: u.color, backgroundColor: u.bg }}>
            {u.label}
        </span>
    )
}

function TarjetaEvento({ evento, onClick }) {
    const u = URGENCIA[evento.urgencia] ?? URGENCIA.normal
    return (
        <button
            type="button"
            onClick={() => onClick(evento)}
            className="w-full text-left bg-[#f8f9fa] hover:bg-[#f0f2f3] rounded-xl p-3 border-l-[3px] transition-colors"
            style={{ borderLeftColor: u.borde }}
        >
            <div className="flex items-center justify-between gap-2 mb-1.5">
                <Insignia urgencia={evento.urgencia} />
                <span className="text-[10.5px] text-[#9ba7ae]">{TIPO_EVENTO[evento.tipo] ?? evento.tipo}</span>
            </div>
            <p className="text-[13.5px] font-bold text-[#191c1d] leading-snug">{evento.titulo}</p>
            <p className="text-[11px] text-[#9ba7ae] mt-0.5 truncate">
                {[evento.curso_nombre, evento.proyecto_nombre].filter(Boolean).join(' · ')}
            </p>
        </button>
    )
}

export default function CalendarioPage() {
    const rol = session.getUser()?.tipo_rol
    const [mes, setMes] = useState(() => inicioMes(new Date()))
    const [dia, setDia] = useState(() => new Date())
    const [eventoId, setEventoId] = useState(null)

    const desde = aISO(inicioMes(mes))
    const hasta = aISO(finMes(mes))

    const { data, isLoading, isFetching, isError, refetch } = useQuery({
        queryKey: ['calendario', desde, hasta],
        queryFn: () => calendarioApi.listar(desde, hasta),
        placeholderData: keepPreviousData,
    })
    const eventos = data?.eventos ?? []

    function cambiarMes(nuevo) {
        const hoy = new Date()
        setMes(nuevo)
        setDia(mismoMes(nuevo, hoy) ? hoy : null)
        setEventoId(null)
    }

    function seleccionarDia(d) {
        setDia(d)
        setEventoId(null)
    }

    function seleccionarEvento(ev) {
        setDia(desdeISO(ev.fecha))
        setEventoId(ev.id)
    }

    const eventosDia = dia ? eventos.filter(ev => ev.fecha === aISO(dia)) : []
    const proximosDia = eventosDia.filter(ev => ev.urgencia === 'proximo').length

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <div className="mb-5">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Calendario</h1>
                <p className="text-[13px] text-[#6b7b83] mt-0.5">
                    Fechas relevantes de tus proyectos, coloreadas por urgencia.
                </p>
            </div>

            {isError && !data ? (
                <div className="bg-white border border-[#e1e3e4] rounded-2xl py-10 text-center">
                    <p className="text-[14px] font-semibold text-[#c62828]">No se pudo cargar el calendario.</p>
                    <button
                        type="button"
                        onClick={() => refetch()}
                        className="mt-3 px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors"
                    >
                        Reintentar
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_300px] gap-5 items-start">
                    <CalendarioUnificado
                        eventos={eventos}
                        mes={mes}
                        onCambiarMes={cambiarMes}
                        onSeleccionarEvento={seleccionarEvento}
                        diaSeleccionado={dia}
                        onSeleccionarDia={seleccionarDia}
                        cargando={isLoading || isFetching}
                    />

                    {/* ── Panel lateral: día seleccionado o detalle del evento ── */}
                    <aside className="bg-white border border-[#e1e3e4] rounded-2xl p-4 lg:mt-12">
                        {eventoId ? (
                            <FichaEvento eventoId={eventoId} onCerrar={() => setEventoId(null)} />
                        ) : (
                            <>
                                <h2 className="text-[15px] font-bold text-[#191c1d]">Detalle del día</h2>
                                {dia ? (
                                    <>
                                        <p className="text-[12.5px] text-[#4c616c] mt-0.5">{fechaLarga(dia)}</p>
                                        <p className="text-[11.5px] text-[#9ba7ae] mb-3">
                                            {eventosDia.length} evento{eventosDia.length !== 1 ? 's' : ''}
                                            {proximosDia > 0 && ` · ${proximosDia} próximo${proximosDia !== 1 ? 's' : ''}`}
                                        </p>
                                        {eventosDia.length === 0 ? (
                                            <p className="text-[13px] text-[#9ba7ae] py-4 text-center">Sin fechas este día.</p>
                                        ) : (
                                            <div className="flex flex-col gap-2 max-h-[460px] overflow-y-auto pr-0.5">
                                                {eventosDia.map(ev => (
                                                    <TarjetaEvento key={ev.id} evento={ev} onClick={seleccionarEvento} />
                                                ))}
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <p className="text-[13px] text-[#9ba7ae] py-4">Selecciona un día del calendario para ver sus fechas.</p>
                                )}

                                {ROLES_CON_RECORDATORIO.includes(rol) && (
                                    <div className="mt-4 rounded-xl bg-[#e3f2fd] px-3 py-2.5">
                                        <p className="text-[12px] font-bold text-[#1565c0]">Recordatorio</p>
                                        <p className="text-[12px] text-[#1565c0] mt-0.5 leading-snug">
                                            Recibirás una alerta y un correo 48 horas antes de que venza cada actividad a tu cargo.
                                        </p>
                                    </div>
                                )}
                            </>
                        )}
                    </aside>
                </div>
            )}
        </div>
    )
}
