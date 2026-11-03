import {
    DIAS_SEMANA, URGENCIA, aISO, desdeISO, inicioMes, finMes, sumarMeses,
    mismoDia, mismoMes, tituloMes, fechaCorta,
} from '../../utils/calendario'

// ── Calendario unificado (HU-040) ─────────────────────────────────────────────
// Agenda mensual con CSS grid (lunes a domingo), sin librerías externas.
// En pantallas pequeñas se muestra como lista de días con eventos.

const MAX_POR_DIA = 3

function IconChevron({ dir }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d={dir === 'izq' ? 'M12 4L6 10l6 6' : 'M8 4l6 6-6 6'} />
        </svg>
    )
}

function Pildora({ evento, onClick }) {
    const u = URGENCIA[evento.urgencia] ?? URGENCIA.normal
    return (
        <button
            type="button"
            onClick={e => { e.stopPropagation(); onClick?.(evento) }}
            title={`${evento.titulo} · ${u.label}`}
            className="w-full text-left truncate text-[10.5px] font-semibold leading-tight px-1.5 py-[3px] rounded border-l-[3px] hover:brightness-95 transition"
            style={{ color: u.color, backgroundColor: u.bg, borderLeftColor: u.borde }}
        >
            {evento.titulo}
        </button>
    )
}

/**
 * @param eventos             eventos del backend ({ id, titulo, fecha 'AAAA-MM-DD', urgencia, ... })
 * @param mes                 Date de cualquier día del mes visible
 * @param onCambiarMes        (Date primer día del nuevo mes) => void
 * @param onSeleccionarEvento (evento) => void
 * @param diaSeleccionado     Date opcional, se resalta en la cuadrícula
 * @param onSeleccionarDia    (Date) => void opcional, al pulsar un día o "+N más"
 * @param cargando            muestra el calendario atenuado mientras llegan los datos
 */
export default function CalendarioUnificado({
    eventos = [], mes, onCambiarMes, onSeleccionarEvento,
    diaSeleccionado = null, onSeleccionarDia, cargando = false,
}) {
    const hoy = new Date()
    const primero = inicioMes(mes)
    const diasDelMes = finMes(mes).getDate()
    const desplazamiento = (primero.getDay() + 6) % 7 // lunes = 0

    // Celdas de la cuadrícula: null para los días fuera del mes
    const total = Math.ceil((desplazamiento + diasDelMes) / 7) * 7
    const celdas = Array.from({ length: total }, (_, i) => {
        const n = i - desplazamiento + 1
        return n >= 1 && n <= diasDelMes ? new Date(primero.getFullYear(), primero.getMonth(), n) : null
    })

    // Eventos agrupados por día (solo los del mes visible)
    const porDia = new Map()
    for (const ev of eventos) {
        if (!ev?.fecha || !mismoMes(desdeISO(ev.fecha), primero)) continue
        if (!porDia.has(ev.fecha)) porDia.set(ev.fecha, [])
        porDia.get(ev.fecha).push(ev)
    }

    const diasConEventos = [...porDia.keys()].sort()

    return (
        <div>
            {/* ── Encabezado: mes, navegación y leyenda ────────────────────── */}
            <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => onCambiarMes(sumarMeses(primero, -1))}
                        aria-label="Mes anterior"
                        className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#e1e3e4] bg-white text-[#4c616c] hover:bg-[#f0f2f3] transition-colors"
                    >
                        <IconChevron dir="izq" />
                    </button>
                    <h2 className="text-[17px] font-extrabold text-[#191c1d] min-w-[150px] text-center tracking-tight">
                        {tituloMes(primero)}
                    </h2>
                    <button
                        type="button"
                        onClick={() => onCambiarMes(sumarMeses(primero, 1))}
                        aria-label="Mes siguiente"
                        className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#e1e3e4] bg-white text-[#4c616c] hover:bg-[#f0f2f3] transition-colors"
                    >
                        <IconChevron dir="der" />
                    </button>
                    <button
                        type="button"
                        onClick={() => onCambiarMes(inicioMes(new Date()))}
                        className="ml-1 px-3.5 h-8 rounded-lg border border-[#d32f2f] text-[#d32f2f] text-[12.5px] font-semibold hover:bg-[#fff1f0] transition-colors"
                    >
                        Hoy
                    </button>
                </div>
                <div className="flex items-center gap-4">
                    {Object.entries(URGENCIA).map(([clave, u]) => (
                        <span key={clave} className="flex items-center gap-1.5 text-[12px] text-[#4c616c]">
                            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: u.borde }} />
                            {u.label}
                        </span>
                    ))}
                </div>
            </div>

            <div className={`transition-opacity ${cargando ? 'opacity-60' : ''}`}>
                {/* ── Cuadrícula mensual (md en adelante) ─────────────────── */}
                <div className="hidden md:block bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden">
                    <div className="grid grid-cols-7 bg-[#f8f9fa] border-b border-[#e1e3e4]">
                        {DIAS_SEMANA.map(d => (
                            <div key={d} className="py-2 text-center text-[11px] font-bold uppercase tracking-[0.5px] text-[#6b7b83]">{d}</div>
                        ))}
                    </div>
                    <div className="grid grid-cols-7">
                        {celdas.map((dia, i) => {
                            const finFila = i % 7 === 6
                            const ultimaFila = i >= celdas.length - 7
                            const bordes = `${finFila ? '' : 'border-r'} ${ultimaFila ? '' : 'border-b'} border-[#f0f2f3]`
                            if (!dia) return <div key={`vacio-${i}`} className={`min-h-[108px] bg-[#fafbfb] ${bordes}`} />

                            const lista = porDia.get(aISO(dia)) ?? []
                            const esHoy = mismoDia(dia, hoy)
                            const seleccionado = mismoDia(dia, diaSeleccionado)
                            const extra = lista.length - MAX_POR_DIA
                            return (
                                <div
                                    key={aISO(dia)}
                                    onClick={() => onSeleccionarDia?.(dia)}
                                    className={`min-h-[108px] p-1.5 flex flex-col gap-1 cursor-pointer transition-colors ${bordes} ${seleccionado ? 'bg-[#fff1f0]' : 'hover:bg-[#fafafa]'}`}
                                >
                                    <button
                                        type="button"
                                        onClick={e => { e.stopPropagation(); onSeleccionarDia?.(dia) }}
                                        aria-label={`Ver el día ${dia.getDate()}`}
                                        className={`self-start w-6 h-6 flex items-center justify-center rounded-full text-[12px] font-semibold ${esHoy ? 'bg-[#d32f2f] text-white' : 'text-[#4c616c]'}`}
                                    >
                                        {dia.getDate()}
                                    </button>
                                    {lista.slice(0, MAX_POR_DIA).map(ev => (
                                        <Pildora key={ev.id} evento={ev} onClick={onSeleccionarEvento} />
                                    ))}
                                    {extra > 0 && (
                                        <button
                                            type="button"
                                            onClick={e => { e.stopPropagation(); onSeleccionarDia?.(dia) }}
                                            className="self-start text-[10.5px] font-semibold text-[#6b7b83] hover:text-[#191c1d] px-1"
                                        >
                                            +{extra} más
                                        </button>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* ── Lista por día (pantallas pequeñas) ──────────────────── */}
                <div className="md:hidden flex flex-col gap-3">
                    {diasConEventos.length === 0 ? (
                        <p className="bg-white border border-[#e1e3e4] rounded-2xl py-8 text-center text-[13px] text-[#9ba7ae]">
                            No hay fechas en {tituloMes(primero).toLowerCase()}.
                        </p>
                    ) : diasConEventos.map(clave => {
                        const dia = desdeISO(clave)
                        return (
                            <div key={clave} className="bg-white border border-[#e1e3e4] rounded-2xl p-3">
                                <p className="text-[12px] font-bold text-[#191c1d] mb-2 flex items-center gap-2">
                                    {fechaCorta(dia)}
                                    {mismoDia(dia, hoy) && <span className="text-[10px] font-bold text-white bg-[#d32f2f] rounded-full px-2 py-0.5">Hoy</span>}
                                </p>
                                <div className="flex flex-col gap-1.5">
                                    {porDia.get(clave).map(ev => {
                                        const u = URGENCIA[ev.urgencia] ?? URGENCIA.normal
                                        return (
                                            <button
                                                key={ev.id}
                                                type="button"
                                                onClick={() => onSeleccionarEvento?.(ev)}
                                                className="w-full text-left px-3 py-2 rounded-lg border-l-[3px]"
                                                style={{ backgroundColor: u.bg, borderLeftColor: u.borde }}
                                            >
                                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{ev.titulo}</p>
                                                <p className="text-[11px] mt-0.5" style={{ color: u.color }}>
                                                    {u.label}{ev.curso_nombre ? ` · ${ev.curso_nombre}` : ''}
                                                </p>
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
