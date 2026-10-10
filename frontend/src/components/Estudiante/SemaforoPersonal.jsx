import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { semaforoApi } from '../../services/estudianteApi'
import Semaforo, { SEMAFORO_NIVELES } from '../Compartidos/Semaforo'

// ── Semáforo de rendimiento personal (HU-041) ─────────────────────────────────
// El nivel lo calcula el backend con la misma regla que ve el director
// (nota promedio y % de actividades incumplidas).

const ORDEN = ['rojo', 'amarillo', 'verde']

const MENSAJE = {
    rojo: 'Tu rendimiento está en nivel crítico y necesitas actuar de inmediato.',
    amarillo: 'Tu rendimiento está en riesgo: hay aspectos que requieren tu atención.',
    verde: 'Vas muy bien: mantienes tu rendimiento en nivel óptimo.',
}

// Se usan si el backend no envía recomendaciones propias
const RECOMENDACION_POR_DEFECTO = {
    rojo: 'Habla con tu docente para acordar un plan de recuperación, entrega primero los pendientes vencidos y coordina con tu equipo las entregas prioritarias.',
    amarillo: 'Prioriza las entregas que vencen pronto, acuerda con tu equipo quién cierra cada tarea pendiente y revisa la retroalimentación de tu última entrega.',
    verde: 'Mantienes tus entregas al día. Conserva este ritmo y apoya a tu equipo en las próximas fases.',
}

function hoySinHora() {
    const h = new Date()
    return new Date(h.getFullYear(), h.getMonth(), h.getDate())
}

// Etiqueta de un entregable crítico según su estado y fecha:
// "Rechazado", "Vencida hace 3 días", "Vence hoy", "Vence mañana", "Vence en 2 días"
function estadoCritico(item) {
    if (item.estado === 'rechazado') return { texto: 'Rechazado', vencida: true }
    return estadoFecha(item.fecha)
}

function estadoFecha(fechaISO) {
    if (!fechaISO) return { texto: 'Pendiente', vencida: false }
    const [a, m, d] = fechaISO.split('-').map(Number)
    const dias = Math.round((new Date(a, m - 1, d) - hoySinHora()) / 86400000)
    if (dias < 0) return { texto: `Vencida hace ${-dias} día${dias === -1 ? '' : 's'}`, vencida: true }
    if (dias === 0) return { texto: 'Vence hoy', vencida: true }
    if (dias === 1) return { texto: 'Vence mañana', vencida: false }
    return { texto: `Vence en ${dias} días`, vencida: false }
}

function IconoNivel({ nivel }) {
    const n = SEMAFORO_NIVELES[nivel]
    return (
        <div
            className="w-[84px] h-[84px] sm:w-[96px] sm:h-[96px] rounded-full flex items-center justify-center flex-shrink-0"
            style={{ border: `8px solid ${n.color}`, backgroundColor: n.bg, color: n.color }}
            aria-hidden="true"
        >
            {nivel === 'verde' ? (
                <svg viewBox="0 0 24 24" fill="none" className="w-9 h-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12l5 5L19 7" /></svg>
            ) : (
                <span className="text-[40px] font-extrabold leading-none">!</span>
            )}
        </div>
    )
}

function TituloSeccion({ children, derecha }) {
    return (
        <div className="flex items-center justify-between gap-3 flex-wrap mb-3">
            <h2 className="flex items-center gap-2 text-[15px] font-bold text-[#191c1d]">
                <span className="w-3 h-3 rounded-full border-2 border-[#d32f2f]" />
                {children}
            </h2>
            {derecha}
        </div>
    )
}

function Esqueleto() {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 animate-pulse flex items-center gap-5" aria-label="Cargando semáforo">
            <div className="w-[96px] h-[96px] rounded-full bg-[#f0f2f3] flex-shrink-0" />
            <div className="flex-1 flex flex-col gap-3">
                <div className="h-4 w-28 bg-[#f0f2f3] rounded" />
                <div className="h-5 w-3/4 bg-[#f0f2f3] rounded" />
                <div className="h-2 w-2/3 bg-[#f0f2f3] rounded" />
            </div>
            <div className="hidden sm:flex flex-col gap-2 w-40">
                <div className="h-14 bg-[#f0f2f3] rounded-xl" />
                <div className="h-14 bg-[#f0f2f3] rounded-xl" />
            </div>
        </div>
    )
}

/**
 * @param proyectos  [{ id, nombre, curso }] — si hay más de uno se muestra el selector
 */
export default function SemaforoPersonal({ proyectos = [], className = '' }) {
    const [proyectoId, setProyectoId] = useState('')

    const { data, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['semaforo-personal', proyectoId || 'todos'],
        queryFn: () => semaforoApi.personal(proyectoId || undefined),
        retry: (intentos, err) => err?.status !== 404 && intentos < 1,
    })

    const noDisponible = isError && error?.status === 404

    // Error real (no "aún no disponible") → aviso con toast
    useEffect(() => {
        if (isError && !noDisponible) toast.error('No se pudo cargar tu semáforo de rendimiento.', { id: 'semaforo-personal' })
    }, [isError, noDisponible])

    const selector = proyectos.length > 1 && (
        <select
            value={proyectoId}
            onChange={e => setProyectoId(e.target.value)}
            aria-label="Proyecto del semáforo"
            className="text-[13px] border border-[#e1e3e4] rounded-xl px-3 py-1.5 bg-white text-[#191c1d] focus:outline-none focus:border-[#d32f2f] transition-colors max-w-[260px]"
        >
            <option value="">Todos mis proyectos</option>
            {proyectos.map(p => (
                <option key={p.id} value={p.id}>{p.nombre}{p.curso ? ` · ${p.curso}` : ''}</option>
            ))}
        </select>
    )

    const nivel = ORDEN.includes(data?.nivel) ? data.nivel : null
    const cfg = nivel ? SEMAFORO_NIVELES[nivel] : null
    const criticos = data?.entregables_criticos ?? []
    const recomendaciones = data?.recomendaciones?.length ? data.recomendaciones : (nivel ? [RECOMENDACION_POR_DEFECTO[nivel]] : [])

    return (
        <section className={className} aria-label="Semáforo de rendimiento">
            <TituloSeccion derecha={selector}>Semáforo de rendimiento</TituloSeccion>

            {isLoading && <Esqueleto />}

            {noDisponible && (
                <div className="bg-white border border-dashed border-[#e1e3e4] rounded-2xl px-5 py-6 text-center text-[13px] text-[#9ba7ae]">
                    Tu semáforo de rendimiento todavía no está disponible.
                </div>
            )}

            {isError && !noDisponible && (
                <div className="bg-white border border-[#e1e3e4] rounded-2xl px-5 py-6 text-center">
                    <p className="text-[13px] text-[#c62828] font-semibold">No se pudo cargar tu semáforo.</p>
                    <button type="button" onClick={() => refetch()} className="mt-2 text-[12px] font-semibold text-[#d32f2f] underline hover:no-underline">
                        Reintentar
                    </button>
                </div>
            )}

            {data && nivel && (
                <>
                    {/* ── Tarjeta principal ─────────────────────────────────── */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 flex flex-col md:flex-row md:items-center gap-5">
                        <IconoNivel nivel={nivel} />

                        <div className="flex-1 min-w-0">
                            <Semaforo nivel={nivel} size="md" />
                            <p className="text-[18px] sm:text-[20px] font-extrabold text-[#191c1d] leading-snug mt-2.5">
                                “{MENSAJE[nivel]}”
                            </p>
                            {/* Escala de 3 niveles */}
                            <div className="grid grid-cols-3 gap-2 mt-4 max-w-[420px]">
                                {ORDEN.map(n => (
                                    <div key={n}>
                                        <div className="h-1.5 rounded-full" style={{ backgroundColor: n === nivel ? SEMAFORO_NIVELES[n].color : '#e1e3e4' }} />
                                        <p className={`text-[10.5px] mt-1 ${n === nivel ? 'font-bold text-[#191c1d]' : 'text-[#9ba7ae]'}`}>
                                            {SEMAFORO_NIVELES[n].texto}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:w-[170px] flex-shrink-0">
                            <div className="bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl px-4 py-3">
                                <p className="text-[24px] font-extrabold text-[#191c1d] leading-none">
                                    {data.nota_promedio != null ? Number(data.nota_promedio).toFixed(1) : '—'}
                                </p>
                                <p className="text-[11px] text-[#6b7b83] mt-1">Nota promedio</p>
                            </div>
                            <div className="bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl px-4 py-3">
                                <p className="text-[24px] font-extrabold leading-none" style={{ color: cfg.color }}>
                                    {Math.round(Number(data.porcentaje_actividades_incumplidas ?? 0))}%
                                </p>
                                <p className="text-[11px] text-[#6b7b83] mt-1">Actividades incumplidas</p>
                            </div>
                        </div>
                    </div>

                    {/* ── Entregables críticos (amarillo / rojo) ────────────── */}
                    {nivel !== 'verde' && criticos.length > 0 && (
                        <div className="mt-6">
                            <TituloSeccion>Entregables críticos</TituloSeccion>
                            <ol className="flex flex-col gap-3">
                                {criticos.map((ent, i) => {
                                    const f = estadoCritico(ent)
                                    const contenido = (
                                        <>
                                            <div className="min-w-0">
                                                <p className="text-[13.5px] font-bold text-[#191c1d] truncate">{ent.titulo}</p>
                                                {ent.estado === 'rechazado' && (
                                                    <p className="text-[12px] text-[#6b7b83] mt-0.5">Corrígelo y vuelve a enviarlo.</p>
                                                )}
                                            </div>
                                            <span className="text-[12px] font-bold flex-shrink-0" style={{ color: f.vencida ? SEMAFORO_NIVELES.rojo.color : '#a15c00' }}>
                                                {f.texto}
                                            </span>
                                        </>
                                    )
                                    const clases = 'flex-1 flex items-start justify-between gap-3 bg-white border border-[#e1e3e4] rounded-xl px-4 py-3'
                                    return (
                                        <li key={`${ent.estado}-${ent.titulo}-${i}`} className="flex items-start gap-3">
                                            <span className="w-7 h-7 flex-shrink-0 mt-2 rounded-md border border-[#e1e3e4] bg-white text-[11px] font-bold text-[#4c616c] flex items-center justify-center">
                                                {String(i + 1).padStart(2, '0')}
                                            </span>
                                            {ent.enlace
                                                ? <Link to={ent.enlace} className={`${clases} hover:border-[#d0d4d6] hover:shadow-sm transition-all`}>{contenido}</Link>
                                                : <div className={clases}>{contenido}</div>}
                                        </li>
                                    )
                                })}
                            </ol>
                        </div>
                    )}

                    {/* ── Recomendaciones ───────────────────────────────────── */}
                    {recomendaciones.length > 0 && (
                        <div className="mt-6 bg-[#e3f2fd] border border-[#bbdefb] rounded-2xl px-4 py-3 flex items-start gap-3">
                            <span className="w-5 h-5 rounded-full bg-[#1565c0] text-white text-[11px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">i</span>
                            <div>
                                <p className="text-[13px] font-bold text-[#0d47a1]">{nivel === 'verde' ? 'Sigue así' : 'Recomendaciones'}</p>
                                {recomendaciones.map((r, i) => (
                                    <p key={i} className="text-[12.5px] text-[#1565c0] leading-relaxed mt-0.5">{r}</p>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </section>
    )
}
