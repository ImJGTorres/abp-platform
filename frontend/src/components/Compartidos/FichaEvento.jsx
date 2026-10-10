import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { calendarioApi } from '../../services/api'
import { URGENCIA, TIPO_EVENTO, desdeISO, fechaLarga } from '../../utils/calendario'

// ── Ficha de detalle de un evento del calendario (HU-040) ─────────────────────
// Panel lateral que se abre al pulsar un evento. Datos de GET /api/calendario/:id/

const ESTADOS = {
    pendiente: 'Pendiente', en_progreso: 'En progreso', completada: 'Completada', bloqueada: 'Bloqueada',
    completado: 'Completado', cancelado: 'Cancelado', activo: 'Activo',
}

function Insignia({ urgencia }) {
    const u = URGENCIA[urgencia] ?? URGENCIA.normal
    return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md" style={{ color: u.color, backgroundColor: u.bg }}>
            {u.label}
        </span>
    )
}

function Cargando() {
    return (
        <div className="flex flex-col gap-3 animate-pulse" aria-label="Cargando evento">
            <div className="h-4 w-24 bg-[#f0f2f3] rounded" />
            <div className="h-5 w-3/4 bg-[#f0f2f3] rounded" />
            <div className="h-3 w-1/2 bg-[#f0f2f3] rounded" />
            <div className="h-14 bg-[#f0f2f3] rounded-lg" />
            <div className="h-9 bg-[#f0f2f3] rounded-xl" />
        </div>
    )
}

/**
 * @param eventoId  id del evento ('hito-<id>' o 'actividad-<id>')
 * @param onCerrar  vuelve a la lista del día
 */
export default function FichaEvento({ eventoId, onCerrar }) {
    const { data, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['calendario-evento', eventoId],
        queryFn: () => calendarioApi.detalle(eventoId),
        retry: (intentos, err) => err?.status !== 404 && intentos < 1,
    })

    const avance = Math.min(Math.max(Math.round(Number(data?.porcentaje_avance ?? 0)), 0), 100)
    const u = URGENCIA[data?.urgencia] ?? URGENCIA.normal

    return (
        <div>
            <button
                type="button"
                onClick={onCerrar}
                className="flex items-center gap-1 text-[12px] font-semibold text-[#9ba7ae] hover:text-[#4c616c] mb-3"
            >
                <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                Volver al día
            </button>

            {isLoading && <Cargando />}

            {isError && (
                <div className="py-6 text-center">
                    {error?.status === 404 ? (
                        <p className="text-[13px] font-semibold text-[#4c616c]">El evento ya no está disponible.</p>
                    ) : (
                        <>
                            <p className="text-[13px] font-semibold text-[#c62828]">No se pudo cargar el detalle del evento.</p>
                            <button
                                type="button"
                                onClick={() => refetch()}
                                className="mt-2 text-[12px] font-semibold text-[#d32f2f] underline hover:no-underline"
                            >
                                Reintentar
                            </button>
                        </>
                    )}
                </div>
            )}

            {data && (
                <div className="flex flex-col gap-3">
                    {/* Título, tipo y fecha */}
                    <div>
                        <div className="flex items-center gap-2 mb-1.5">
                            <Insignia urgencia={data.urgencia} />
                            <span className="text-[11px] text-[#9ba7ae]">{TIPO_EVENTO[data.tipo] ?? data.tipo}</span>
                        </div>
                        <h3 className="text-[16px] font-extrabold text-[#191c1d] leading-snug">{data.titulo}</h3>
                        <p className="text-[12px] text-[#6b7b83] mt-1">{fechaLarga(desdeISO(data.fecha))}</p>
                        <p className="text-[12px] text-[#9ba7ae]">{[data.curso_nombre, data.proyecto_nombre].filter(Boolean).join(' · ')}</p>
                    </div>

                    {data.descripcion && (
                        <p className="text-[13px] text-[#4c616c] whitespace-pre-line">{data.descripcion}</p>
                    )}

                    {/* Avance */}
                    <div className="bg-[#f8f9fa] rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1.5">
                            <p className="text-[10px] font-bold uppercase tracking-[0.5px] text-[#9ba7ae]">Avance</p>
                            <p className="text-[13px] font-extrabold" style={{ color: u.color }}>{avance}%</p>
                        </div>
                        <div
                            className="h-2 bg-[#e1e3e4] rounded-full overflow-hidden"
                            role="progressbar" aria-valuenow={avance} aria-valuemin={0} aria-valuemax={100}
                        >
                            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${avance}%`, backgroundColor: u.borde }} />
                        </div>
                        {data.estado && (
                            <p className="text-[11px] text-[#6b7b83] mt-1.5">Estado: <span className="font-semibold text-[#191c1d]">{ESTADOS[data.estado] ?? data.estado}</span></p>
                        )}
                    </div>

                    {/* Equipo */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.5px] text-[#9ba7ae] mb-1.5">
                            Equipo{data.equipo?.nombre ? ` · ${data.equipo.nombre}` : ''}
                        </p>
                        {data.equipo?.miembros?.length > 0 ? (
                            <div className="flex flex-wrap gap-1.5">
                                {data.equipo.miembros.map(m => (
                                    <span key={m} className="text-[11.5px] text-[#4c616c] bg-[#f0f2f3] rounded-lg px-2 py-1">{m}</span>
                                ))}
                            </div>
                        ) : (
                            <p className="text-[12px] text-[#9ba7ae]">Sin equipo asignado.</p>
                        )}
                    </div>

                    {/* Enlace directo */}
                    {data.enlace && (
                        <Link
                            to={data.enlace}
                            className="mt-1 text-center px-4 py-2.5 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors"
                        >
                            {data.tipo === 'actividad' ? 'Ir a la actividad' : 'Ver en el proyecto'}
                        </Link>
                    )}
                </div>
            )}
        </div>
    )
}
