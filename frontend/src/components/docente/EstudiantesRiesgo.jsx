import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { reportesApi, cursosApi } from '../../services/docenteApi'

// Umbrales por defecto (coinciden con los del backend)
const UMBRAL_NOTA = 3.0
const UMBRAL_PCT_INCUMPLIDAS = 50

function IconAlert() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 2L1.5 17h17L10 2z" />
            <path d="M10 8v4" />
            <circle cx="10" cy="14" r="0.6" fill="currentColor" />
        </svg>
    )
}

function IconUser() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="5" r="3" />
            <path d="M2 14a6 6 0 0112 0" />
        </svg>
    )
}

function IconFilter() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <path d="M2 4h12M4 8h8M6 12h4" />
        </svg>
    )
}

function IconChevronRight() {
    return (
        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 3l5 5-5 5" />
        </svg>
    )
}

function CeldaCritica({ value, critica, children }) {
    if (critica) {
        return (
            <td className="px-4 py-3">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-red-50 border border-red-200 text-[#d32f2f] font-bold text-[13px]">
                    {children ?? value}
                </span>
            </td>
        )
    }
    return (
        <td className="px-4 py-3 text-[13px] text-[#4c616c] font-medium">
            {children ?? value}
        </td>
    )
}

export default function EstudiantesRiesgo() {
    const { cursoId } = useParams()
    const [estudiantes, setEstudiantes] = useState([])
    const [proyectos, setProyectos] = useState([])
    const [proyectoFiltro, setProyectoFiltro] = useState('')
    const [cargando, setCargando] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        cursosApi.obtenerProyectos(cursoId)
            .then(setProyectos)
            .catch(() => { })
    }, [cursoId])

    useEffect(() => {
        cargar()
    }, [cursoId, proyectoFiltro])

    async function cargar() {
        setCargando(true)
        setError(null)
        try {
            const data = await reportesApi.bajoRendimiento({
                cursoId: cursoId ? Number(cursoId) : undefined,
                proyectoId: proyectoFiltro ? Number(proyectoFiltro) : undefined,
            })
            setEstudiantes(data.estudiantes ?? [])
        } catch {
            setError('No se pudo cargar el reporte de estudiantes en riesgo.')
        } finally {
            setCargando(false)
        }
    }

    const perfilUrl = (id) => {
        const params = new URLSearchParams()
        if (cursoId) params.set('curso_id', cursoId)
        if (proyectoFiltro) params.set('proyecto_id', proyectoFiltro)
        return `/docente/estudiantes/${id}/rendimiento?${params}`
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            {/* Encabezado */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-[#d32f2f]">
                        <IconAlert />
                    </div>
                    <div>
                        <h1 className="text-[18px] font-bold text-[#191c1d]">Estudiantes en Riesgo</h1>
                        <p className="text-[13px] text-[#9ba7ae]">
                            {cargando ? 'Cargando...' : `${estudiantes.length} estudiante${estudiantes.length !== 1 ? 's' : ''} detectado${estudiantes.length !== 1 ? 's' : ''}`}
                        </p>
                    </div>
                </div>
                <div className="sm:ml-auto flex items-center gap-2">
                    <IconFilter />
                    <select
                        value={proyectoFiltro}
                        onChange={e => setProyectoFiltro(e.target.value)}
                        className="text-[13px] border border-[#e1e3e4] rounded-xl px-3 py-2 bg-white text-[#191c1d] focus:outline-none focus:border-[#d32f2f] transition-colors min-w-[180px]"
                    >
                        <option value="">Todos los proyectos</option>
                        {proyectos.map(p => (
                            <option key={p.id} value={p.id}>{p.nombre}</option>
                        ))}
                    </select>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] text-[13px] rounded-xl px-4 py-3 mb-4">
                    {error}
                </div>
            )}

            {/* Tabla */}
            {cargando ? (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                </div>
            ) : estudiantes.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] flex flex-col items-center justify-center py-16 gap-3">
                    <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center">
                        <svg viewBox="0 0 20 20" fill="none" className="w-6 h-6 text-green-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                            <path d="M4 10l4 4 8-8" />
                        </svg>
                    </div>
                    <p className="text-[15px] font-semibold text-[#191c1d]">Sin estudiantes en riesgo</p>
                    <p className="text-[13px] text-[#9ba7ae]">Todos los estudiantes están dentro de los parámetros aceptables.</p>
                </div>
            ) : (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#e1e3e4] bg-[#f8f9fa]">
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estudiante</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Código</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Nota Prom.</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">% Incumplidas</th>
                                    <th className="px-4 py-3" />
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f0f2f3]">
                                {estudiantes.map(est => (
                                    <tr key={est.id} className="hover:bg-[#fafafa] transition-colors">
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2.5">
                                                <div className="w-7 h-7 rounded-full bg-red-50 flex items-center justify-center text-[#d32f2f] flex-shrink-0">
                                                    <IconUser />
                                                </div>
                                                <div>
                                                    <p className="text-[13px] font-semibold text-[#191c1d]">{est.nombre} {est.apellido}</p>
                                                    <p className="text-[11px] text-[#9ba7ae]">{est.correo}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-[13px] text-[#4c616c] font-mono">
                                            {est.codigo ?? '—'}
                                        </td>
                                        <CeldaCritica critica={est.nota_promedio < UMBRAL_NOTA}>
                                            {est.nota_promedio?.toFixed(2)} / 5.0
                                        </CeldaCritica>
                                        <CeldaCritica critica={est.porcentaje_actividades_incumplidas >= UMBRAL_PCT_INCUMPLIDAS}>
                                            {est.porcentaje_actividades_incumplidas?.toFixed(1)}%
                                            <span className="text-[11px] font-normal ml-1 opacity-70">
                                                ({est.actividades_incumplidas}/{est.total_actividades})
                                            </span>
                                        </CeldaCritica>
                                        <td className="px-4 py-3">
                                            <Link
                                                to={perfilUrl(est.id)}
                                                className="flex items-center gap-1 text-[12px] font-semibold text-[#d32f2f] hover:text-[#af101a] transition-colors whitespace-nowrap"
                                            >
                                                Ver perfil
                                                <IconChevronRight />
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
