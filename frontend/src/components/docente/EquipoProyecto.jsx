import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { equiposApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']

const ROLES = [
    { key: 'lider',         label: 'Líder',         icon: '👑', bg: 'bg-[#fef9c3]',  text: 'text-[#92400e]', border: 'border-[#f59e0b]' },
    { key: 'desarrollador', label: 'Desarrollador', icon: '💻', bg: 'bg-[#e3f2fd]',  text: 'text-[#1565c0]', border: 'border-[#1976d2]' },
    { key: 'analista',      label: 'Analista',      icon: '📊', bg: 'bg-[#fff3e0]',  text: 'text-[#e65100]', border: 'border-[#f57c00]' },
    { key: 'disenador',     label: 'Diseñador',     icon: '🎨', bg: 'bg-[#f3e5f5]',  text: 'text-[#6a1b9a]', border: 'border-[#7b1fa2]' },
    { key: 'tester',        label: 'Tester',        icon: '🔬', bg: 'bg-[#e8f5e9]',  text: 'text-[#1b5e20]', border: 'border-[#388e3c]' },
]

function Avatar({ iniciales, colorIdx, size = 'md' }) {
    const sz = {
        sm: 'w-8 h-8 text-[10px]',
        md: 'w-10 h-10 text-[13px]',
        lg: 'w-14 h-14 text-[18px]',
    }[size]
    return (
        <div style={{ backgroundColor: AVATAR_COLORS[colorIdx % AVATAR_COLORS.length] }}
            className={`${sz} rounded-full flex items-center justify-center text-white font-bold flex-shrink-0`}>
            {iniciales}
        </div>
    )
}

function RolBadge({ rol }) {
    const r = ROLES.find(x => x.key === rol)
    if (!r) return null
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold ${r.bg} ${r.text}`}>
            {r.icon} {r.label.toUpperCase()}
        </span>
    )
}

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function EquipoProyecto() {
    const { cursoId, proyectoId } = useParams()

    const [info, setInfo] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [miembroSel, setMiembroSel] = useState(null)
    const [guardandoRol, setGuardandoRol] = useState(false)

    useEffect(() => { cargarDatos() }, [proyectoId])

    async function cargarDatos() {
        setLoading(true)
        setError(null)
        try {
            const data = await equiposApi.obtenerPorProyecto(proyectoId)
            const equipo = data.equipos?.[0] ?? null
            setInfo({ proyecto: data.proyecto, curso: data.curso, equipo })
            if (equipo?.miembros?.length > 0) setMiembroSel(equipo.miembros[0])
        } catch {
            setError('No se pudo cargar la información del equipo.')
        } finally {
            setLoading(false)
        }
    }

    async function handleCambiarRol(nuevoRol) {
        if (!miembroSel || guardandoRol) return
        const rol = miembroSel.rol_interno === nuevoRol ? '' : nuevoRol
        setGuardandoRol(true)
        try {
            const updated = await equiposApi.actualizarRolMiembro(miembroSel.id, rol)
            setInfo(prev => ({
                ...prev,
                equipo: {
                    ...prev.equipo,
                    miembros: prev.equipo.miembros.map(m =>
                        m.id === miembroSel.id
                            ? { ...m, rol_interno: updated.rol_interno }
                            : (updated.rol_interno === 'lider' && m.rol_interno === 'lider')
                                ? { ...m, rol_interno: '' }
                                : m
                    ),
                },
            }))
            setMiembroSel(prev => ({ ...prev, rol_interno: updated.rol_interno }))
        } catch (err) {
            alert(err?.data?.detail ?? 'Error al actualizar el rol.')
        } finally {
            setGuardandoRol(false)
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

    if (error || !info) return (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <p className="text-[14px] text-[#ba1a1a]">{error ?? 'No encontrado.'}</p>
            <Link to={`/docente/cursos/${cursoId}`} className="text-[13px] text-[#d32f2f] hover:underline">Volver al curso</Link>
        </div>
    )

    const { proyecto, curso, equipo } = info
    const miembros = equipo?.miembros ?? []
    const selIdx = miembros.findIndex(m => m.id === miembroSel?.id)

    return (
        <div className="flex-1 flex flex-col overflow-hidden" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Breadcrumb */}
            <div className="px-6 pt-5 pb-3 flex items-center gap-2 text-[13px] flex-shrink-0">
                <Link to="/docente/cursos" className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">Mis cursos</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5"/></svg>
                <Link to={`/docente/cursos/${cursoId}`} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors">{curso?.nombre ?? 'Curso'}</Link>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5"/></svg>
                <span className="text-[#191c1d] font-semibold truncate">{proyecto?.nombre}</span>
            </div>

            {/* Cuerpo: panel izquierdo + panel derecho */}
            <div className="flex-1 flex gap-4 overflow-hidden px-6 pb-6">

                {/* Panel izquierdo: lista de miembros */}
                <div className="w-64 flex-shrink-0 bg-white rounded-2xl border border-[#e1e3e4] flex flex-col overflow-hidden">
                    <div className="px-4 py-3 border-b border-[#e1e3e4]">
                        <p className="text-[11px] font-bold text-[#9ba7ae] tracking-widest uppercase leading-tight">
                            {equipo?.nombre ?? proyecto?.nombre}
                        </p>
                        <p className="text-[11px] text-[#9ba7ae] mt-0.5">
                            {miembros.length} miembro{miembros.length !== 1 ? 's' : ''}
                        </p>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {miembros.length === 0 ? (
                            <p className="p-5 text-[13px] text-[#9ba7ae] text-center">Sin miembros aún.</p>
                        ) : (
                            miembros.map((m, i) => {
                                const sel = miembroSel?.id === m.id
                                return (
                                    <button key={m.id}
                                        onClick={() => setMiembroSel(m)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors border-l-2 ${sel ? 'bg-[#fff8f7] border-[#d32f2f]' : 'border-transparent hover:bg-[#f8f9fa]'}`}>
                                        <Avatar iniciales={m.iniciales} colorIdx={i} size="sm" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[13px] font-semibold text-[#191c1d] truncate">{m.nombre_completo}</p>
                                            {m.rol_interno
                                                ? <RolBadge rol={m.rol_interno} />
                                                : <span className="text-[11px] text-[#9ba7ae]">Sin rol</span>
                                            }
                                        </div>
                                    </button>
                                )
                            })
                        )}
                    </div>
                </div>

                {/* Panel derecho: perfil del miembro */}
                {miembroSel ? (
                    <div className="flex-1 bg-white rounded-2xl border border-[#e1e3e4] flex flex-col overflow-y-auto min-w-0">

                        {/* Header del perfil */}
                        <div className="p-6 border-b border-[#e1e3e4] flex items-center gap-4">
                            <Avatar iniciales={miembroSel.iniciales} colorIdx={selIdx >= 0 ? selIdx : 0} size="lg" />
                            <div className="flex-1 min-w-0">
                                <h2 className="text-[18px] font-bold text-[#191c1d] leading-tight">{miembroSel.nombre_completo}</h2>
                                <p className="text-[13px] text-[#9ba7ae] mt-0.5">{miembroSel.correo}</p>
                                <div className="flex items-center gap-2 mt-2 flex-wrap">
                                    <span className="flex items-center gap-1 text-[12px] font-semibold text-[#2e7d32]">
                                        <span className="w-1.5 h-1.5 rounded-full bg-[#2e7d32]" />
                                        ACTIVO
                                    </span>
                                    {miembroSel.rol_interno && <RolBadge rol={miembroSel.rol_interno} />}
                                </div>
                            </div>
                        </div>

                        {/* Info grid */}
                        <div className="px-6 py-5 border-b border-[#e1e3e4] grid grid-cols-3 gap-4">
                            <div>
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Incorporación</p>
                                <p className="text-[14px] font-semibold text-[#191c1d]">{formatFecha(miembroSel.fecha_asignacion)}</p>
                            </div>
                            <div>
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Equipo</p>
                                <p className="text-[14px] font-semibold text-[#191c1d]">{equipo?.nombre ?? '—'}</p>
                            </div>
                            <div>
                                <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Entregables asignados</p>
                                <p className="text-[14px] font-semibold text-[#191c1d]">—</p>
                            </div>
                        </div>

                        {/* Selector de rol */}
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-[14px] font-bold text-[#191c1d]">Rol en el equipo</h3>
                                <span className="text-[11px] text-[#9ba7ae] font-mono bg-[#f8f9fa] px-2 py-0.5 rounded">
                                    PATCH /api/miembros/{miembroSel.id}/
                                </span>
                            </div>
                            <div className="flex flex-wrap gap-2 mb-4">
                                {ROLES.map(r => {
                                    const activo = miembroSel.rol_interno === r.key
                                    return (
                                        <button key={r.key}
                                            onClick={() => handleCambiarRol(r.key)}
                                            disabled={guardandoRol}
                                            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border-2 text-[13px] font-semibold transition-all disabled:opacity-50 ${
                                                activo
                                                    ? `${r.bg} ${r.text} ${r.border}`
                                                    : 'border-[#e1e3e4] text-[#4c616c] hover:bg-[#f8f9fa]'
                                            }`}>
                                            {r.icon} {r.label}
                                        </button>
                                    )
                                })}
                            </div>
                            {miembroSel.rol_interno === 'lider' && (
                                <div className="bg-[#e3f2fd] rounded-xl px-4 py-3 text-[12px] text-[#1565c0] leading-relaxed">
                                    Un equipo puede tener <strong>solo un líder</strong>. El rol es visible para todos los integrantes del equipo.{' '}
                                    <code className="bg-[#bbdefb] px-1 rounded text-[11px]">rol_en_equipo ∈ {'{lider, miembro}'}</code> en BD.
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 bg-white rounded-2xl border border-[#e1e3e4] flex items-center justify-center">
                        <p className="text-[13px] text-[#9ba7ae]">Selecciona un miembro para ver su perfil.</p>
                    </div>
                )}
            </div>
        </div>
    )
}
