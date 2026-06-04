import { useState, useEffect, useCallback } from 'react'
import { reportesApi } from '../../services/docenteApi'
import { periodosApi } from '../../services/api'

const UMBRAL_NOTA = 3.0
const UMBRAL_PCT = 50

function riesgoScore(est) {
    const notaRisk = Math.max(0, (UMBRAL_NOTA - (est.nota_promedio ?? UMBRAL_NOTA)) / UMBRAL_NOTA) * 100
    const pctRisk = est.porcentaje_actividades_incumplidas ?? 0
    return (notaRisk + pctRisk) / 2
}

function NivelRiesgo({ score }) {
    if (score >= 70) return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-50 border border-red-200 text-[#d32f2f] text-[11px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-[#d32f2f]" />Alto
        </span>
    )
    if (score >= 40) return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-50 border border-orange-200 text-orange-700 text-[11px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />Medio
        </span>
    )
    return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-50 border border-yellow-200 text-yellow-700 text-[11px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />Bajo
        </span>
    )
}

function BarraRiesgo({ valor, critica }) {
    const color = critica ? '#d32f2f' : '#ffa726'
    return (
        <div className="flex items-center gap-2">
            <span className={`text-[13px] font-semibold w-12 flex-shrink-0 ${critica ? 'text-[#d32f2f]' : 'text-[#4c616c]'}`}>
                {valor != null ? Number(valor).toFixed(1) : '—'}
            </span>
            <div className="w-24 h-1.5 bg-[#f0f2f3] rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full"
                    style={{
                        width: `${Math.min(Math.max(valor ?? 0, 0), 100)}%`,
                        backgroundColor: color,
                    }}
                />
            </div>
        </div>
    )
}

export default function EstudiantesRiesgoDirector() {
    const [periodos, setPeriodos] = useState([])
    const [periodoSel, setPeriodoSel] = useState('')
    const [estudiantes, setEstudiantes] = useState([])
    const [cargando, setCargando] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        periodosApi.listar().then(setPeriodos).catch(() => {})
    }, [])

    const cargar = useCallback(async (periodoId) => {
        setCargando(true)
        setError(null)
        try {
            const data = await reportesApi.bajoRendimiento({
                periodoId: periodoId ? Number(periodoId) : undefined,
            })
            const ordenados = (data.estudiantes ?? []).slice().sort(
                (a, b) => riesgoScore(b) - riesgoScore(a)
            )
            setEstudiantes(ordenados)
        } catch {
            setError('No se pudo cargar el reporte de estudiantes en riesgo.')
        } finally {
            setCargando(false)
        }
    }, [])

    useEffect(() => {
        cargar(periodoSel)
    }, [periodoSel, cargar])

    return (
        <div className="p-4 sm:p-6 flex flex-col gap-5">
            {/* Encabezado */}
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">Director</p>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d]">Estudiantes en riesgo</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        {cargando ? 'Cargando...' : `${estudiantes.length} estudiante${estudiantes.length !== 1 ? 's' : ''} detectado${estudiantes.length !== 1 ? 's' : ''} · ordenados de mayor a menor riesgo`}
                    </p>
                </div>
            </div>

            {/* Filtro de periodo */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-4">
                <div className="flex items-center gap-3 flex-wrap">
                    <p className="text-[13px] font-semibold text-[#191c1d] flex-shrink-0">Periodo académico:</p>
                    <select
                        value={periodoSel}
                        onChange={e => setPeriodoSel(e.target.value)}
                        className="border border-[#e1e3e4] rounded-xl px-3 py-1.5 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/30"
                    >
                        <option value="">Todos los periodos</option>
                        {periodos.map(p => (
                            <option key={p.id} value={p.id}>{p.nombre ?? `Periodo ${p.id}`}</option>
                        ))}
                    </select>
                    {cargando && (
                        <div className="w-4 h-4 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                    )}
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error}
                </div>
            )}

            {/* Tabla */}
            {!cargando && estudiantes.length === 0 && !error && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] flex flex-col items-center justify-center py-16 gap-3">
                    <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center">
                        <svg viewBox="0 0 20 20" fill="none" className="w-6 h-6 text-green-600" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                            <path d="M4 10l4 4 8-8" />
                        </svg>
                    </div>
                    <p className="text-[15px] font-semibold text-[#191c1d]">Sin estudiantes en riesgo</p>
                    <p className="text-[13px] text-[#9ba7ae]">Todos los estudiantes están dentro de los parámetros aceptables.</p>
                </div>
            )}

            {!cargando && estudiantes.length > 0 && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#e1e3e4] bg-[#f8f9fa]">
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">#</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Estudiante</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Código</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Nota prom.</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">% Incumplidas</th>
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Nivel</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f0f2f3]">
                                {estudiantes.map((est, i) => {
                                    const score = riesgoScore(est)
                                    const notaCritica = est.nota_promedio != null && est.nota_promedio < UMBRAL_NOTA
                                    const pctCritica = est.porcentaje_actividades_incumplidas >= UMBRAL_PCT
                                    return (
                                        <tr key={est.id} className="hover:bg-[#fafafa] transition-colors">
                                            <td className="px-4 py-3 text-[12px] font-bold text-[#9ba7ae] w-8">{i + 1}</td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2.5">
                                                    <div className="w-7 h-7 rounded-full bg-red-50 flex items-center justify-center text-[#d32f2f] flex-shrink-0 text-[11px] font-bold select-none">
                                                        {est.nombre?.[0]}{est.apellido?.[0]}
                                                    </div>
                                                    <div>
                                                        <p className="text-[13px] font-semibold text-[#191c1d]">{est.nombre} {est.apellido}</p>
                                                        <p className="text-[11px] text-[#9ba7ae]">{est.correo}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-[13px] text-[#4c616c] font-mono">
                                                {est.codigo_estudiante ?? '—'}
                                            </td>
                                            <td className="px-4 py-3">
                                                <BarraRiesgo valor={est.nota_promedio != null ? est.nota_promedio * 20 : null} critica={notaCritica} />
                                                <p className={`text-[11px] mt-0.5 ${notaCritica ? 'text-[#d32f2f] font-semibold' : 'text-[#9ba7ae]'}`}>
                                                    {est.nota_promedio?.toFixed(2) ?? '—'} / 5.0
                                                </p>
                                            </td>
                                            <td className="px-4 py-3">
                                                <BarraRiesgo valor={est.porcentaje_actividades_incumplidas} critica={pctCritica} />
                                                <p className={`text-[11px] mt-0.5 ${pctCritica ? 'text-[#d32f2f] font-semibold' : 'text-[#9ba7ae]'}`}>
                                                    {est.actividades_incumplidas ?? 0}/{est.total_actividades ?? 0} actividades
                                                </p>
                                            </td>
                                            <td className="px-4 py-3">
                                                <NivelRiesgo score={score} />
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
