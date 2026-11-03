import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { reportesApi } from '../../services/docenteApi'
import Semaforo, { SEMAFORO_NIVELES } from '../Compartidos/Semaforo'
import MigasDePan from '../Compartidos/MigasDePan'

// ── Panel de semáforos del docente (HU-042) ───────────────────────────────────
// Un proyecto por tarjeta con su avance y nivel. La lista que se muestra la filtra
// el backend (?color=). Los números de los botones se cuentan sobre la respuesta
// sin filtro (la misma de "Todos", que queda en caché).

const FILTROS = [
    { valor: '', label: 'Todos' },
    { valor: 'verde', label: 'Verde' },
    { valor: 'amarillo', label: 'Amarillo' },
    { valor: 'rojo', label: 'Rojo' },
]

function rutaProyecto(p) {
    return `/docente/proyectos/${p.proyecto_id}/monitoreo`
}

function TarjetaProyecto({ proyecto }) {
    const nivel = SEMAFORO_NIVELES[proyecto.nivel] ? proyecto.nivel : 'rojo'
    const cfg = SEMAFORO_NIVELES[nivel]
    const avance = Math.min(Math.max(Math.round(Number(proyecto.porcentaje_avance ?? 0)), 0), 100)
    const subtitulo = proyecto.curso_nombre

    return (
        <Link
            to={rutaProyecto(proyecto)}
            state={{ nombre: proyecto.nombre, cursoId: proyecto.curso_id, cursoNombre: proyecto.curso_nombre }}
            className="group bg-white border border-[#e1e3e4] border-l-4 rounded-xl px-4 py-4 flex flex-col gap-3 hover:shadow-md hover:border-[#d0d4d6] transition-all"
            style={{ borderLeftColor: cfg.color }}
        >
            <div className="min-w-0">
                <p className="text-[14.5px] font-bold text-[#191c1d] truncate">{proyecto.nombre}</p>
                {subtitulo && <p className="text-[11.5px] text-[#9ba7ae] truncate mt-0.5">{subtitulo}</p>}
            </div>

            <div className="flex items-center gap-3">
                <div
                    className="flex-1 h-2 bg-[#eceff1] rounded-full overflow-hidden"
                    role="progressbar" aria-valuenow={avance} aria-valuemin={0} aria-valuemax={100} aria-label="Avance del proyecto"
                >
                    <div className="h-full rounded-full transition-all duration-500" style={{ width: `${avance}%`, backgroundColor: cfg.color }} />
                </div>
                <span className="text-[13px] font-extrabold text-[#191c1d] w-10 text-right">{avance}%</span>
            </div>

            <div className="flex items-center justify-between gap-2">
                <Semaforo nivel={nivel} size="sm" />
                <span className="text-[12px] font-semibold text-[#1565c0] group-hover:underline">Ver detalle</span>
            </div>
        </Link>
    )
}

function Esqueleto() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" aria-label="Cargando proyectos">
            {Array.from({ length: 6 }, (_, i) => (
                <div key={i} className="bg-white border border-[#e1e3e4] rounded-xl p-4 animate-pulse flex flex-col gap-3">
                    <div className="h-4 w-2/3 bg-[#f0f2f3] rounded" />
                    <div className="h-3 w-1/2 bg-[#f0f2f3] rounded" />
                    <div className="h-2 w-full bg-[#f0f2f3] rounded" />
                    <div className="h-5 w-24 bg-[#f0f2f3] rounded" />
                </div>
            ))}
        </div>
    )
}

function Vacio({ titulo, texto, accion }) {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl py-14 px-4 flex flex-col items-center text-center">
            <div className="w-10 h-10 rounded-xl bg-[#eceff1] mb-4" />
            <p className="text-[14px] font-bold text-[#191c1d]">{titulo}</p>
            <p className="text-[12.5px] text-[#6b7b83] mt-1">{texto}</p>
            {accion}
        </div>
    )
}

export default function PanelSemaforosDocente() {
    const [color, setColor] = useState('')

    const reintento = (intentos, err) => err?.status !== 404 && intentos < 1

    // Lista que se muestra: filtrada por el backend
    const { data, isLoading, isFetching, isError, error, refetch } = useQuery({
        queryKey: ['semaforos-docente', color],
        queryFn: () => reportesApi.semaforosDocente(color || undefined),
        placeholderData: keepPreviousData,
        retry: reintento,
    })

    // Todos los proyectos (para los números de los botones); con "Todos" es la misma consulta
    const { data: todos } = useQuery({
        queryKey: ['semaforos-docente', ''],
        queryFn: () => reportesApi.semaforosDocente(),
        retry: reintento,
    })

    const proyectos = Array.isArray(data) ? data : []
    const conteo = Array.isArray(todos)
        ? todos.reduce((acc, p) => ({ ...acc, [p.nivel]: (acc[p.nivel] ?? 0) + 1 }), { total: todos.length, verde: 0, amarillo: 0, rojo: 0 })
        : {}
    const noDisponible = isError && error?.status === 404
    const nombreFiltro = FILTROS.find(f => f.valor === color)?.label

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <MigasDePan items={[
                { label: 'Mis cursos', to: '/docente/cursos' },
                { label: 'Panel de semáforos' },
            ]} />

            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Panel de semáforos</h1>
                <p className="text-[13px] text-[#6b7b83] mt-0.5">
                    Vista panorámica del avance y del nivel de rendimiento de cada proyecto a tu cargo.
                </p>
            </div>

            <h2 className="flex items-center gap-2 text-[15px] font-bold text-[#191c1d] mb-3">
                <span className="w-3 h-3 rounded-full border-2 border-[#d32f2f]" />
                Proyectos
            </h2>

            {/* ── Filtro por color (lo aplica la API) ───────────────────── */}
            <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Filtrar por nivel">
                {FILTROS.map(f => {
                    const activo = color === f.valor
                    const cantidad = f.valor ? conteo[f.valor] : conteo.total
                    return (
                        <button
                            key={f.label}
                            type="button"
                            onClick={() => setColor(f.valor)}
                            aria-pressed={activo}
                            disabled={noDisponible}
                            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg border text-[13px] font-semibold transition-colors disabled:opacity-50 ${
                                activo
                                    ? 'bg-[#d32f2f] border-[#d32f2f] text-white'
                                    : 'bg-white border-[#d0d4d6] text-[#191c1d] hover:bg-[#f0f2f3]'
                            }`}
                        >
                            {f.valor && (
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: activo ? '#fff' : SEMAFORO_NIVELES[f.valor].color }} />
                            )}
                            {f.label}
                            {cantidad != null && (
                                <span className={`text-[12px] font-medium ${activo ? 'text-white/80' : 'text-[#9ba7ae]'}`}>{cantidad}</span>
                            )}
                        </button>
                    )
                })}
            </div>

            {/* ── Contenido ─────────────────────────────────────────────── */}
            {isLoading ? (
                <Esqueleto />
            ) : noDisponible ? (
                <Vacio titulo="El panel de semáforos todavía no está disponible" texto="Vuelve a intentarlo más tarde." />
            ) : isError ? (
                <Vacio
                    titulo="No se pudo cargar el panel de semáforos"
                    texto="Revisa tu conexión e intenta de nuevo."
                    accion={
                        <button type="button" onClick={() => refetch()} className="mt-4 px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-lg hover:bg-[#b71c1c] transition-colors">
                            Reintentar
                        </button>
                    }
                />
            ) : proyectos.length === 0 ? (
                color ? (
                    <Vacio
                        titulo="No hay proyectos en este nivel"
                        texto={`Cuando un proyecto alcance el nivel ${nombreFiltro} aparecerá aquí.`}
                        accion={
                            <button type="button" onClick={() => setColor('')} className="mt-4 px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-lg hover:bg-[#b71c1c] transition-colors">
                                Ver todos
                            </button>
                        }
                    />
                ) : (
                    <Vacio titulo="Aún no tienes proyectos a cargo" texto="Cuando crees proyectos en tus cursos aparecerán aquí con su semáforo." />
                )
            ) : (
                <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 transition-opacity ${isFetching ? 'opacity-60' : ''}`}>
                    {proyectos.map(p => <TarjetaProyecto key={p.proyecto_id} proyecto={p} />)}
                </div>
            )}
        </div>
    )
}
