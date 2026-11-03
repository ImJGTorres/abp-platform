import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'
import { busquedaApi, session } from '../../services/api'
import { GRUPOS_BUSQUEDA, rutaBusqueda, mensajeErrorBusqueda } from '../../utils/busqueda'

const MIN_CARACTERES = 2
const ESPERA_MS = 300
const MAX_POR_GRUPO = 5

function IconSearch() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="9" r="5.5" /><path d="M13.5 13.5L17 17" />
        </svg>
    )
}

/**
 * Campo de búsqueda global del encabezado (HU-045). Solo director y administrador.
 */
export default function BusquedaGlobal() {
    const rol = session.getUser()?.tipo_rol
    const navigate = useNavigate()
    const location = useLocation()
    const contenedor = useRef(null)

    const [texto,     setTexto]     = useState('')
    const [resultados, setResultados] = useState(null)
    const [cargando,  setCargando]  = useState(false)
    const [error,     setError]     = useState(null)
    const [abierto,   setAbierto]   = useState(false)

    const permitido = rol === 'director' || rol === 'administrador'
    const termino = texto.trim()
    const consultable = termino.length >= MIN_CARACTERES

    // Espera 300 ms tras dejar de escribir y descarta respuestas de búsquedas anteriores
    useEffect(() => {
        if (!permitido || !consultable) return
        let activo = true
        const timer = setTimeout(() => {
            setCargando(true)
            setError(null)
            busquedaApi.buscar(termino)
                .then(data => { if (activo) setResultados(data) })
                .catch(err => {
                    if (!activo) return
                    const msg = mensajeErrorBusqueda(err)
                    setError(msg)
                    toast.error(msg)
                })
                .finally(() => { if (activo) setCargando(false) })
        }, ESPERA_MS)
        return () => { activo = false; clearTimeout(timer) }
    }, [termino, consultable, permitido])

    // Cierra el desplegable al hacer clic fuera
    useEffect(() => {
        if (!abierto) return
        function alHacerClic(e) {
            if (contenedor.current && !contenedor.current.contains(e.target)) setAbierto(false)
        }
        document.addEventListener('mousedown', alHacerClic)
        return () => document.removeEventListener('mousedown', alHacerClic)
    }, [abierto])

    if (!permitido) return null

    const urlTodos = `${rutaBusqueda(rol, location.pathname)}?q=${encodeURIComponent(termino)}`

    function cambiar(e) {
        setTexto(e.target.value)
        setAbierto(true)
    }

    function alTeclear(e) {
        if (e.key === 'Escape') {
            setAbierto(false)
        } else if (e.key === 'Enter' && consultable) {
            e.preventDefault()
            setAbierto(false)
            navigate(urlTodos)
        }
    }

    function cerrarYLimpiar() {
        setAbierto(false)
        setTexto('')
        setResultados(null)
    }

    const gruposConDatos = GRUPOS_BUSQUEDA.filter(g => (resultados?.[g.clave] ?? []).length > 0)

    return (
        <div ref={contenedor} className="relative w-full max-w-[320px] hidden sm:block">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9ba7ae] pointer-events-none"><IconSearch /></span>
            <input
                type="search"
                value={texto}
                onChange={cambiar}
                onFocus={() => setAbierto(true)}
                onKeyDown={alTeclear}
                placeholder="Buscar cursos, proyectos, usuarios..."
                aria-label="Búsqueda global"
                className="w-full pl-9 pr-3 py-2 text-[13px] text-[#191c1d] bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors placeholder-[#c4cdd2]"
            />

            {abierto && termino.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1 bg-white rounded-xl border border-[#e1e3e4] shadow-lg z-30 max-h-[70vh] overflow-y-auto min-w-[320px]">
                    {!consultable ? (
                        <p className="px-4 py-3 text-[12px] text-[#9ba7ae]">Escribe al menos {MIN_CARACTERES} caracteres.</p>
                    ) : cargando && !resultados ? (
                        <p className="px-4 py-3 text-[12px] text-[#9ba7ae]">Buscando...</p>
                    ) : error ? (
                        <p className="px-4 py-3 text-[12px] text-[#c62828]">{error}</p>
                    ) : gruposConDatos.length === 0 ? (
                        <p className="px-4 py-3 text-[12px] text-[#9ba7ae]">Sin resultados para “{termino}”.</p>
                    ) : (
                        <>
                            {gruposConDatos.map(g => {
                                const items = resultados[g.clave]
                                return (
                                    <div key={g.clave} className="py-1.5">
                                        <p className="px-4 pt-1 pb-1 text-[10px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae]">{g.titulo}</p>
                                        {items.slice(0, MAX_POR_GRUPO).map(it => (
                                            <Link
                                                key={`${g.clave}-${it.id}`}
                                                to={it.enlace}
                                                onClick={cerrarYLimpiar}
                                                className="block px-4 py-2 hover:bg-[#f0f2f3] transition-colors"
                                            >
                                                <p className="text-[13px] font-semibold text-[#191c1d] truncate">{it.titulo}</p>
                                                {it.subtitulo && <p className="text-[11px] text-[#9ba7ae] truncate">{it.subtitulo}</p>}
                                            </Link>
                                        ))}
                                    </div>
                                )
                            })}
                            <Link
                                to={urlTodos}
                                onClick={() => setAbierto(false)}
                                className="block px-4 py-2.5 text-[12px] font-semibold text-[#d32f2f] hover:bg-[#fff5f5] border-t border-[#f0f2f3] transition-colors"
                            >
                                Ver todos los resultados
                            </Link>
                        </>
                    )}
                </div>
            )}
        </div>
    )
}
