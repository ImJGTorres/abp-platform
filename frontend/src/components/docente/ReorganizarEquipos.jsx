import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { equiposApi, estudiantesApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']
const TEAM_COLORS   = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f', '#0097a7']

const ROL = {
    lider:         { label: 'Líder',         bg: '#fef9c3', color: '#92400e' },
    desarrollador: { label: 'Desarrollador', bg: '#e3f2fd', color: '#1565c0' },
    analista:      { label: 'Analista',      bg: '#fff3e0', color: '#e65100' },
    disenador:     { label: 'Diseñador',     bg: '#f3e5f5', color: '#6a1b9a' },
    tester:        { label: 'QA',            bg: '#e8f5e9', color: '#1b5e20' },
    documentador:  { label: 'Documentador',  bg: '#e0f7fa', color: '#006064' },
}

function Avatar({ ini, idx, size = 'md' }) {
    const sz = size === 'sm' ? 'w-7 h-7 text-[10px]' : 'w-9 h-9 text-[12px]'
    return (
        <div style={{ backgroundColor: AVATAR_COLORS[idx % AVATAR_COLORS.length] }}
            className={`${sz} rounded-full flex items-center justify-center text-white font-bold flex-shrink-0`}>
            {ini}
        </div>
    )
}

function RolChip({ rol }) {
    const r = ROL[rol]
    if (!r) return null
    return (
        <span style={{ backgroundColor: r.bg, color: r.color }}
            className="text-[11px] font-bold px-2 py-0.5 rounded-md whitespace-nowrap">
            {r.label}
        </span>
    )
}

function MemberCard({ miembro, idx, onDragStart, onDragEnd }) {
    return (
        <div
            draggable
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            className="flex items-center gap-3 px-3 py-2.5 bg-white border border-[#e1e3e4] rounded-xl cursor-grab active:cursor-grabbing hover:border-[#d32f2f] hover:shadow-sm transition-all select-none"
        >
            <Avatar ini={miembro.iniciales} idx={idx} />
            <div className="flex-1 min-w-0">
                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{miembro.nombre_completo}</p>
                <div className="mt-0.5">
                    {miembro.rol_interno
                        ? <RolChip rol={miembro.rol_interno} />
                        : <span className="text-[11px] text-[#9ba7ae]">Sin rol</span>
                    }
                </div>
            </div>
        </div>
    )
}

function TeamColumn({ equipo, colorIdx, isOver, onDragOver, onDragLeave, onDrop, onMemberDragStart, onDragEnd }) {
    const miembros = equipo.miembros ?? []
    const color = TEAM_COLORS[colorIdx % TEAM_COLORS.length]

    return (
        <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={`rounded-2xl border-2 border-dashed p-4 flex flex-col gap-3 min-h-[180px] transition-all ${
                isOver
                    ? 'border-[#d32f2f] bg-[#fff8f7] shadow-md'
                    : 'border-[#e1e3e4] bg-[#f8f9fa]'
            }`}
        >
            <div>
                <div className="flex items-center gap-2 mb-0.5">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <h3 className="text-[14px] font-bold text-[#191c1d] truncate">{equipo.nombre}</h3>
                </div>
                <p className="text-[11px] text-[#9ba7ae] pl-[18px]">
                    {miembros.length} miembro{miembros.length !== 1 ? 's' : ''} · {equipo.cantidad_entregables} entregable{equipo.cantidad_entregables !== 1 ? 's' : ''}
                </p>
                {equipo.cantidad_entregables > 0 && (
                    <p className="text-[11px] text-[#b45309] font-medium pl-[18px] mt-0.5">
                        ⚠ No eliminar: tiene entregables
                    </p>
                )}
            </div>

            <div className="flex flex-col gap-2 flex-1">
                {miembros.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center border border-dashed border-[#d1d3d4] rounded-xl py-6 text-[12px] text-[#9ba7ae]">
                        Suelta un miembro aquí
                    </div>
                ) : (
                    miembros.map((m, i) => (
                        <MemberCard
                            key={m.id}
                            miembro={m}
                            idx={i}
                            onDragStart={e => onMemberDragStart(e, m)}
                            onDragEnd={onDragEnd}
                        />
                    ))
                )}
            </div>
        </div>
    )
}

export default function ReorganizarEquipos() {
    const { cursoId, proyectoId } = useParams()
    const navigate = useNavigate()

    const [equipos, setEquipos]       = useState([])
    const [sinAsignar, setSinAsignar] = useState([])
    const [loading, setLoading]       = useState(true)
    const [error, setError]           = useState(null)
    const [moviendo, setMoviendo]     = useState(false)
    const [aviso, setAviso]           = useState(null)
    const [dropTarget, setDropTarget] = useState(null)

    const dragRef = useRef(null)

    useEffect(() => { cargarDatos() }, [proyectoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        try {
            const [eqData, saData] = await Promise.all([
                equiposApi.obtenerPorProyecto(proyectoId),
                estudiantesApi.sinEquipoEnProyecto(cursoId, proyectoId),
            ])
            setEquipos(eqData.equipos ?? [])
            setSinAsignar((saData ?? []).map(e => ({
                ...e,
                iniciales: (e.nombre?.[0] ?? '').toUpperCase() + (e.apellido?.[0] ?? '').toUpperCase(),
                nombre_completo: `${e.nombre} ${e.apellido}`.trim(),
                usuario_id: e.id,
            })))
        } catch {
            setError('No se pudo cargar la información de equipos.')
        } finally {
            setLoading(false)
        }
    }

    function handleDragStart(e, miembro, origenEquipoId) {
        dragRef.current = { miembro, origenEquipoId }
        e.dataTransfer.effectAllowed = 'move'
    }

    function handleDragOver(e, targetId) {
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
        setDropTarget(targetId)
    }

    function handleDragLeave(e) {
        if (!e.currentTarget.contains(e.relatedTarget)) {
            setDropTarget(null)
        }
    }

    function handleDragEnd() {
        dragRef.current = null
        setDropTarget(null)
    }

     async function handleDrop(e, destinoEquipoId) {
        e.preventDefault()
        setDropTarget(null)
        const drag = dragRef.current
        dragRef.current = null
        if (!drag) return

        const { miembro, origenEquipoId } = drag
        if (origenEquipoId === destinoEquipoId) return

        // No mover al único líder del equipo
        if (origenEquipoId !== null && miembro.rol_interno === 'lider') {
            const equipo = equipos.find(eq => eq.id === origenEquipoId)
            const lideres = (equipo?.miembros ?? []).filter(m => m.rol_interno === 'lider')
            if (lideres.length <= 1) {
                setAviso('No puedes mover al único líder de un equipo.')
                setTimeout(() => setAviso(null), 4000)
                return
            }
        }

        setMoviendo(true)
        setAviso(null)
        setError(null)
        try {
            if (origenEquipoId === null) {
                // Sin equipo → Equipo: asignar
                await equiposApi.asignarEstudiantes(destinoEquipoId, [miembro.usuario_id])
            } else if (destinoEquipoId === null) {
                // Equipo → Sin equipo: retirar
                await equiposApi.retirarMiembro(origenEquipoId, miembro.usuario_id)
            } else {
                // Equipo → Equipo: mover
                await equiposApi.moverMiembro(origenEquipoId, miembro.usuario_id, destinoEquipoId)
            }
            await cargarDatos()
        } catch (err) {
            setError(err?.data?.detail ?? 'Error al mover el estudiante. Intenta de nuevo.')
        } finally {
            setMoviendo(false)
        }
    }

    if (loading) return (
        <div className="flex-1 flex items-center justify-center">
            <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
        </div>
    )

    return (
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="mb-4 flex items-center gap-2 text-[13px]">
                <button
                    onClick={() => navigate(-1)}
                    className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                    Equipos
                </button>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5" /></svg>
                <span className="font-semibold text-[#191c1d]">Reorganizar Equipos</span>
                <span className="ml-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#e3f2fd] text-[#1565c0]">HU-013</span>
            </div>

            {/* Banner informativo */}
            <div className="mb-5 flex items-start gap-3 px-4 py-3 bg-[#e3f2fd] border border-[#bbdefb] rounded-xl text-[13px] text-[#1565c0]">
                <svg className="w-4 h-4 flex-shrink-0 mt-0.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                    <circle cx="8" cy="8" r="6" /><path d="M8 7v4M8 5.5v.5" />
                </svg>
                <p className="leading-relaxed">
                    <strong>Arrastra</strong> un miembro de un equipo a otro para reasignarlo. Los cambios usan{' '}
                    <code className="bg-[#bbdefb] px-1 rounded text-[11px]">DELETE /api/miembros/:id/</code>{' '}+{' '}
                    <code className="bg-[#bbdefb] px-1 rounded text-[11px]">POST /api/equipos/:id/miembros/</code>.{' '}
                    No puedes mover al único líder de un equipo.
                </p>
            </div>

            {/* Avisos */}
            {aviso && (
                <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#ffdad6] border border-[#ffb4ab] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <circle cx="8" cy="8" r="6" /><path d="M8 5v3M8 10.5v.5" />
                    </svg>
                    {aviso}
                </div>
            )}

            {error && (
                <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#ffdad6] border border-[#ffb4ab] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                    {error}
                </div>
            )}

            {moviendo && (
                <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#f0f2f3] rounded-xl text-[13px] text-[#4c616c]">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Moviendo estudiante...
                </div>
            )}

            {/* Grid de equipos */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 mb-6">
                {equipos.map((eq, i) => (
                    <TeamColumn
                        key={eq.id}
                        equipo={eq}
                        colorIdx={i}
                        isOver={dropTarget === eq.id}
                        onDragOver={e => handleDragOver(e, eq.id)}
                        onDragLeave={handleDragLeave}
                        onDrop={e => handleDrop(e, eq.id)}
                        onMemberDragStart={(e, m) => handleDragStart(e, m, eq.id)}
                        onDragEnd={handleDragEnd}
                    />
                ))}
            </div>

            {/* Sin equipo asignado */}
            <div
                onDragOver={e => handleDragOver(e, 'sin_asignar')}
                onDragLeave={handleDragLeave}
                onDrop={e => handleDrop(e, null)}
                className={`rounded-2xl border-2 border-dashed p-4 transition-all ${
                    dropTarget === 'sin_asignar'
                        ? 'border-[#d32f2f] bg-[#fff8f7] shadow-md'
                        : 'border-[#e1e3e4] bg-[#f8f9fa]'
                }`}
            >
                <p className="text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase mb-3">
                    SIN EQUIPO ASIGNADO ({sinAsignar.length})
                </p>
                <div className="flex flex-wrap gap-2 min-h-[40px]">
                    {sinAsignar.length === 0 ? (
                        <p className="text-[13px] text-[#9ba7ae] py-1 self-center">
                            Todos los estudiantes están asignados a un equipo.
                        </p>
                    ) : (
                        sinAsignar.map((est, i) => (
                            <div
                                key={est.id}
                                draggable
                                onDragStart={e => handleDragStart(e, est, null)}
                                onDragEnd={handleDragEnd}
                                className="flex items-center gap-2 px-3 py-2 bg-white border border-[#e1e3e4] rounded-xl cursor-grab active:cursor-grabbing hover:border-[#d32f2f] hover:shadow-sm transition-all select-none"
                            >
                                <Avatar ini={est.iniciales} idx={i} size="sm" />
                                <span className="text-[13px] font-semibold text-[#191c1d] whitespace-nowrap">
                                    {est.nombre} {est.apellido}
                                </span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}
