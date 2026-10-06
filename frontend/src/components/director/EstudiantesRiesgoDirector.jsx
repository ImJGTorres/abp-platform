import { useState, useEffect, useCallback, useMemo } from 'react'
import { reportesApi } from '../../services/docenteApi'
import { periodosApi, cursosAdminApi } from '../../services/api'
import Semaforo from '../Compartidos/Semaforo'

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
    const [todosCursos, setTodosCursos] = useState([])
    const [cursoSel, setCursoSel] = useState('')
    const [filtroNivel, setFiltroNivel] = useState('todos')
    const [estudiantes, setEstudiantes] = useState([])
    const [cargando, setCargando] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        periodosApi.listar().then(setPeriodos).catch(() => {})
        cursosAdminApi.listar().then(data => {
            const arr = Array.isArray(data) ? data : (data?.results ?? [])
            setTodosCursos(arr)
        }).catch(() => {})
    }, [])

    const cursosFiltrados = useMemo(() => {
        if (!periodoSel) return todosCursos
        return todosCursos.filter(c => String(c.id_periodo_academico) === String(periodoSel))
    }, [todosCursos, periodoSel])

    const cargar = useCallback(async (periodoId, cursoId) => {
        setCargando(true)
        setError(null)
        try {
            const data = await reportesApi.bajoRendimiento({
                periodoId: periodoId ? Number(periodoId) : undefined,
                cursoId: cursoId ? Number(cursoId) : undefined,
                soloRiesgo: false,
            })
            setEstudiantes(data.estudiantes ?? [])
        } catch {
            setError('No se pudo cargar el reporte de estudiantes.')
        } finally {
            setCargando(false)
        }
    }, [])

    useEffect(() => {
        cargar(periodoSel, cursoSel)
    }, [periodoSel, cursoSel, cargar])

    const conteos = useMemo(() => {
        const c = { verde: 0, amarillo: 0, rojo: 0 }
        estudiantes.forEach(e => {
            if (e.nivel_semaforo && c[e.nivel_semaforo] !== undefined) {
                c[e.nivel_semaforo]++
            }
        })
        return c
    }, [estudiantes])

    const estudiantesVisibles = useMemo(() => {
        if (filtroNivel === 'todos') return estudiantes
        return estudiantes.filter(e => e.nivel_semaforo === filtroNivel)
    }, [estudiantes, filtroNivel])

    return (
        <div className="p-4 sm:p-6 flex flex-col gap-5">
            {/* Encabezado */}
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[11px] font-semibold text-[#9ba7ae] uppercase tracking-wide mb-0.5">Director</p>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d]">Semáforo de Rendimiento</h1>
                    <p className="text-[13px] text-[#9ba7ae] mt-0.5">
                        {cargando ? 'Cargando...' : `${estudiantes.length} estudiante${estudiantes.length !== 1 ? 's' : ''} evaluado${estudiantes.length !== 1 ? 's' : ''} · ${conteos.rojo} en riesgo crítico`}
                    </p>
                </div>
            </div>

            {/* Filtros de periodo y curso */}
            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-[#191c1d]">Periodo:</span>
                        <select
                            value={periodoSel}
                            onChange={e => { setPeriodoSel(e.target.value); setCursoSel('') }}
                            className="border border-[#e1e3e4] rounded-xl px-3 py-1.5 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/30"
                        >
                            <option value="">Todos los periodos</option>
                            {periodos.map(p => (
                                <option key={p.id} value={p.id}>{p.nombre ?? `Periodo ${p.id}`}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-[#191c1d]">Curso:</span>
                        <select
                            value={cursoSel}
                            onChange={e => setCursoSel(e.target.value)}
                            className="border border-[#e1e3e4] rounded-xl px-3 py-1.5 text-[13px] text-[#191c1d] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/30 max-w-[220px]"
                        >
                            <option value="">Todos los cursos</option>
                            {cursosFiltrados.map(c => (
                                <option key={c.id} value={c.id}>{c.nombre}</option>
                            ))}
                        </select>
                    </div>

                    {cargando && (
                        <div className="w-4 h-4 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                    )}
                </div>

                {/* Botones de filtro por color / nivel */}
                <div className="flex items-center gap-1.5 bg-[#f8f9fa] p-1 rounded-xl border border-[#e1e3e4]">
                    <button
                        onClick={() => setFiltroNivel('todos')}
                        className={`px-3 py-1.5 rounded-lg text-[12px] font-bold transition-all ${
                            filtroNivel === 'todos'
                                ? 'bg-white text-[#191c1d] shadow-sm'
                                : 'text-[#6b7280] hover:text-[#191c1d]'
                        }`}
                    >
                        Todos ({estudiantes.length})
                    </button>
                    <button
                        onClick={() => setFiltroNivel('verde')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold transition-all ${
                            filtroNivel === 'verde'
                                ? 'bg-[#f1f8e9] text-[#2e7d32] border border-[#a5d6a7] shadow-sm'
                                : 'text-[#2e7d32] hover:bg-[#f1f8e9]/50'
                        }`}
                    >
                        <span className="w-2 h-2 rounded-full bg-[#2e7d32]" />
                        Verde ({conteos.verde})
                    </button>
                    <button
                        onClick={() => setFiltroNivel('amarillo')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold transition-all ${
                            filtroNivel === 'amarillo'
                                ? 'bg-[#fffde7] text-[#f9a825] border border-[#fff59d] shadow-sm'
                                : 'text-[#f9a825] hover:bg-[#fffde7]/50'
                        }`}
                    >
                        <span className="w-2 h-2 rounded-full bg-[#f9a825]" />
                        Amarillo ({conteos.amarillo})
                    </button>
                    <button
                        onClick={() => setFiltroNivel('rojo')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold transition-all ${
                            filtroNivel === 'rojo'
                                ? 'bg-[#ffebee] text-[#c62828] border border-[#ef9a9a] shadow-sm'
                                : 'text-[#c62828] hover:bg-[#ffebee]/50'
                        }`}
                    >
                        <span className="w-2 h-2 rounded-full bg-[#c62828]" />
                        Rojo ({conteos.rojo})
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] rounded-xl px-4 py-3 text-[13px]">
                    {error}
                </div>
            )}

            {/* Tabla */}
            {!cargando && estudiantesVisibles.length === 0 && !error && (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] flex flex-col items-center justify-center py-16 gap-3">
                    <div className="w-12 h-12 rounded-full bg-[#f0f2f3] flex items-center justify-center">
                        <svg viewBox="0 0 20 20" fill="none" className="w-6 h-6 text-[#9ba7ae]" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                            <path d="M4 10l4 4 8-8" />
                        </svg>
                    </div>
                    <p className="text-[15px] font-semibold text-[#191c1d]">Sin estudiantes</p>
                    <p className="text-[13px] text-[#9ba7ae]">No hay estudiantes registrados para el filtro seleccionado.</p>
                </div>
            )}

            {!cargando && estudiantesVisibles.length > 0 && (
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
                                    <th className="px-4 py-3 text-left text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Semáforo</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f0f2f3]">
                                {estudiantesVisibles.map((est, i) => {
                                    const notaCritica = est.nota_promedio != null && est.nota_promedio < 3.0
                                    const pctCritica = est.porcentaje_actividades_incumplidas >= 50
                                    return (
                                        <tr key={est.id} className="hover:bg-[#fafafa] transition-colors">
                                            <td className="px-4 py-3 text-[12px] font-bold text-[#9ba7ae] w-8">{i + 1}</td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2.5">
                                                    <div className="w-7 h-7 rounded-full bg-[#f0f2f3] flex items-center justify-center text-[#4c616c] flex-shrink-0 text-[11px] font-bold select-none">
                                                        {est.nombre?.[0]}{est.apellido?.[0]}
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
                                                <Semaforo nivel={est.nivel_semaforo} size="sm" />
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
