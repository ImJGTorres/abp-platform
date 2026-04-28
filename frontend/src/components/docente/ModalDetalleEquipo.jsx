import { useState } from 'react'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']
const TEAM_COLORS   = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f', '#0097a7']

const ROL = {
    lider:         { label: 'LÍDER',         icon: '👑', bg: 'bg-[#fef9c3]', text: 'text-[#92400e]' },
    desarrollador: { label: 'DESARROLLADOR', icon: '💻', bg: 'bg-[#e3f2fd]', text: 'text-[#1565c0]' },
    disenador:     { label: 'DISEÑADOR',     icon: '🎨', bg: 'bg-[#f3e5f5]', text: 'text-[#6a1b9a]' },
    tester:        { label: 'TESTER',        icon: '🔬', bg: 'bg-[#e8f5e9]', text: 'text-[#1b5e20]' },
    analista:      { label: 'ANALISTA',      icon: '📊', bg: 'bg-[#fff3e0]', text: 'text-[#e65100]' },
}

function rolBadge(rol) {
    const r = ROL[rol]
    if (!r) return <span className="text-[#9ba7ae]">—</span>
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold ${r.bg} ${r.text}`}>
            {r.icon} {r.label}
        </span>
    )
}

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

function IconX()     { return <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg> }
function IconPlus()  { return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M8 3v10M3 8h10"/></svg> }
function IconPerson(){ return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-6 6s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z"/></svg> }

function Avatar({ iniciales, colorIndex, size = 'sm' }) {
    const sz = size === 'sm' ? 'w-7 h-7 text-[10px]' : 'w-8 h-8 text-[11px]'
    return (
        <div style={{ backgroundColor: AVATAR_COLORS[colorIndex % AVATAR_COLORS.length] }}
            className={`${sz} rounded-full flex items-center justify-center text-white font-bold ring-2 ring-white flex-shrink-0`}>
            {iniciales}
        </div>
    )
}

/**
 * Modal de detalle de un equipo/proyecto.
 *
 * Props:
 *   titulo    — nombre a mostrar en el header (proyecto o equipo)
 *   subtitulo — descripción
 *   colorIndex — índice para el color del cuadrado del header
 *   equipo    — objeto con { id, nombre, cupo_maximo, cantidad_miembros, miembros, lider, estado, cantidad_entregables }
 *   onClose   — cierra el modal
 *   onAgregar — callback al pulsar "Asignar estudiante"
 */
export default function ModalDetalleEquipo({ titulo, subtitulo, colorIndex = 0, equipo, onClose, onAgregar }) {
    const [tab, setTab] = useState('miembros')
    const color   = TEAM_COLORS[colorIndex % TEAM_COLORS.length]
    const miembros = equipo?.miembros ?? []

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
            onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]"
                onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="p-6 border-b border-[#e1e3e4] flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-[18px] font-bold flex-shrink-0"
                        style={{ backgroundColor: color }}>
                        {(titulo ?? '?')[0].toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                        <h2 className="text-[18px] font-bold text-[#191c1d] leading-tight">{titulo}</h2>
                        {subtitulo && <p className="text-[13px] text-[#9ba7ae] mt-0.5">{subtitulo}</p>}
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-xl text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#191c1d] flex items-center justify-center transition-colors flex-shrink-0">
                        <IconX />
                    </button>
                </div>

                {/* Acciones */}
                <div className="px-6 pt-4 pb-3 flex items-center gap-2 flex-wrap border-b border-[#f0f2f3]">
                    <button onClick={onAgregar}
                        className="flex items-center gap-1.5 h-9 px-4 rounded-xl border border-[#e1e3e4] text-[#4c616c] text-[13px] font-semibold hover:bg-[#f0f2f3] transition-colors">
                        <IconPlus /> Asignar estudiante
                    </button>
                    <button className="flex items-center gap-1.5 h-9 px-4 rounded-xl border border-[#e1e3e4] text-[#4c616c] text-[13px] font-semibold hover:bg-[#f0f2f3] transition-colors">
                        <IconPerson /> Perfiles y roles
                    </button>
                    <button className="flex items-center gap-1.5 h-9 px-4 rounded-xl border border-[#e1e3e4] text-[#4c616c] text-[13px] font-semibold hover:bg-[#f0f2f3] transition-colors">
                        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M2 5h12M2 11h12M5 2l-3 3 3 3M11 14l3-3-3-3"/></svg>
                        Reorganizar
                    </button>
                </div>

                {/* Tabs */}
                <div className="px-6 flex gap-1 border-b border-[#e1e3e4]">
                    <button onClick={() => setTab('miembros')}
                        className={`py-3 px-1 text-[13px] font-semibold border-b-2 transition-colors ${tab === 'miembros' ? 'border-[#d32f2f] text-[#d32f2f]' : 'border-transparent text-[#9ba7ae] hover:text-[#4c616c]'}`}>
                        Miembros ({miembros.length})
                    </button>
                    <button onClick={() => setTab('info')}
                        className={`py-3 px-4 text-[13px] font-semibold border-b-2 transition-colors ${tab === 'info' ? 'border-[#d32f2f] text-[#d32f2f]' : 'border-transparent text-[#9ba7ae] hover:text-[#4c616c]'}`}>
                        Info del equipo
                    </button>
                </div>

                {/* Contenido */}
                <div className="flex-1 overflow-y-auto">

                    {tab === 'miembros' && (
                        miembros.length === 0 ? (
                            <div className="p-12 text-center text-[13px] text-[#9ba7ae]">
                                No hay miembros en este equipo aún.
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-[#e1e3e4]">
                                            {['ESTUDIANTE', 'CORREO', 'ROL EN EQUIPO', 'ESTADO', 'INCORPORACIÓN', 'ACCIONES'].map(h => (
                                                <th key={h} className="px-5 py-3 text-left text-[11px] font-semibold text-[#9ba7ae] tracking-wide whitespace-nowrap">{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {miembros.map((m, i) => (
                                            <tr key={m.id} className="border-b border-[#f0f2f3] last:border-0 hover:bg-[#fafbfc] transition-colors">
                                                <td className="px-5 py-3.5">
                                                    <div className="flex items-center gap-2.5">
                                                        <Avatar iniciales={m.iniciales} colorIndex={i} />
                                                        <span className="text-[13px] font-semibold text-[#191c1d] whitespace-nowrap">{m.nombre_completo}</span>
                                                    </div>
                                                </td>
                                                <td className="px-5 py-3.5 text-[13px] text-[#5b403d] whitespace-nowrap">{m.correo ?? '—'}</td>
                                                <td className="px-5 py-3.5">{rolBadge(m.rol_interno)}</td>
                                                <td className="px-5 py-3.5">
                                                    <span className={`inline-flex items-center gap-1 text-[12px] font-semibold ${m.estado === 'activo' ? 'text-[#2e7d32]' : 'text-[#9ba7ae]'}`}>
                                                        <span className={`w-1.5 h-1.5 rounded-full ${m.estado === 'activo' ? 'bg-[#2e7d32]' : 'bg-[#9ba7ae]'}`} />
                                                        {m.estado === 'activo' ? 'ACTIVO' : 'INACTIVO'}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-3.5 text-[13px] text-[#5b403d] whitespace-nowrap">
                                                    {formatFecha(m.fecha_asignacion)}
                                                </td>
                                                <td className="px-5 py-3.5">
                                                    <button className="flex items-center gap-1.5 h-7 px-3 rounded-lg border border-[#e1e3e4] text-[#4c616c] text-[12px] font-semibold hover:bg-[#f0f2f3] transition-colors">
                                                        <IconPerson /> Perfil
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )
                    )}

                    {tab === 'info' && (
                        <div className="p-6 flex flex-col gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-[#f8f9fa] rounded-xl p-4">
                                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Cupo máximo</p>
                                    <p className="text-[20px] font-bold text-[#191c1d]">{equipo?.cupo_maximo ?? '—'}</p>
                                    <p className="text-[12px] text-[#9ba7ae]">{equipo?.cantidad_miembros ?? 0} ocupado{equipo?.cantidad_miembros !== 1 ? 's' : ''}</p>
                                </div>
                                <div className="bg-[#f8f9fa] rounded-xl p-4">
                                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Estado</p>
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px] font-semibold ${equipo?.estado === 'activo' ? 'bg-[#e8f5e9] text-[#2e7d32]' : 'bg-[#f0f2f3] text-[#9ba7ae]'}`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${equipo?.estado === 'activo' ? 'bg-[#2e7d32]' : 'bg-[#9ba7ae]'}`} />
                                        {equipo?.estado === 'activo' ? 'Activo' : 'Inactivo'}
                                    </span>
                                </div>
                            </div>
                            {equipo?.lider && (
                                <div>
                                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-1">Líder</p>
                                    <p className="text-[14px] font-semibold text-[#191c1d]">{equipo.lider.nombre}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
