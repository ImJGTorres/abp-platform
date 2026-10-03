import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { configuracionApi, buildMediaUrl } from '../services/api'

const MAX_CARACTERES = 200
const MAX_LOGO_BYTES = 2 * 1024 * 1024
const EXTENSIONES_LOGO = ['png', 'jpg', 'jpeg']

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatFecha(iso) {
    if (!iso) return null
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return null
    return d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Solo los 400 traen un mensaje pensado para el usuario (validación de DRF);
// en 5xx, 404, etc. el texto del backend es técnico, así que se usa `porDefecto`.
function mensajeError(err, porDefecto) {
    if (err?.type === 'network') return 'No hay conexión con el servidor. Revisa tu conexión e intenta de nuevo.'
    if (err?.status !== 400) return porDefecto
    const data = err?.data
    if (!data) return porDefecto
    if (typeof data.detail === 'string') return data.detail
    for (const valor of Object.values(data)) {
        if (Array.isArray(valor) && valor.length) return String(valor[0])
        if (typeof valor === 'string') return valor
    }
    return porDefecto
}

function erroresPorCampo(data) {
    const errores = {}
    for (const campo of ['nombre_institucion', 'programa_academico', 'logotipo']) {
        const v = data?.[campo]
        if (Array.isArray(v) && v.length) errores[campo] = String(v[0])
        else if (typeof v === 'string') errores[campo] = v
    }
    return errores
}

function validar(form) {
    const errores = {}
    for (const [campo, etiqueta] of [['nombre_institucion', 'El nombre de la institución'], ['programa_academico', 'El programa académico']]) {
        const valor = form[campo].trim()
        if (!valor) errores[campo] = `${etiqueta} es obligatorio.`
        else if (valor.length > MAX_CARACTERES) errores[campo] = `Máximo ${MAX_CARACTERES} caracteres.`
    }
    return errores
}

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconUpload() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13V3M6 7l4-4 4 4" />
            <path d="M3 13v3a1 1 0 001 1h12a1 1 0 001-1v-3" />
        </svg>
    )
}

function IconImage() {
    return (
        <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="16" rx="2" />
            <circle cx="9" cy="10" r="2" />
            <path d="M21 16l-5-5-9 9" />
        </svg>
    )
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function CampoTexto({ id, label, value, onChange, error, placeholder }) {
    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor={id} className="text-[12px] font-semibold text-[#4c616c]">
                {label} <span className="text-[#d32f2f]">*</span>
            </label>
            <input
                id={id}
                type="text"
                value={value}
                maxLength={MAX_CARACTERES}
                placeholder={placeholder}
                onChange={e => onChange(e.target.value)}
                className={`px-3 py-2 text-[13px] text-[#191c1d] bg-white border rounded-xl focus:outline-none transition-colors ${
                    error ? 'border-[#d32f2f]' : 'border-[#e1e3e4] focus:border-[#d32f2f]'
                }`}
            />
            <div className="flex items-start justify-between gap-2">
                <p className="text-[11px] text-[#d32f2f] min-h-[14px]">{error ?? ''}</p>
                <p className="text-[11px] text-[#9ba7ae] flex-shrink-0">{value.length}/{MAX_CARACTERES}</p>
            </div>
        </div>
    )
}

// Réplica del encabezado del PDF (exportaciones/generadores/pdf.py → _encabezado_pagina)
function VistaPreviaMembrete({ logo, nombre, programa }) {
    return (
        <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-4">
                <div className="w-16 h-16 flex-shrink-0 flex items-center justify-center rounded-lg overflow-hidden">
                    {logo
                        ? <img src={logo} alt="Logotipo" className="max-w-full max-h-full object-contain" />
                        : <div className="w-full h-full bg-[#f0f2f3] text-[#9ba7ae] flex items-center justify-center"><IconImage /></div>
                    }
                </div>
                <div className="min-w-0">
                    <p className="text-[14px] font-bold text-[#424242] break-words">
                        {nombre.trim() || 'Nombre de la institución'}
                    </p>
                    <p className="text-[12px] text-[#424242] break-words">
                        {programa.trim() || 'Programa académico'}
                    </p>
                </div>
            </div>
            <div className="mt-3 h-[2px] bg-[#d32f2f]" />
            {/* Simulación del cuerpo del reporte */}
            <div className="mt-4 flex flex-col items-center gap-2 opacity-40">
                <div className="h-2.5 w-40 bg-[#d32f2f] rounded" />
                <div className="h-2 w-full bg-[#e1e3e4] rounded" />
                <div className="h-2 w-5/6 bg-[#e1e3e4] rounded" />
                <div className="h-2 w-4/6 bg-[#e1e3e4] rounded" />
            </div>
        </div>
    )
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function IdentidadInstitucional() {
    const [form, setForm] = useState({ nombre_institucion: '', programa_academico: '' })
    const [logoActual, setLogoActual] = useState(null)       // URL guardada en el backend
    const [archivo, setArchivo] = useState(null)             // File nuevo sin guardar
    const [previewUrl, setPreviewUrl] = useState(null)       // object URL del archivo nuevo
    const [fechaActualizacion, setFechaActualizacion] = useState(null)
    const [errores, setErrores] = useState({})
    const [cargando, setCargando] = useState(true)
    const [guardando, setGuardando] = useState(false)
    const [errorCarga, setErrorCarga] = useState(null)
    const inputLogo = useRef(null)

    function aplicarDatos(data) {
        setForm({
            nombre_institucion: data?.nombre_institucion ?? '',
            programa_academico: data?.programa_academico ?? '',
        })
        setLogoActual(data?.logotipo ? buildMediaUrl(data.logotipo) : null)
        setFechaActualizacion(data?.fecha_actualizacion ?? null)
    }

    useEffect(() => {
        let activo = true
        configuracionApi.obtenerIdentidad()
            .then(data => { if (activo) aplicarDatos(data) })
            .catch(err => {
                if (!activo) return
                // 404: aún no hay identidad registrada → formulario vacío sin aviso.
                // Otros errores no bloquean el formulario: se muestra un aviso encima.
                if (err?.status !== 404) setErrorCarga(mensajeError(err, 'No se pudieron cargar los datos guardados de la identidad institucional.'))
            })
            .finally(() => { if (activo) setCargando(false) })
        return () => { activo = false }
    }, [])

    // Libera el object URL de la vista previa al cambiarlo o desmontar
    useEffect(() => {
        return () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }
    }, [previewUrl])

    function cambiarCampo(campo, valor) {
        setForm(f => ({ ...f, [campo]: valor }))
        if (errores[campo]) setErrores(e => ({ ...e, [campo]: undefined }))
    }

    function limpiarArchivo() {
        setArchivo(null)
        setPreviewUrl(null)
        if (inputLogo.current) inputLogo.current.value = ''
    }

    function seleccionarLogo(e) {
        const file = e.target.files?.[0]
        if (!file) return

        const ext = file.name.split('.').pop()?.toLowerCase()
        if (!EXTENSIONES_LOGO.includes(ext)) {
            setErrores(er => ({ ...er, logotipo: 'Solo se permiten archivos PNG o JPG.' }))
            limpiarArchivo()
            return
        }
        if (file.size > MAX_LOGO_BYTES) {
            setErrores(er => ({ ...er, logotipo: 'El logotipo no puede superar 2 MB.' }))
            limpiarArchivo()
            return
        }

        setErrores(er => ({ ...er, logotipo: undefined }))
        setArchivo(file)
        setPreviewUrl(URL.createObjectURL(file))
    }

    async function guardar(e) {
        e.preventDefault()
        const erroresCliente = validar(form)
        if (Object.keys(erroresCliente).length) {
            setErrores(erroresCliente)
            return
        }

        const formData = new FormData()
        formData.append('nombre_institucion', form.nombre_institucion.trim())
        formData.append('programa_academico', form.programa_academico.trim())
        if (archivo) formData.append('logotipo', archivo)

        setGuardando(true)
        try {
            const data = await configuracionApi.actualizarIdentidad(formData)
            aplicarDatos(data)
            limpiarArchivo()
            setErrores({})
            toast.success('Identidad institucional actualizada.')
        } catch (err) {
            if (err?.status === 400) setErrores(erroresPorCampo(err.data))
            toast.error(mensajeError(err, 'No se pudo guardar la identidad institucional. Intenta de nuevo más tarde.'))
        } finally {
            setGuardando(false)
        }
    }

    if (cargando) {
        return <p className="text-[13px] text-[#9ba7ae] py-10 text-center">Cargando identidad institucional...</p>
    }

    const logoVista = previewUrl ?? logoActual
    const fecha = formatFecha(fechaActualizacion)

    return (
        <div className="max-w-[1000px]" style={{ fontFamily: "'Manrope', sans-serif" }}>
            {/* ── Cabecera ─────────────────────────────────────────────────── */}
            <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
                <div>
                    <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Identidad institucional</h1>
                    <p className="text-[13px] text-[#6b7b83] mt-0.5">
                        Nombre, programa y logotipo que aparecen en el encabezado de los reportes exportados.
                    </p>
                </div>
                {fecha && (
                    <p className="text-[12px] text-[#9ba7ae] pt-1">
                        Última actualización: <span className="font-semibold text-[#4c616c]">{fecha}</span>
                    </p>
                )}
            </div>

            {errorCarga && (
                <div className="flex items-center justify-between gap-3 mb-4 px-4 py-3 bg-[#fff8e1] border border-[#ffe082] rounded-xl flex-wrap">
                    <p className="text-[12px] text-[#8d6e00]">
                        <span className="font-semibold">{errorCarga}</span> Puedes editar el formulario, pero lo que ves no refleja lo que está guardado actualmente.
                    </p>
                    <button
                        type="button"
                        onClick={() => window.location.reload()}
                        className="text-[12px] font-semibold text-[#8d6e00] underline hover:no-underline"
                    >
                        Reintentar
                    </button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                {/* ── Formulario ───────────────────────────────────────────── */}
                <form onSubmit={guardar} noValidate className="bg-white border border-[#e1e3e4] rounded-2xl p-5 flex flex-col gap-3">
                    <CampoTexto
                        id="nombre_institucion"
                        label="Nombre de la institución"
                        placeholder="Ej. Universidad Francisco de Paula Santander"
                        value={form.nombre_institucion}
                        onChange={v => cambiarCampo('nombre_institucion', v)}
                        error={errores.nombre_institucion}
                    />
                    <CampoTexto
                        id="programa_academico"
                        label="Programa académico"
                        placeholder="Ej. Ingeniería de Sistemas"
                        value={form.programa_academico}
                        onChange={v => cambiarCampo('programa_academico', v)}
                        error={errores.programa_academico}
                    />

                    <div className="flex flex-col gap-1.5">
                        <span className="text-[12px] font-semibold text-[#4c616c]">Logotipo</span>
                        <div className="flex items-center gap-3 flex-wrap">
                            <label
                                htmlFor="logotipo"
                                className="flex items-center gap-2 px-3.5 py-2 text-[13px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors cursor-pointer"
                            >
                                <IconUpload />
                                {logoVista ? 'Cambiar logotipo' : 'Subir logotipo'}
                            </label>
                            <input
                                ref={inputLogo}
                                id="logotipo"
                                type="file"
                                accept=".png,.jpg,.jpeg"
                                onChange={seleccionarLogo}
                                className="hidden"
                            />
                            {archivo && (
                                <div className="flex items-center gap-2 min-w-0">
                                    <span className="text-[12px] text-[#191c1d] truncate max-w-[180px]">{archivo.name}</span>
                                    <button type="button" onClick={limpiarArchivo} className="text-[12px] font-semibold text-[#9ba7ae] hover:text-[#d32f2f]">
                                        Quitar
                                    </button>
                                </div>
                            )}
                        </div>
                        <p className="text-[11px] text-[#9ba7ae]">PNG o JPG, máximo 2 MB.</p>
                        {errores.logotipo && <p className="text-[11px] text-[#d32f2f]">{errores.logotipo}</p>}
                    </div>

                    <div className="flex justify-end pt-2 border-t border-[#f0f2f3] mt-1">
                        <button
                            type="submit"
                            disabled={guardando}
                            className="px-5 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                            {guardando ? 'Guardando...' : 'Guardar'}
                        </button>
                    </div>
                </form>

                {/* ── Vista previa ─────────────────────────────────────────── */}
                <section>
                    <h2 className="text-[11px] font-bold uppercase tracking-[0.7px] text-[#9ba7ae] mb-2">
                        Vista previa del membrete
                    </h2>
                    <VistaPreviaMembrete
                        logo={logoVista}
                        nombre={form.nombre_institucion}
                        programa={form.programa_academico}
                    />
                    {archivo && (
                        <p className="text-[11px] text-[#9ba7ae] mt-2">El logotipo nuevo se aplicará al guardar.</p>
                    )}
                </section>
            </div>
        </div>
    )
}
