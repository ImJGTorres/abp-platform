import { useState, useEffect, useCallback } from 'react'
import { anunciosApi, session } from '../../services/api'

function formatFecha(iso) {
    if (!iso) return '—'
    try {
        const d = new Date(iso)
        return d.toLocaleDateString('es-CO', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    } catch {
        return '—'
    }
}

export default function MuroAnuncios({ cursoId, proyectoId, tituloSeccion = 'Muro de Anuncios' }) {
    const user = session.getUser()
    const rol = user?.tipo_rol
    const puedePublicar = ['administrador', 'director', 'docente'].includes(rol)

    const [anuncios, setAnuncios] = useState([])
    const [cargando, setCargando] = useState(true)
    const [error, setError] = useState(null)

    // Formulario de publicación
    const [titulo, setTitulo] = useState('')
    const [mensaje, setMensaje] = useState('')
    const [errorForm, setErrorForm] = useState('')
    const [enviando, setEnviando] = useState(false)
    const [toast, setToast] = useState('')

    const cargarAnuncios = useCallback(async () => {
        if (!cursoId && !proyectoId) return
        setCargando(true)
        setError(null)
        try {
            const data = cursoId
                ? await anunciosApi.listarCurso(cursoId)
                : await anunciosApi.listarProyecto(proyectoId)
            setAnuncios(Array.isArray(data) ? data : (data.results ?? []))
        } catch (err) {
            setError(err?.data?.detail ?? 'No se pudieron cargar los anuncios.')
        } finally {
            setCargando(false)
        }
    }, [cursoId, proyectoId])

    useEffect(() => {
        cargarAnuncios()
    }, [cargarAnuncios])

    async function handlePublicar(e) {
        e.preventDefault()
        setErrorForm('')

        const t = titulo.trim()
        const m = mensaje.trim()

        if (!t || !m) {
            setErrorForm('El título y el mensaje son requeridos.')
            return
        }

        setEnviando(true)
        try {
            const nuevo = cursoId
                ? await anunciosApi.publicarCurso(cursoId, { titulo: t, mensaje: m })
                : await anunciosApi.publicarProyecto(proyectoId, { titulo: t, mensaje: m })

            setAnuncios(prev => [nuevo, ...prev])
            setTitulo('')
            setMensaje('')
            setToast('Anuncio publicado satisfactoriamente.')
            setTimeout(() => setToast(''), 4000)
        } catch (err) {
            const msg = err?.data?.titulo?.[0]
                ?? err?.data?.mensaje?.[0]
                ?? err?.data?.detail
                ?? 'Error al publicar el anuncio.'
            setErrorForm(msg)
        } finally {
            setEnviando(false)
        }
    }

    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 flex flex-col gap-5">
            {/* Cabecera */}
            <div className="flex items-center justify-between border-b border-[#f0f2f3] pb-3 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-red-50 text-[#d32f2f] flex items-center justify-center flex-shrink-0">
                        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                        </svg>
                    </div>
                    <div>
                        <h2 className="text-[16px] font-bold text-[#191c1d] leading-tight">{tituloSeccion}</h2>
                        <p className="text-[11px] text-[#9ba7ae]">
                            {cargando ? 'Cargando anuncios...' : `${anuncios.length} anuncio${anuncios.length !== 1 ? 's' : ''}`}
                        </p>
                    </div>
                </div>

                {toast && (
                    <div className="px-3 py-1 bg-green-50 border border-green-200 text-green-700 text-[12px] font-semibold rounded-lg flex items-center gap-1.5 animate-fadeIn">
                        <svg viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
                            <path d="M13.854 3.646a.5.5 0 010 .708l-7 7a.5.5 0 01-.708 0l-3.5-3.5a.5.5 0 11.708-.708L6.5 10.293l6.646-6.647a.5.5 0 01.708 0z" />
                        </svg>
                        {toast}
                    </div>
                )}
            </div>

            {/* Formulario de publicación (Solo para Administrador, Director y Docente) */}
            {puedePublicar && (
                <form onSubmit={handlePublicar} className="bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl p-4 flex flex-col gap-3">
                    <p className="text-[13px] font-bold text-[#191c1d]">Publicar nuevo anuncio</p>

                    {errorForm && (
                        <div className="px-3 py-2 bg-red-50 border border-red-200 text-[#d32f2f] text-[12px] font-medium rounded-lg">
                            {errorForm}
                        </div>
                    )}

                    <div>
                        <input
                            type="text"
                            placeholder="Título del anuncio..."
                            value={titulo}
                            onChange={e => setTitulo(e.target.value)}
                            className="w-full text-[13px] border border-[#e1e3e4] rounded-lg px-3 py-2 bg-white text-[#191c1d] placeholder-[#9ba7ae] focus:outline-none focus:border-[#d32f2f] transition-colors"
                        />
                    </div>

                    <div>
                        <textarea
                            placeholder="Mensaje del anuncio..."
                            value={mensaje}
                            onChange={e => setMensaje(e.target.value)}
                            rows={3}
                            className="w-full text-[13px] border border-[#e1e3e4] rounded-lg px-3 py-2 bg-white text-[#191c1d] placeholder-[#9ba7ae] focus:outline-none focus:border-[#d32f2f] transition-colors resize-y"
                        />
                    </div>

                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={enviando}
                            className="px-4 py-2 bg-[#d32f2f] hover:bg-[#b71c1c] disabled:opacity-50 text-white text-[12px] font-bold rounded-lg transition-colors flex items-center gap-1.5"
                        >
                            {enviando ? (
                                <>
                                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    <span>Publicando...</span>
                                </>
                            ) : (
                                <>
                                    <svg viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
                                        <path d="M1.5 1.5A.5.5 0 001 2v12a.5.5 0 00.757.429l13-6a.5.5 0 000-.858l-13-6A.5.5 0 001.5 1.5z" />
                                    </svg>
                                    <span>Publicar anuncio</span>
                                </>
                            )}
                        </button>
                    </div>
                </form>
            )}

            {/* Lista de anuncios */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-[#d32f2f] text-[13px] rounded-xl px-4 py-3">
                    {error}
                </div>
            )}

            {cargando && anuncios.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                    <div className="w-7 h-7 border-2 border-[#d32f2f] border-t-transparent rounded-full animate-spin" />
                </div>
            ) : anuncios.length === 0 && !error ? (
                <div className="text-center py-12 border border-dashed border-[#e1e3e4] rounded-xl bg-[#fafafa]">
                    <div className="w-10 h-10 rounded-full bg-[#f0f2f3] flex items-center justify-center mx-auto mb-2 text-[#9ba7ae]">
                        <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                            <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" />
                        </svg>
                    </div>
                    <p className="text-[13px] font-semibold text-[#4c616c]">No hay anuncios publicados</p>
                    <p className="text-[12px] text-[#9ba7ae]">Los anuncios y novedades aparecerán en este espacio.</p>
                </div>
            ) : (
                <div className="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1">
                    {anuncios.map(a => (
                        <div key={a.id} className="border border-[#e1e3e4] rounded-xl p-4 bg-white hover:border-[#cfd8dc] transition-colors shadow-sm">
                            <div className="flex items-start justify-between gap-3 mb-2 flex-wrap">
                                <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-full bg-[#f0f2f3] flex items-center justify-center text-[#4c616c] font-bold text-[11px] select-none">
                                        {a.autor?.nombre?.[0]?.toUpperCase() ?? 'A'}
                                    </div>
                                    <div>
                                        <p className="text-[12px] font-semibold text-[#191c1d] leading-none">
                                            {a.autor ? `${a.autor.nombre} ${a.autor.apellido}` : 'Docente'}
                                        </p>
                                        <p className="text-[10px] text-[#9ba7ae] mt-0.5">
                                            {formatFecha(a.fecha_publicacion || a.fecha_creacion)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <h3 className="text-[14px] font-bold text-[#191c1d] mb-1">{a.titulo}</h3>
                            <p className="text-[13px] text-[#4c616c] leading-relaxed whitespace-pre-wrap">{a.mensaje}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
