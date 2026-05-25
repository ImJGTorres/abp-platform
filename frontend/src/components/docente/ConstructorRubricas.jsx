import { useState, useEffect, Fragment } from 'react'
import { useParams } from 'react-router-dom'
import { rubricasApi } from '../../services/docenteApi'

// ── Icons ─────────────────────────────────────────────────────────────────────

function IconPlus() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M10 4v12M4 10h12" />
        </svg>
    )
}

function IconTrash() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 6h14M8 6V4h4v2M6 6l1 11h6l1-11" />
        </svg>
    )
}

function IconSave() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="14" height="14" rx="2" />
            <path d="M7 3v5h6V3" />
            <path d="M5 13h10" />
        </svg>
    )
}

function IconEdit() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 3.5a2.121 2.121 0 013 3L6 18l-4 1 1-4 11.5-11.5z" />
        </svg>
    )
}

function IconBack() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M12 4L6 10l6 6" />
        </svg>
    )
}

function IconEye() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 10s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z" />
            <circle cx="10" cy="10" r="2.5" />
        </svg>
    )
}

// ── Constantes ────────────────────────────────────────────────────────────────

const NIVELES = [
    { key: 'excelente',     nivel: 4, label: 'Excelente',     etiqueta: 'excelente',     color: '#2e7d32', bg: '#f1f8e9' },
    { key: 'satisfactorio', nivel: 3, label: 'Satisfactorio', etiqueta: 'satisfactorio', color: '#1565c0', bg: '#e3f2fd' },
    { key: 'basico',        nivel: 2, label: 'Básico',        etiqueta: 'basico',        color: '#e65100', bg: '#fff3e0' },
    { key: 'insuficiente',  nivel: 1, label: 'Insuficiente',  etiqueta: 'insuficiente',  color: '#c62828', bg: '#ffebee' },
]

function nivelesVacios() {
    return Object.fromEntries(
        NIVELES.map(n => [n.key, { descripcion: '', puntos: 0 }])
    )
}

function criterioVacio() {
    return {
        id: crypto.randomUUID(),
        nombre: '',
        niveles: nivelesVacios(),
    }
}

// Normaliza criterios desde la API al formato interno
function normalizarCriterios(criteriosApi) {
    return (criteriosApi ?? []).map(c => {
        const nivelPorEtiqueta = {}
        for (const nv of (c.niveles ?? [])) {
            nivelPorEtiqueta[nv.etiqueta] = { descripcion: nv.descripcion ?? '', puntos: nv.puntos ?? 0 }
        }
        return {
            id: c.id ?? crypto.randomUUID(),
            nombre: c.nombre ?? '',
            niveles: Object.fromEntries(
                NIVELES.map(n => [
                    n.key,
                    nivelPorEtiqueta[n.etiqueta] ?? { descripcion: '', puntos: 0 },
                ])
            ),
        }
    })
}

// Extrae el primer string de mensaje de una estructura anidada arbitraria
function extraerMensaje(val) {
    if (!val) return ''
    if (typeof val === 'string') return val
    if (Array.isArray(val)) {
        for (const item of val) {
            const m = extraerMensaje(item)
            if (m) return m
        }
        return ''
    }
    if (typeof val === 'object') {
        for (const v of Object.values(val)) {
            const m = extraerMensaje(v)
            if (m) return m
        }
        return ''
    }
    return String(val)
}

// Convierte errores del backend a string legible
function parsearError(data) {
    if (!data) return 'No se pudo guardar la rúbrica.'
    if (typeof data === 'string') return data
    if (data.detail) return String(data.detail)
    if (data.criterios) {
        if (typeof data.criterios === 'string') return data.criterios
        if (Array.isArray(data.criterios)) {
            for (let i = 0; i < data.criterios.length; i++) {
                const e = data.criterios[i]
                if (!e || typeof e !== 'object' || Object.keys(e).length === 0) continue
                for (const [field, msgs] of Object.entries(e)) {
                    const msg = extraerMensaje(msgs)
                    if (msg) return `Criterio ${i + 1} — ${field}: ${msg}`
                }
            }
        }
    }
    const entries = Object.entries(data)
    if (entries.length > 0) {
        const [field, msgs] = entries[0]
        const msg = extraerMensaje(msgs)
        return `${field}: ${msg}`
    }
    return 'No se pudo guardar la rúbrica.'
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ConstructorRubricas() {
    const { proyectoId } = useParams()

    const [rubricas,     setRubricas]     = useState([])
    const [loadingLista, setLoadingLista] = useState(true)
    const [errorLista,   setErrorLista]   = useState(null)

    // 'lista' | 'detalle' | 'editor'
    const [vista,        setVista]        = useState('lista')
    const [rubricaVista, setRubricaVista] = useState(null)   // para detalle
    const [editando,     setEditando]     = useState(null)   // para editor

    const [saving,       setSaving]       = useState(false)
    const [saveError,    setSaveError]    = useState(null)

    // Modal eliminar
    const [confirmEliminar, setConfirmEliminar] = useState(null)  // { id, nombre }
    const [eliminando,      setEliminando]      = useState(false)
    const [errorEliminar,   setErrorEliminar]   = useState('')

    useEffect(() => { cargarRubricas() }, [proyectoId])

    async function cargarRubricas() {
        setLoadingLista(true)
        setErrorLista(null)
        try {
            const data = await rubricasApi.listar(proyectoId)
            setRubricas(Array.isArray(data) ? data : (data.results ?? []))
        } catch {
            setErrorLista('No se pudieron cargar las rúbricas.')
        } finally {
            setLoadingLista(false)
        }
    }

    function verDetalle(r) {
        setRubricaVista(r)
        setVista('detalle')
    }

    function nuevaRubrica() {
        setEditando({ id: null, nombre: '', descripcion: '', criterios: [criterioVacio()] })
        setSaveError(null)
        setVista('editor')
    }

    function editarRubrica(r) {
        const criterios = normalizarCriterios(r.criterios)
        setEditando({
            id: r.id,
            nombre: r.nombre ?? '',
            descripcion: r.descripcion ?? '',
            criterios: criterios.length ? criterios : [criterioVacio()],
        })
        setSaveError(null)
        setVista('editor')
    }

    function volverALista() {
        setVista('lista')
        setEditando(null)
        setRubricaVista(null)
        setSaveError(null)
    }

    async function ejecutarEliminar() {
        if (!confirmEliminar) return
        setEliminando(true)
        setErrorEliminar('')
        try {
            await rubricasApi.eliminar(confirmEliminar.id)
            setRubricas(prev => prev.filter(r => r.id !== confirmEliminar.id))
            // Si se estaba viendo el detalle de la que se eliminó, volver a lista
            if (rubricaVista?.id === confirmEliminar.id) volverALista()
            setConfirmEliminar(null)
        } catch (e) {
            const msg = e?.data?.detail ?? 'No se puede eliminar porque la rúbrica ya tiene evaluaciones registradas.'
            setErrorEliminar(msg)
        } finally {
            setEliminando(false)
        }
    }

    // ── Edición ───────────────────────────────────────────────────────────────

    function setCampo(field, value) {
        setEditando(e => ({ ...e, [field]: value }))
    }

    function addCriterio() {
        setEditando(e => ({ ...e, criterios: [...e.criterios, criterioVacio()] }))
    }

    function removeCriterio(id) {
        setEditando(e => ({ ...e, criterios: e.criterios.filter(c => c.id !== id) }))
    }

    function updateCriterio(id, field, value) {
        setEditando(e => ({
            ...e,
            criterios: e.criterios.map(c => {
                if (c.id !== id) return c
                if (field.startsWith('nivel_')) {
                    const parts = field.split('_')          // ['nivel', key, sub]
                    const sub = parts[parts.length - 1]     // 'desc' | 'pts'
                    const key = parts.slice(1, -1).join('_') // the etiqueta key
                    return {
                        ...c,
                        niveles: {
                            ...c.niveles,
                            [key]: {
                                ...c.niveles[key],
                                [sub === 'desc' ? 'descripcion' : 'puntos']: value,
                            },
                        },
                    }
                }
                return { ...c, [field]: value }
            }),
        }))
    }

    // ── Validaciones ──────────────────────────────────────────────────────────

    function jerarquiaValida(c) {
        const ins = parseFloat(c.niveles.insuficiente.puntos) || 0
        const bas = parseFloat(c.niveles.basico.puntos) || 0
        const sat = parseFloat(c.niveles.satisfactorio.puntos) || 0
        const exc = parseFloat(c.niveles.excelente.puntos) || 0
        return ins < bas && bas < sat && sat < exc
    }

    const sumaExcelente = editando
        ? editando.criterios.reduce((acc, c) => acc + (parseFloat(c.niveles.excelente.puntos) || 0), 0)
        : 0

    const sumaValida = Math.abs(sumaExcelente - 100) < 0.01

    const formValida =
        editando?.nombre?.trim() &&
        editando?.criterios?.length > 0 &&
        editando?.criterios?.every(c => c.nombre.trim()) &&
        editando?.criterios?.every(c => jerarquiaValida(c)) &&
        sumaValida

    // ── Guardar ───────────────────────────────────────────────────────────────

    async function guardar() {
        if (!formValida || saving) return
        setSaving(true)
        setSaveError(null)
        try {
            const payload = {
                nombre:      editando.nombre.trim(),
                descripcion: editando.descripcion.trim(),
                criterios: editando.criterios.map(c => ({
                    nombre: c.nombre.trim(),
                    // Backend aún requiere peso_porcentual; lo igualamos a los puntos de excelente
                    peso_porcentual: parseFloat(c.niveles.excelente.puntos) || 0,
                    niveles: NIVELES.map(n => ({
                        nivel:       n.nivel,
                        etiqueta:    n.etiqueta,
                        descripcion: c.niveles[n.key].descripcion,
                        puntos:      parseFloat(c.niveles[n.key].puntos) || 0,
                    })),
                })),
            }

            let result
            if (editando.id) {
                result = await rubricasApi.actualizar(editando.id, payload)
                setRubricas(prev => prev.map(r => r.id === editando.id ? result : r))
            } else {
                result = await rubricasApi.crear(proyectoId, payload)
                setRubricas(prev => [...prev, result])
            }
            volverALista()
        } catch (e) {
            setSaveError(parsearError(e?.data))
        } finally {
            setSaving(false)
        }
    }

    // ── Vista: Lista ──────────────────────────────────────────────────────────

    if (vista === 'lista') {
        return (
            <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight">Rúbricas</h1>
                        <p className="text-[13px] text-[#6b7b83] mt-0.5">
                            Define criterios y niveles de desempeño para evaluar a tus estudiantes.
                        </p>
                    </div>
                    <button
                        onClick={nuevaRubrica}
                        className="flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors shadow-sm"
                    >
                        <IconPlus />
                        Nueva rúbrica
                    </button>
                </div>

                {loadingLista ? (
                    <div className="flex items-center justify-center h-40 text-[#9ba7ae] text-[13px]">
                        Cargando rúbricas...
                    </div>
                ) : errorLista ? (
                    <div className="text-center text-[#c62828] text-[13px] py-10">{errorLista}</div>
                ) : rubricas.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-52 text-center gap-3">
                        <div className="w-14 h-14 bg-[#fce4e4] rounded-2xl flex items-center justify-center">
                            <svg viewBox="0 0 24 24" className="w-7 h-7 text-[#d32f2f]" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="3" /><path d="M9 9h6M9 12h6M9 15h4" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-[14px] font-semibold text-[#191c1d]">Aún no hay rúbricas</p>
                            <p className="text-[12px] text-[#9ba7ae] mt-0.5">Crea la primera rúbrica para este proyecto.</p>
                        </div>
                        <button
                            onClick={nuevaRubrica}
                            className="mt-1 px-4 py-2 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors"
                        >
                            Crear rúbrica
                        </button>
                    </div>
                ) : (
                    <div className="grid gap-3">
                        {rubricas.map(r => (
                            <div
                                key={r.id}
                                onClick={() => verDetalle(r)}
                                className="bg-white border border-[#e1e3e4] rounded-2xl p-4 flex items-start gap-4 hover:border-[#d32f2f]/40 hover:shadow-sm transition-all cursor-pointer"
                            >
                                <div className="flex-1 min-w-0">
                                    <p className="text-[15px] font-bold text-[#191c1d] truncate">{r.nombre}</p>
                                    {r.descripcion && (
                                        <p className="text-[12px] text-[#6b7b83] mt-0.5 line-clamp-2">{r.descripcion}</p>
                                    )}
                                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                                        <span className="text-[11px] font-semibold text-[#9ba7ae] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                                            {(r.criterios ?? []).length} criterio{(r.criterios ?? []).length !== 1 ? 's' : ''}
                                        </span>
                                        {r.tipo && (
                                            <span className="text-[11px] font-semibold text-[#1565c0] bg-[#e3f2fd] px-2 py-0.5 rounded-lg capitalize">
                                                {r.tipo_display ?? r.tipo}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 flex-shrink-0" onClick={e => e.stopPropagation()}>
                                    <button
                                        onClick={() => editarRubrica(r)}
                                        className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors"
                                    >
                                        <IconEdit />
                                        Editar
                                    </button>
                                    <button
                                        onClick={() => { setConfirmEliminar({ id: r.id, nombre: r.nombre }); setErrorEliminar('') }}
                                        className="flex items-center justify-center w-8 h-8 text-[#ba1a1a] bg-[#fff1f0] rounded-xl hover:bg-[#fce4e4] transition-colors"
                                    >
                                        <IconTrash />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Modal eliminar ─────────────────────────────────────── */}
                {confirmEliminar && (
                    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm" style={{ fontFamily: "'Manrope', sans-serif" }}>
                            <div className="p-6">
                                <div className="w-12 h-12 rounded-full bg-[#ffebee] flex items-center justify-center mx-auto mb-4">
                                    <IconTrash />
                                </div>
                                <p className="text-[16px] font-bold text-[#191c1d] text-center mb-1">
                                    ¿Eliminar rúbrica?
                                </p>
                                <p className="text-[13px] text-[#6b7b83] text-center">
                                    Se eliminará <strong className="text-[#191c1d]">"{confirmEliminar.nombre}"</strong> y todos sus criterios. Esta acción no se puede deshacer.
                                </p>
                                {errorEliminar && (
                                    <div className="mt-4 px-4 py-3 bg-[#ffebee] border border-[#ef9a9a] rounded-xl text-[13px] text-[#c62828]">
                                        {errorEliminar}
                                    </div>
                                )}
                            </div>
                            <div className="flex gap-2 px-6 pb-6">
                                <button
                                    onClick={() => setConfirmEliminar(null)}
                                    disabled={eliminando}
                                    className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[13px] hover:bg-[#f0f2f3] transition-colors disabled:opacity-50"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={ejecutarEliminar}
                                    disabled={eliminando}
                                    className="flex-1 h-11 rounded-xl bg-[#ba1a1a] text-white font-bold text-[13px] hover:bg-[#930014] transition-colors disabled:opacity-50"
                                >
                                    {eliminando ? 'Eliminando...' : 'Eliminar'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        )
    }

    // ── Vista: Detalle ────────────────────────────────────────────────────────

    if (vista === 'detalle' && rubricaVista) {
        const r = rubricaVista
        return (
            <div className="flex-1 overflow-y-auto p-4 sm:p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
                {/* Cabecera */}
                <div className="mb-5">
                    <button
                        onClick={volverALista}
                        className="flex items-center gap-1.5 text-[12px] font-semibold text-[#9ba7ae] hover:text-[#4c616c] transition-colors mb-3"
                    >
                        <IconBack />
                        Rúbricas
                    </button>
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight leading-tight">{r.nombre}</h1>
                            {r.descripcion && (
                                <p className="text-[13px] text-[#6b7b83] mt-1">{r.descripcion}</p>
                            )}
                            <div className="flex items-center gap-3 mt-2 flex-wrap">
                                <span className="text-[11px] font-semibold text-[#9ba7ae] bg-[#f0f2f3] px-2 py-0.5 rounded-lg">
                                    {(r.criterios ?? []).length} criterio{(r.criterios ?? []).length !== 1 ? 's' : ''}
                                </span>
                                {r.tipo && (
                                    <span className="text-[11px] font-semibold text-[#1565c0] bg-[#e3f2fd] px-2 py-0.5 rounded-lg capitalize">
                                        {r.tipo_display ?? r.tipo}
                                    </span>
                                )}
                            </div>
                        </div>
                        <button
                            onClick={() => editarRubrica(r)}
                            className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2.5 text-[13px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors"
                        >
                            <IconEdit />
                            Editar
                        </button>
                    </div>
                </div>

                {/* Criterios */}
                <div className="flex flex-col gap-4">
                    {(r.criterios ?? []).map((c, idx) => (
                        <div key={c.id ?? idx} className="bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden">
                            <div className="px-5 py-3.5 border-b border-[#f0f2f3] bg-[#fafafa]">
                                <p className="text-[14px] font-bold text-[#191c1d]">{c.nombre}</p>
                                {c.descripcion && (
                                    <p className="text-[12px] text-[#6b7b83] mt-0.5">{c.descripcion}</p>
                                )}
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full min-w-[500px]">
                                    <thead>
                                        <tr className="border-b border-[#f0f2f3]">
                                            {NIVELES.map(n => (
                                                <th key={n.key} className="px-4 py-2.5 text-left text-[11px] font-bold uppercase tracking-[0.6px]" style={{ color: n.color }}>
                                                    {n.label}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            {NIVELES.map(n => {
                                                const nv = (c.niveles ?? []).find(v => v.etiqueta === n.etiqueta)
                                                return (
                                                    <td key={n.key} className="px-4 py-3 align-top">
                                                        <p className="text-[12px] text-[#4c616c] leading-snug">
                                                            {nv?.descripcion || <span className="text-[#c4cdd2] italic">Sin descriptor</span>}
                                                        </p>
                                                        <span
                                                            className="inline-block mt-2 text-[11px] font-bold px-2 py-0.5 rounded-lg"
                                                            style={{ color: n.color, backgroundColor: n.bg }}
                                                        >
                                                            {nv?.puntos ?? 0} pts
                                                        </span>
                                                    </td>
                                                )
                                            })}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    // ── Vista: Editor ─────────────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <div className="flex gap-6 p-4 sm:p-6 min-h-full items-start">

                {/* Columna principal */}
                <div className="flex-1 min-w-0 flex flex-col gap-5">

                    {/* Cabecera */}
                    <div>
                        <button
                            onClick={volverALista}
                            className="flex items-center gap-1.5 text-[12px] font-semibold text-[#9ba7ae] hover:text-[#4c616c] transition-colors mb-2"
                        >
                            <IconBack />
                            Rúbricas
                        </button>
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <p className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae] mb-1">
                                    {editando.id ? 'Editando rúbrica' : 'Nueva rúbrica'}
                                </p>
                                <h1 className="text-[22px] font-extrabold text-[#191c1d] tracking-tight leading-tight">
                                    {editando.nombre || (
                                        <span className="text-[#9ba7ae] font-normal text-[18px]">Sin título</span>
                                    )}
                                </h1>
                            </div>
                            <button
                                onClick={guardar}
                                disabled={!formValida || saving}
                                className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 bg-[#d32f2f] text-white text-[13px] font-semibold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                            >
                                <IconSave />
                                {saving ? 'Guardando...' : 'Guardar Rúbrica'}
                            </button>
                        </div>
                    </div>

                    {saveError && (
                        <div className="bg-[#ffebee] border border-[#ef9a9a] text-[#c62828] text-[13px] rounded-xl px-4 py-3">
                            {saveError}
                        </div>
                    )}

                    {/* Datos básicos */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-5 flex flex-col gap-4">
                        <div>
                            <label className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#6b7b83] block mb-1.5">
                                Nombre de la rúbrica *
                            </label>
                            <input
                                type="text"
                                placeholder="Ej: Análisis de Metodología Cuantitativa"
                                value={editando.nombre}
                                onChange={e => setCampo('nombre', e.target.value)}
                                className={`w-full px-3.5 py-2.5 text-[14px] text-[#191c1d] bg-[#f8f9fa] border rounded-xl focus:outline-none focus:bg-white transition-colors placeholder-[#c4cdd2] ${
                                    editando.nombre === '' ? 'border-[#ef9a9a] focus:border-[#d32f2f]' : 'border-[#e1e3e4] focus:border-[#d32f2f]'
                                }`}
                            />
                            {editando.nombre === '' && (
                                <p className="text-[11px] text-[#c62828] mt-1">El nombre de la rúbrica es obligatorio.</p>
                            )}
                        </div>
                        <div>
                            <label className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#6b7b83] block mb-1.5">
                                Descripción
                            </label>
                            <textarea
                                placeholder="Detalle el propósito de esta rúbrica..."
                                value={editando.descripcion}
                                onChange={e => setCampo('descripcion', e.target.value)}
                                rows={2}
                                className="w-full px-3.5 py-2.5 text-[14px] text-[#191c1d] bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors placeholder-[#c4cdd2] resize-none"
                            />
                        </div>
                    </div>

                    {/* Matriz */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl overflow-hidden">
                        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#e1e3e4]">
                            <h2 className="text-[14px] font-bold text-[#191c1d]">Matriz de Evaluación</h2>
                            <button
                                onClick={addCriterio}
                                className="flex items-center gap-1.5 text-[13px] font-semibold text-[#d32f2f] hover:text-[#b71c1c] transition-colors"
                            >
                                <IconPlus />
                                Añadir Criterio
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full min-w-[700px]">
                                <thead>
                                    <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] w-[160px]">
                                            Criterio
                                        </th>
                                        {NIVELES.map(n => (
                                            <th key={n.key} className="text-left px-3 py-3 text-[11px] font-bold uppercase tracking-[0.6px]" style={{ color: n.color }}>
                                                {n.label}
                                            </th>
                                        ))}
                                        <th className="w-10" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {editando.criterios.map((c) => (
                                        <Fragment key={c.id}>
                                        <tr className="border-b border-[#f0f2f3]">
                                            {/* Nombre del criterio */}
                                            <td className="px-4 py-3 align-top">
                                                <input
                                                    type="text"
                                                    placeholder="Nombre del criterio"
                                                    value={c.nombre}
                                                    onChange={e => updateCriterio(c.id, 'nombre', e.target.value)}
                                                    className={`w-full text-[13px] font-semibold text-[#191c1d] bg-transparent border-0 border-b focus:outline-none pb-1 placeholder-[#c4cdd2] ${
                                                        c.nombre === '' ? 'border-[#ef9a9a] focus:border-[#d32f2f]' : 'border-[#e1e3e4] focus:border-[#d32f2f]'
                                                    }`}
                                                />
                                                {c.nombre === '' && (
                                                    <p className="text-[10px] text-[#c62828] mt-1">Campo obligatorio</p>
                                                )}
                                            </td>

                                            {/* Descriptor + puntos por nivel */}
                                            {NIVELES.map(n => (
                                                <td key={n.key} className="px-3 py-3 align-top">
                                                    <textarea
                                                        rows={3}
                                                        placeholder={`Descriptor ${n.label.toLowerCase()}...`}
                                                        value={c.niveles[n.key].descripcion}
                                                        onChange={e => updateCriterio(c.id, `nivel_${n.key}_desc`, e.target.value)}
                                                        className="w-full text-[12px] text-[#4c616c] bg-[#f8f9fa] border border-[#e1e3e4] rounded-lg px-2.5 py-2 focus:outline-none focus:border-[#d32f2f] focus:bg-white resize-none transition-colors placeholder-[#c4cdd2]"
                                                    />
                                                    <div className="flex items-center gap-1 mt-1.5">
                                                        <span className="text-[10px] text-[#9ba7ae] font-semibold">Pts:</span>
                                                        <input
                                                            type="number"
                                                            min="0"
                                                            step="0.5"
                                                            value={c.niveles[n.key].puntos}
                                                            onChange={e => updateCriterio(c.id, `nivel_${n.key}_pts`, e.target.value)}
                                                            className="w-14 text-[12px] font-bold bg-transparent border-b focus:outline-none text-center"
                                                            style={{ borderColor: n.color + '55', color: n.color }}
                                                        />
                                                    </div>
                                                </td>
                                            ))}

                                            {/* Eliminar fila */}
                                            <td className="px-2 py-3 align-top">
                                                <button
                                                    onClick={() => removeCriterio(c.id)}
                                                    disabled={editando.criterios.length === 1}
                                                    className="w-7 h-7 flex items-center justify-center text-[#9ba7ae] hover:text-[#ba1a1a] hover:bg-[#fff1f0] rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                                                >
                                                    <IconTrash />
                                                </button>
                                            </td>
                                        </tr>
                                        {c.nombre !== '' && !jerarquiaValida(c) && (
                                            <tr>
                                                <td colSpan={6} className="px-4 pb-3 pt-0">
                                                    <div className="flex items-center gap-2 bg-[#fff3e0] border border-[#ffe0b2] rounded-xl px-3 py-2">
                                                        <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5 text-[#e65100] flex-shrink-0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                                                            <path d="M10 3L2 17h16L10 3z" /><path d="M10 9v4M10 15h.01" />
                                                        </svg>
                                                        <p className="text-[11px] font-semibold text-[#e65100]">
                                                            Los puntos deben ir en orden creciente: Insuficiente &lt; Básico &lt; Satisfactorio &lt; Excelente
                                                        </p>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                        </Fragment>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Panel lateral */}
                <div className="w-[220px] flex-shrink-0 flex flex-col gap-4 sticky top-0">
                    <div className={`rounded-2xl p-4 border ${sumaValida ? 'bg-[#f1f8e9] border-[#c8e6c9]' : sumaExcelente > 100 ? 'bg-[#ffebee] border-[#ef9a9a]' : 'bg-white border-[#e1e3e4]'}`}>
                        <p className="text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] mb-3">
                            Total de Criterios
                        </p>
                        <p className="text-[32px] font-extrabold text-[#191c1d] leading-none">
                            {editando.criterios.length}
                        </p>

                        <p className="text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] mt-3 mb-1">
                            Suma Excelente
                        </p>
                        <div className="flex items-end gap-1">
                            <span
                                className="text-[28px] font-extrabold leading-none"
                                style={{ color: sumaValida ? '#2e7d32' : sumaExcelente > 100 ? '#c62828' : '#d32f2f' }}
                            >
                                {sumaExcelente.toFixed(sumaExcelente % 1 === 0 ? 0 : 1)}
                            </span>
                            <span className="text-[16px] font-bold text-[#9ba7ae] mb-0.5">/ 100</span>
                        </div>

                        <div className="mt-2 h-2 bg-[#e1e3e4] rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-300"
                                style={{
                                    width: `${Math.min(sumaExcelente, 100)}%`,
                                    backgroundColor: sumaValida ? '#4caf50' : sumaExcelente > 100 ? '#c62828' : '#d32f2f',
                                }}
                            />
                        </div>

                        <p className="text-[11px] mt-2" style={{ color: sumaValida ? '#2e7d32' : sumaExcelente > 100 ? '#c62828' : '#6b7b83' }}>
                            {sumaValida
                                ? '✓ Suma de excelente = 100 pts'
                                : sumaExcelente > 100
                                    ? `Excede en ${(sumaExcelente - 100).toFixed(1)} pts`
                                    : `Faltan ${(100 - sumaExcelente).toFixed(1)} pts`
                            }
                        </p>

                        <button
                            onClick={guardar}
                            disabled={!formValida || saving}
                            className="mt-4 w-full py-2.5 bg-[#d32f2f] text-white text-[13px] font-bold rounded-xl hover:bg-[#b71c1c] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {saving ? 'Guardando...' : editando.id ? 'Actualizar Rúbrica' : 'Publicar Rúbrica'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}