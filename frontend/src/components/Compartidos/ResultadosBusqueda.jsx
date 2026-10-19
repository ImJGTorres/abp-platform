import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { busquedaApi } from '../../services/api'
import { GRUPOS_BUSQUEDA, mensajeErrorBusqueda } from '../../utils/busqueda'

const MIN_CARACTERES = 2

/**
 * Página de resultados completos de la búsqueda global (HU-045).
 * Lee el término de ?q= en la URL. Rutas: /director/busqueda y /admin/busqueda.
 */
export default function ResultadosBusqueda() {
    const [params] = useSearchParams()
    const q = (params.get('q') ?? '').trim()
    const consultable = q.length >= MIN_CARACTERES

    // Respuesta asociada al término con que se pidió; mientras no coincida con `q` se está cargando
    const [respuesta, setRespuesta] = useState(null)   // { q, data, error }

    useEffect(() => {
        if (!consultable) return
        let activo = true
        busquedaApi.buscar(q)
            .then(data => { if (activo) setRespuesta({ q, data, error: null }) })
            .catch(err => {
                if (!activo) return
                const msg = mensajeErrorBusqueda(err)
                setRespuesta({ q, data: null, error: msg })
                toast.error(msg)
            })
        return () => { activo = false }
    }, [q, consultable])

    const cargando = consultable && respuesta?.q !== q
    const resultados = respuesta?.q === q ? respuesta.data : null
    const error = respuesta?.q === q ? respuesta.error : null

    const total = GRUPOS_BUSQUEDA.reduce((n, g) => n + (resultados?.[g.clave]?.length ?? 0), 0)

    return (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Resultados de búsqueda</h1>
            <p className="text-[13px] text-[#6b7b83] mt-0.5 mb-6">
                {q ? <>Término buscado: <strong className="text-[#191c1d]">“{q}”</strong></> : 'Escribe un término en el buscador del encabezado.'}
            </p>

            {!consultable ? (
                <div className="text-center text-[13px] text-[#9ba7ae] py-10">
                    Escribe al menos {MIN_CARACTERES} caracteres para buscar.
                </div>
            ) : cargando ? (
                <div className="flex flex-col gap-3" aria-busy="true">
                    {[0, 1, 2].map(i => <div key={i} className="h-16 bg-[#f0f2f3] rounded-2xl animate-pulse" />)}
                </div>
            ) : error ? (
                <div className="text-center text-[#c62828] text-[13px] py-10">{error}</div>
            ) : total === 0 ? (
                <div className="flex flex-col items-center justify-center h-52 text-center gap-1">
                    <p className="text-[14px] font-semibold text-[#191c1d]">Sin resultados</p>
                    <p className="text-[12px] text-[#9ba7ae]">No se encontró nada para “{q}”.</p>
                </div>
            ) : (
                <div className="flex flex-col gap-6">
                    {GRUPOS_BUSQUEDA.map(g => {
                        const items = resultados?.[g.clave] ?? []
                        if (items.length === 0) return null
                        return (
                            <section key={g.clave}>
                                <h2 className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae] mb-2">
                                    {g.titulo} <span className="text-[#c4cdd2]">({items.length})</span>
                                </h2>
                                <div className="grid gap-2">
                                    {items.map(it => (
                                        <Link
                                            key={`${g.clave}-${it.id}`}
                                            to={it.enlace}
                                            className="bg-white border border-[#e1e3e4] rounded-2xl px-4 py-3 hover:border-[#d32f2f]/40 hover:shadow-sm transition-all"
                                        >
                                            <p className="text-[14px] font-bold text-[#191c1d] truncate">{it.titulo}</p>
                                            {it.subtitulo && <p className="text-[12px] text-[#6b7b83] truncate mt-0.5">{it.subtitulo}</p>}
                                        </Link>
                                    ))}
                                </div>
                            </section>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
