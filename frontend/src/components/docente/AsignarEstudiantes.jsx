import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { equiposApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']

function avatar(nombre, apellido) {
    const n = nombre?.[0]?.toUpperCase()  ?? ''
    const a = apellido?.[0]?.toUpperCase() ?? ''
    return n + a
}

function colorFor(id) {
    return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function AsignarEstudiantes() {
    const { equipoId } = useParams()
    const navigate     = useNavigate()

    const [datos, setDatos]             = useState(null)
    const [loading, setLoading]         = useState(true)
    const [asignando, setAsignando]     = useState(false)
    const [error, setError]             = useState(null)
    const [busqueda, setBusqueda]       = useState('')
    const [seleccionados, setSeleccionados] = useState(new Set())

    useEffect(() => { cargarDatos() }, [equipoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        setSeleccionados(new Set())
        try {
            const data = await equiposApi.obtenerEstudiantes(equipoId)
            setDatos(data)
        } catch {
            setError('No se pudo cargar la lista de estudiantes.')
        } finally {
            setLoading(false)
        }
    }

    async function handleAsignar() {
        if (seleccionados.size === 0) return
        setAsignando(true)
        try {
            await equiposApi.asignarEstudiantes(equipoId, [...seleccionados])
            await cargarDatos()
        } catch {
            setError('Error al asignar estudiantes. Inténtalo de nuevo.')
        } finally {
            setAsignando(false)
        }
    }

    function toggleSeleccion(id) {
        setSeleccionados(prev => {
            const next = new Set(prev)
            next.has(id) ? next.delete(id) : next.add(id)
            return next
        })
    }

    const disponiblesFiltrados = useMemo(() => {
        if (!datos) return []
        const q = busqueda.toLowerCase()
        if (!q) return datos.disponibles
        return datos.disponibles.filter(e =>
            `${e.nombre} ${e.apellido}`.toLowerCase().includes(q) ||
            e.correo.toLowerCase().includes(q)
        )
    }, [datos, busqueda])

    const miembrosActuales = datos?.cantidad_miembros ?? 0
    const cupoMaximo       = datos?.equipo?.cupo_maximo ?? 0
    const ocupados         = miembrosActuales + seleccionados.size
    const cupoLleno        = ocupados >= cupoMaximo

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
            </div>
        )
    }

    return (
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-5 flex items-center gap-2 text-[13px]">
                <button onClick={() => navigate(-1)} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                    Equipos
                </button>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="font-semibold text-[#191c1d]">{datos?.equipo?.nombre ?? 'Asignar estudiantes'}</span>
            </div>

            {error && (
                <div className="mb-4 px-4 py-3 rounded-xl bg-[#ffdad6] text-[#ba1a1a] text-[13px] font-medium flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="8" cy="8" r="6" /><path d="M8 5v3M8 10.5v.5" /></svg>
                    {error}
                </div>
            )}

            <div className="flex gap-5 items-start flex-col lg:flex-row">

                {/* ── Panel izquierdo: lista de estudiantes ── */}
                <div className="flex-1 bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden min-w-0">

                    <div className="px-5 pt-5 pb-4 border-b border-[#e1e3e4]">
                        <h2 className="text-[15px] font-bold text-[#191c1d] mb-3">Estudiantes del Curso</h2>
                        {/* Buscador */}
                        <div className="relative">
                            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                                <circle cx="6.5" cy="6.5" r="4" /><path d="M11 11l3 3" />
                            </svg>
                            <input
                                type="text"
                                value={busqueda}
                                onChange={e => setBusqueda(e.target.value)}
                                placeholder="Buscar por nombre o correo..."
                                className="w-full h-10 pl-9 pr-4 rounded-xl border border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-colors"
                            />
                        </div>
                    </div>

                    <div className="overflow-y-auto max-h-[calc(100vh-280px)]">

                        {/* Disponibles */}
                        {disponiblesFiltrados.length > 0 && (
                            <div>
                                <p className="px-5 pt-4 pb-2 text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase">
                                    Disponibles ({disponiblesFiltrados.length})
                                </p>
                                {disponiblesFiltrados.map(est => {
                                    const checked  = seleccionados.has(est.id)
                                    const disabled = !checked && cupoLleno
                                    return (
                                        <label
                                            key={est.id}
                                            className={`flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#f8f9fa]'} ${checked ? 'bg-[#fff8f7]' : ''}`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={checked}
                                                disabled={disabled}
                                                onChange={() => toggleSeleccion(est.id)}
                                                className="w-4 h-4 rounded accent-[#d32f2f] flex-shrink-0"
                                            />
                                            <div
                                                className="w-9 h-9 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                                                style={{ backgroundColor: colorFor(est.id) }}
                                            >
                                                {avatar(est.nombre, est.apellido)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{est.nombre} {est.apellido}</p>
                                                <p className="text-[12px] text-[#9ba7ae] truncate">{est.correo}</p>
                                            </div>
                                            <span className="flex items-center gap-1 text-[11px] font-semibold text-[#2e7d32] flex-shrink-0">
                                                <span className="w-1.5 h-1.5 rounded-full bg-[#2e7d32]" />
                                                DISPONIBLE
                                            </span>
                                        </label>
                                    )
                                })}
                            </div>
                        )}

                        {disponiblesFiltrados.length === 0 && busqueda && (
                            <p className="px-5 py-6 text-[13px] text-[#9ba7ae] text-center">Sin resultados para "{busqueda}"</p>
                        )}

                        {/* Ya en el equipo */}
                        {(datos?.ya_en_equipo?.length ?? 0) > 0 && (
                            <div>
                                <p className="px-5 pt-4 pb-2 text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase">
                                    Ya en ({datos.ya_en_equipo.length})
                                </p>
                                {datos.ya_en_equipo.map(est => (
                                    <div key={est.id} className="flex items-center gap-3 px-5 py-3 opacity-60">
                                        <div className="w-4 h-4 flex-shrink-0" />
                                        <div
                                            className="w-9 h-9 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                                            style={{ backgroundColor: colorFor(est.id) }}
                                        >
                                            {avatar(est.nombre, est.apellido)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[13px] font-semibold text-[#191c1d] truncate">{est.nombre} {est.apellido}</p>
                                            <p className="text-[12px] text-[#9ba7ae] truncate">{est.correo}</p>
                                        </div>
                                        <span className="flex items-center gap-1 text-[11px] font-semibold text-[#1976d2] flex-shrink-0">
                                            <span className="w-1.5 h-1.5 rounded-full bg-[#1976d2]" />
                                            EN EQUIPO
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Asignados a otro equipo */}
                        {(datos?.en_otro_equipo?.length ?? 0) > 0 && (
                            <div>
                                <p className="px-5 pt-4 pb-2 text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase">
                                    Asignados a otro equipo ({datos.en_otro_equipo.length})
                                </p>
                                {datos.en_otro_equipo.map(est => (
                                    <div key={est.id} className="flex items-center gap-3 px-5 py-3 opacity-40">
                                        <div className="w-4 h-4 flex-shrink-0" />
                                        <div
                                            className="w-9 h-9 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                                            style={{ backgroundColor: colorFor(est.id) }}
                                        >
                                            {avatar(est.nombre, est.apellido)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[13px] font-semibold text-[#191c1d] truncate">{est.nombre} {est.apellido}</p>
                                            <p className="text-[12px] text-[#9ba7ae] truncate">{est.correo}</p>
                                        </div>
                                        <span className="flex items-center gap-1 text-[11px] font-semibold text-[#9ba7ae] flex-shrink-0">
                                            <span className="w-1.5 h-1.5 rounded-full bg-[#9ba7ae]" />
                                            OTRO EQUIPO
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="h-4" />
                    </div>
                </div>

                {/* ── Panel derecho: capacidad y acción ── */}
                <div className="w-full lg:w-64 flex-shrink-0 flex flex-col gap-3">
                    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5">

                        {/* Contador */}
                        <div className="text-center mb-4">
                            <p className="text-[28px] font-bold text-[#191c1d] leading-none">
                                {ocupados}
                                <span className="text-[18px] text-[#9ba7ae] font-normal">/{cupoMaximo}</span>
                            </p>
                            <p className="text-[12px] text-[#9ba7ae] mt-1">miembros</p>
                        </div>

                        {/* Barra de capacidad */}
                        <div className="mb-4">
                            <div className="flex items-center justify-between mb-1.5">
                                <span className="text-[12px] text-[#5b403d] font-medium">Capacidad</span>
                                <span className="text-[12px] font-bold text-[#191c1d]">{ocupados}/{cupoMaximo}</span>
                            </div>
                            <div className="h-2 rounded-full bg-[#f0f2f3] overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all ${cupoLleno ? 'bg-[#d32f2f]' : 'bg-[#388e3c]'}`}
                                    style={{ width: cupoMaximo > 0 ? `${Math.min((ocupados / cupoMaximo) * 100, 100)}%` : '0%' }}
                                />
                            </div>
                        </div>

                        {/* Botón asignar */}
                        <button
                            onClick={handleAsignar}
                            disabled={seleccionados.size === 0 || asignando}
                            className="w-full h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {asignando ? (
                                <>
                                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Asignando...
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-6 6s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z" /></svg>
                                    Asignar estudiantes
                                    {seleccionados.size > 0 && (
                                        <span className="bg-white text-[#d32f2f] text-[11px] font-bold w-5 h-5 rounded-full flex items-center justify-center">
                                            {seleccionados.size}
                                        </span>
                                    )}
                                </>
                            )}
                        </button>
                    </div>

                    {/* Nota informativa */}
                    <div className="bg-[#f8f9fa] rounded-xl border border-[#e1e3e4] px-4 py-3">
                        <p className="text-[12px] text-[#5b403d] text-center leading-relaxed">
                            Un estudiante no puede pertenecer a más de un equipo en el mismo curso.
                        </p>
                    </div>

                    {cupoLleno && seleccionados.size === 0 && (
                        <div className="bg-[#fff8f7] rounded-xl border border-[#ffdad6] px-4 py-3">
                            <p className="text-[12px] text-[#ba1a1a] text-center leading-relaxed font-medium">
                                El equipo ha alcanzado su capacidad máxima.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
