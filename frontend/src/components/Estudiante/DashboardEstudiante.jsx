import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { request } from '../../services/api'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconFolder() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M2 5a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" /></svg>
}
function IconArrow() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 10h12M10 4l6 6-6 6" /></svg>
}
function IconUsers() {
    return <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><circle cx="7" cy="7" r="3" /><path d="M1 17a6 6 0 0112 0" /><path d="M13 5a3 3 0 110 6" opacity="0.6" /><path d="M16 17a5 5 0 00-3-4.6" opacity="0.6" /></svg>
}
function IconEmpty() {
    return <svg viewBox="0 0 48 48" fill="none" className="w-12 h-12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="8" y="12" width="32" height="28" rx="3" /><path d="M16 12V9a2 2 0 012-2h12a2 2 0 012 2v3" /><path d="M24 22v8M20 26h8" /></svg>
}

// ── Helper ─────────────────────────────────────────────────────────────────

async function getMisEquipos() {
    const res = await request('/api/mis-equipos/')
    const data = await res.json()
    if (!res.ok) throw data
    return data
}

// ── Componente principal ───────────────────────────────────────────────────

export default function DashboardEstudiante({ basePath = '/estudiante' }) {
    const navigate = useNavigate()
    const [equipos, setEquipos] = useState([])
    const [loading, setLoading] = useState(true)
    const [error,   setError]   = useState('')

    useEffect(() => { cargar() }, [])

    async function cargar() {
        setLoading(true)
        setError('')
        try {
            const data = await getMisEquipos()
            setEquipos(data)
        } catch (err) {
            setError(err.detail || 'Error cargando tu información.')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="flex flex-col items-center gap-3">
                    <svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span className="text-[14px] text-[#9ba7ae]">Cargando tus proyectos...</span>
                </div>
            </div>
        )
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            <div className="mb-6">
                <h1 className="text-[22px] font-extrabold text-[#191c1d] mb-1">Mis proyectos</h1>
                <p className="text-[13px] text-[#9ba7ae]">Selecciona un proyecto para ver sus actividades, evaluaciones e historial.</p>
            </div>

            {error && (
                <div className="mb-4 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium">
                    {error}
                </div>
            )}

            {equipos.length === 0 ? (
                <div className="text-center py-20 bg-white border border-dashed border-[#e1e3e4] rounded-2xl">
                    <div className="w-14 h-14 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-3 text-[#9ba7ae]">
                        <IconEmpty />
                    </div>
                    <p className="text-[15px] font-bold text-[#4c616c] mb-1">Aún no tienes equipo asignado</p>
                    <p className="text-[13px] text-[#9ba7ae]">Cuando el docente te asigne a un equipo, tus proyectos aparecerán aquí.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                    {equipos.map(e => (
                        <div
                            key={e.equipo.id}
                            className="bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden shadow-sm hover:shadow-md hover:border-[#d0d4d6] transition-all group"
                        >
                            {/* Cabecera */}
                            <div className="p-5 pb-4">
                                <div className="flex items-start gap-3 mb-4">
                                    <div className="w-10 h-10 rounded-xl bg-[#ffdad6] flex items-center justify-center flex-shrink-0 text-[#d32f2f]">
                                        <IconFolder />
                                    </div>
                                    <div className="min-w-0">
                                        <h2 className="text-[15px] font-extrabold text-[#191c1d] leading-tight mb-0.5 truncate">
                                            {e.proyecto.nombre}
                                        </h2>
                                        <p className="text-[12px] text-[#9ba7ae] truncate">{e.curso.nombre}</p>
                                    </div>
                                </div>

                                {/* Equipo */}
                                <div className="flex items-center gap-1.5 text-[12px] text-[#4c616c] mb-2">
                                    <IconUsers />
                                    <span className="font-semibold truncate">{e.equipo.nombre}</span>
                                </div>

                                {/* Stats */}
                                <div className="flex items-center gap-3 text-[11px] text-[#9ba7ae]">
                                    <span>
                                        {e.fases.reduce((s, f) => s + f.actividades.length, 0)} actividad
                                        {e.fases.reduce((s, f) => s + f.actividades.length, 0) !== 1 ? 'es' : ''}
                                    </span>
                                    <span>·</span>
                                    <span>{e.fases.length} fase{e.fases.length !== 1 ? 's' : ''}</span>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="border-t border-[#f0f2f3] p-3">
                                <button
                                    onClick={() => navigate(`/estudiante/proyectos/${e.proyecto.id}/actividades`)}
                                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#d32f2f] text-white text-[13px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors group-hover:shadow-sm"
                                >
                                    Entrar al proyecto
                                    <IconArrow />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}