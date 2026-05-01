import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cursosApi } from '../../services/docenteApi'

const ESTADO_CONFIG = {
    activo:   { label: 'Activo',   bg: 'bg-[#e8f5e9]', text: 'text-[#2e7d32]' },
    borrador: { label: 'Borrador', bg: 'bg-[#fff8e1]', text: 'text-[#f57f17]' },
    cerrado:  { label: 'Cerrado',  bg: 'bg-[#f0f2f3]', text: 'text-[#9ba7ae]' },
}

function CursoCard({ curso, onClick }) {
    const estado = ESTADO_CONFIG[curso.estado] ?? ESTADO_CONFIG.borrador

    return (
        <button
            onClick={onClick}
            className="bg-white rounded-2xl border border-[#e1e3e4] p-5 text-left hover:shadow-md hover:border-[#c9cbcc] transition-all group w-full"
        >
            {/* Estado badge */}
            <div className="flex items-start justify-between gap-2 mb-3">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold ${estado.bg} ${estado.text}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${estado.text.replace('text-', 'bg-')}`} />
                    {estado.label}
                </span>
                <svg className="w-4 h-4 text-[#9ba7ae] group-hover:text-[#d32f2f] transition-colors flex-shrink-0 mt-0.5"
                    viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 3l5 5-5 5" />
                </svg>
            </div>

            {/* Nombre */}
            <h3 className="text-[15px] font-bold text-[#191c1d] leading-snug mb-1 group-hover:text-[#d32f2f] transition-colors line-clamp-2">
                {curso.nombre}
            </h3>

            {/* Código */}
            <p className="text-[12px] text-[#9ba7ae] font-medium mb-3">{curso.codigo}</p>

            {/* Descripción */}
            {curso.descripcion && (
                <p className="text-[13px] text-[#5b403d] leading-relaxed mb-4 line-clamp-2">{curso.descripcion}</p>
            )}

            {/* Footer stats */}
            <div className="flex items-center gap-3 pt-3 border-t border-[#f0f2f3]">
                <div className="flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2z" />
                        <path d="M10 7v4M8 9h4" />
                    </svg>
                    <span className="text-[12px] text-[#5b403d] font-medium">{curso.total_proyectos} proyecto{curso.total_proyectos !== 1 ? 's' : ''}</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 7a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path d="M3 14a5 5 0 0110 0" />
                    </svg>
                    <span className="text-[12px] text-[#5b403d] font-medium">{curso.cantidad_estudiantes_actual}/{curso.cantidad_max_estudiantes}</span>
                </div>
                <div className="ml-auto">
                    <span className="text-[11px] text-[#9ba7ae]">{curso.periodo_nombre}</span>
                </div>
            </div>
        </button>
    )
}

export default function GestionCursos() {
    const navigate = useNavigate()
    const [cursos, setCursos] = useState([])
    const [loading, setLoading] = useState(true)
    const [filtroEstado, setFiltroEstado] = useState('')
    const [busqueda, setBusqueda] = useState('')

    useEffect(() => {
        cargarCursos()
    }, [])

    async function cargarCursos() {
        setLoading(true)
        try {
            const data = await cursosApi.listar()
            setCursos(data.results ?? data)
        } catch (error) {
            console.error('Error cargando cursos:', error)
        } finally {
            setLoading(false)
        }
    }

    const cursosFiltrados = cursos.filter(c => {
        if (filtroEstado && c.estado !== filtroEstado) return false
        if (busqueda) {
            const q = busqueda.toLowerCase()
            if (!c.nombre.toLowerCase().includes(q) && !c.codigo.toLowerCase().includes(q)) return false
        }
        return true
    })

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
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>

            {/* Header */}
            <div className="mb-6">
                <h1 className="text-[22px] sm:text-[24px] font-bold text-[#191c1d] leading-tight">Mis cursos</h1>
                <p className="text-[13px] text-[#9ba7ae] mt-0.5">Selecciona un curso para ver sus proyectos y equipos</p>
            </div>

            {/* Filtros */}
            <div className="mb-5 flex flex-col sm:flex-row gap-3">
                <input
                    type="text"
                    value={busqueda}
                    onChange={e => setBusqueda(e.target.value)}
                    placeholder="Buscar por nombre o código..."
                    className="flex-1 h-10 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all bg-white"
                />
                <select
                    value={filtroEstado}
                    onChange={e => setFiltroEstado(e.target.value)}
                    className="h-10 px-4 rounded-xl border-2 border-[#e1e3e4] text-[13px] outline-none focus:border-[#d32f2f] transition-all bg-white sm:w-48"
                >
                    <option value="">Todos los estados</option>
                    <option value="activo">Activo</option>
                    <option value="borrador">Borrador</option>
                    <option value="cerrado">Cerrado</option>
                </select>
            </div>

            {/* Mosaico de cursos */}
            {cursosFiltrados.length === 0 ? (
                <div className="bg-white rounded-2xl border border-[#e1e3e4] p-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#fdf6f0] flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-[#f57c00]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M2 3h6a2 2 0 012 2v11a2 2 0 00-2 2H2z" />
                            <path d="M18 3h-6a2 2 0 00-2 2v11a2 2 0 012 2h6z" />
                        </svg>
                    </div>
                    <h3 className="text-[15px] font-semibold text-[#191c1d] mb-1">
                        {cursos.length === 0 ? 'No tienes cursos asignados' : 'Sin resultados'}
                    </h3>
                    <p className="text-[13px] text-[#9ba7ae]">
                        {cursos.length === 0
                            ? 'El administrador debe asignarte cursos para que aparezcan aquí.'
                            : 'Intenta con otro filtro o búsqueda.'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {cursosFiltrados.map(c => (
                        <CursoCard
                            key={c.id}
                            curso={c}
                            onClick={() => navigate(`/docente/cursos/${c.id}`)}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}