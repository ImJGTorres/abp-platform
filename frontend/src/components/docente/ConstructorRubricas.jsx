import { useState, useEffect } from 'react'
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

// ── Constantes — deben coincidir con el backend ───────────────────────────────
// Backend etiquetas: 'insuficiente' | 'basico' | 'satisfactorio' | 'excelente'
// Backend niveles:    1             |    2     |        3         |     4

const NIVELES = [
    { key: 'excelente',     nivel: 4, label: 'Excelente',     etiqueta: 'excelente',     puntosDefault: 100, color: '#2e7d32', bg: '#f1f8e9', pct: '100%' },
    { key: 'satisfactorio', nivel: 3, label: 'Satisfactorio', etiqueta: 'satisfactorio', puntosDefault: 75,  color: '#1565c0', bg: '#e3f2fd', pct: '75%'  },
    { key: 'basico',        nivel: 2, label: 'Básico',        etiqueta: 'basico',        puntosDefault: 50,  color: '#e65100', bg: '#fff3e0', pct: '50%'  },
    { key: 'insuficiente',  nivel: 1, label: 'Insuficiente',  etiqueta: 'insuficiente',  puntosDefault: 0,   color: '#c62828', bg: '#ffebee', pct: '0%'   },
]

function nivelesVacios() {
    return Object.fromEntries(
        NIVELES.map(n => [n.key, { descripcion: '', puntos: n.puntosDefault }])
    )
}

function criterioVacio() {
    return {
        id: crypto.randomUUID(),
        nombre: '',
        peso_porcentual: '',
        niveles: nivelesVacios(),
    }
}

// Normaliza criterios que vienen de la API al formato interno del formulario
function normalizarCriterios(criteriosApi) {
    return (criteriosApi ?? []).map(c => {
        // Construye un mapa por etiqueta para acceso rápido
        const nivelPorEtiqueta = {}
        for (const nv of (c.niveles ?? [])) {
            nivelPorEtiqueta[nv.etiqueta] = { descripcion: nv.descripcion ?? '', puntos: nv.puntos ?? 0 }
        }
        return {
            id: c.id ?? crypto.randomUUID(),
            nombre: c.nombre ?? '',
            peso_porcentual: c.peso_porcentual ?? '',
            niveles: Object.fromEntries(
                NIVELES.map(n => [
                    n.key,
                    nivelPorEtiqueta[n.etiqueta] ?? { descripcion: '', puntos: n.puntosDefault },
                ])
            ),
        }
    })
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ConstructorRubricas() {
    const { proyectoId } = useParams()

    const [rubricas,     setRubricas]     = useState([])
    const [loadingLista, setLoadingLista] = useState(true)
    const [errorLista,   setErrorLista]   = useState(null)

    const [editando,  setEditando]  = useState(null)
    const [saving,    setSaving]    = useState(false)
    const [saveError, setSaveError] = useState(null)

    useEffect(() => {
        cargarRubricas()
    }, [proyectoId])

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

    function nuevaRubrica() {
        setEditando({
            id: null,
            nombre: '',
            descripcion: '',
            criterios: [criterioVacio()],
        })
        setSaveError(null)
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
    }

    async function eliminarRubrica(id) {
        if (!confirm('¿Eliminar esta rúbrica?')) return
        try {
            await rubricasApi.eliminar(id)
            setRubricas(prev => prev.filter(r => r.id !== id))
        } catch {
            alert('No se pudo eliminar la rúbrica.')
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
                // field es 'nombre', 'peso_porcentual', o 'nivel_KEY_desc' / 'nivel_KEY_pts'
                if (field.startsWith('nivel_')) {
                    const [, key, sub] = field.split('_')  // 'nivel', 'excelente', 'desc'|'pts'
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

    const pesoTotal = editando
        ? editando.criterios.reduce((acc, c) => acc + (parseFloat(c.peso_porcentual) || 0), 0)
        : 0

    const pesosValidos = Math.abs(pesoTotal - 100) < 0.01

    const formValida =
        editando?.nombre?.trim() &&
        editando.criterios.length > 0 &&
        editando.criterios.every(c => c.nombre.trim() && c.peso_porcentual !== '') &&
        pesosValidos

    // ── Guardar ───────────────────────────────────────────────────────────────

    async function guardar() {
        if (!formValida) return
        setSaving(true)
        setSaveError(null)
        try {
            const payload = {
                nombre:      editando.nombre.trim(),
                descripcion: editando.descripcion.trim(),
                criterios: editando.criterios.map(c => ({
                    nombre:          c.nombre.trim(),
                    peso_porcentual: parseFloat(c.peso_porcentual),
                    niveles: NIVELES.map(n => ({
                        nivel:       n.nivel,
                        etiqueta:    n.etiqueta,
                        descripcion: c.niveles[n.key].descripcion,
                        puntos:      parseFloat(c.niveles[n.key].puntos) ?? n.puntosDefault,
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
            setEditando(null)
        } catch (e) {
            const detail = e?.data?.detail
                ?? e?.data?.criterios
                ?? e?.data?.nombre?.[0]
                ?? JSON.stringify(e?.data)
                ?? 'No se pudo guardar la rúbrica.'
            setSaveError(typeof detail === 'string' ? detail : JSON.stringify(detail))
        } finally {
            setSaving(false)
        }
    }

    // ── Render: Vista lista ───────────────────────────────────────────────────

    if (!editando) {
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
                                className="bg-white border border-[#e1e3e4] rounded-2xl p-4 flex items-start gap-4 hover:border-[#d32f2f]/30 hover:shadow-sm transition-all"
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
                                <div className="flex items-center gap-2 flex-shrink-0">
                                    <button
                                        onClick={() => editarRubrica(r)}
                                        className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-semibold text-[#4c616c] bg-[#f0f2f3] rounded-xl hover:bg-[#e1e3e4] transition-colors"
                                    >
                                        <IconEdit />
                                        Editar
                                    </button>
                                    <button
                                        onClick={() => eliminarRubrica(r.id)}
                                        className="flex items-center justify-center w-8 h-8 text-[#ba1a1a] bg-[#fff1f0] rounded-xl hover:bg-[#fce4e4] transition-colors"
                                    >
                                        <IconTrash />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        )
    }

    // ── Render: Constructor ───────────────────────────────────────────────────

    return (
        <div className="flex-1 overflow-y-auto" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <div className="flex gap-6 p-4 sm:p-6 min-h-full items-start">

                {/* Columna principal */}
                <div className="flex-1 min-w-0 flex flex-col gap-5">

                    {/* Cabecera del formulario */}
                    <div>
                        <button
                            onClick={() => setEditando(null)}
                            className="flex items-center gap-1.5 text-[12px] font-semibold text-[#9ba7ae] hover:text-[#4c616c] transition-colors mb-2"
                        >
                            <IconBack />
                            Rúbricas
                        </button>
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <p className="text-[11px] font-bold uppercase tracking-[0.8px] text-[#9ba7ae] mb-1">
                                    Nombre de la rúbrica
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
                                className="w-full px-3.5 py-2.5 text-[14px] text-[#191c1d] bg-[#f8f9fa] border border-[#e1e3e4] rounded-xl focus:outline-none focus:border-[#d32f2f] focus:bg-white transition-colors placeholder-[#c4cdd2]"
                            />
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

                    {/* Matriz de evaluación */}
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
                            <table className="w-full min-w-[750px]">
                                <thead>
                                    <tr className="bg-[#f8f9fa] border-b border-[#e1e3e4]">
                                        <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] w-[180px]">
                                            Criterio / Peso %
                                        </th>
                                        {NIVELES.map(n => (
                                            <th key={n.key} className="text-left px-3 py-3 text-[11px] font-bold uppercase tracking-[0.6px]" style={{ color: n.color }}>
                                                {n.label}
                                                <br />
                                                <span className="text-[10px] font-semibold opacity-70">({n.pct})</span>
                                            </th>
                                        ))}
                                        <th className="w-10" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {editando.criterios.map((c) => (
                                        <tr key={c.id} className="border-b border-[#f0f2f3] last:border-0">
                                            {/* Nombre + Peso */}
                                            <td className="px-4 py-3 align-top">
                                                <input
                                                    type="text"
                                                    placeholder="Nombre del criterio"
                                                    value={c.nombre}
                                                    onChange={e => updateCriterio(c.id, 'nombre', e.target.value)}
                                                    className="w-full text-[13px] font-semibold text-[#191c1d] bg-transparent border-0 border-b border-[#e1e3e4] focus:outline-none focus:border-[#d32f2f] pb-1 placeholder-[#c4cdd2] mb-2"
                                                />
                                                <div className="flex items-center gap-1">
                                                    <span className="text-[10px] font-bold text-[#9ba7ae] uppercase">Peso:</span>
                                                    <input
                                                        type="number"
                                                        min="0"
                                                        max="100"
                                                        step="0.01"
                                                        placeholder="0"
                                                        value={c.peso_porcentual}
                                                        onChange={e => updateCriterio(c.id, 'peso_porcentual', e.target.value)}
                                                        className="w-14 text-[13px] font-bold text-[#d32f2f] bg-transparent border-0 border-b border-[#e1e3e4] focus:outline-none focus:border-[#d32f2f] text-center"
                                                    />
                                                    <span className="text-[12px] font-bold text-[#d32f2f]">%</span>
                                                </div>
                                            </td>

                                            {/* Descriptores por nivel */}
                                            {NIVELES.map(n => (
                                                <td key={n.key} className="px-3 py-3 align-top">
                                                    <textarea
                                                        rows={3}
                                                        placeholder={`Descriptor ${n.label.toLowerCase()}...`}
                                                        value={c.niveles[n.key].descripcion}
                                                        onChange={e => updateCriterio(c.id, `nivel_${n.key}_desc`, e.target.value)}
                                                        className="w-full text-[12px] text-[#4c616c] bg-[#f8f9fa] border border-[#e1e3e4] rounded-lg px-2.5 py-2 focus:outline-none focus:border-[#d32f2f] focus:bg-white resize-none transition-colors placeholder-[#c4cdd2]"
                                                    />
                                                    {/* Puntos del nivel */}
                                                    <div className="flex items-center gap-1 mt-1">
                                                        <span className="text-[10px] text-[#9ba7ae]">Pts:</span>
                                                        <input
                                                            type="number"
                                                            min="0"
                                                            step="0.5"
                                                            value={c.niveles[n.key].puntos}
                                                            onChange={e => updateCriterio(c.id, `nivel_${n.key}_pts`, e.target.value)}
                                                            className="w-14 text-[11px] font-semibold bg-transparent border-b border-[#e1e3e4] focus:outline-none focus:border-[#d32f2f] text-center"
                                                            style={{ color: n.color }}
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
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Panel lateral derecho */}
                <div className="w-[220px] flex-shrink-0 flex flex-col gap-4 sticky top-0">

                    {/* Validación de pesos */}
                    <div className={`rounded-2xl p-4 border ${pesosValidos ? 'bg-[#f1f8e9] border-[#c8e6c9]' : pesoTotal > 100 ? 'bg-[#ffebee] border-[#ef9a9a]' : 'bg-white border-[#e1e3e4]'}`}>
                        <p className="text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] mb-3">
                            Total de Criterios
                        </p>
                        <p className="text-[32px] font-extrabold text-[#191c1d] leading-none">
                            {editando.criterios.length}
                        </p>

                        <p className="text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] mt-3 mb-1">
                            Peso Acumulado
                        </p>
                        <div className="flex items-end gap-1">
                            <span
                                className="text-[28px] font-extrabold leading-none"
                                style={{ color: pesosValidos ? '#2e7d32' : pesoTotal > 100 ? '#c62828' : '#d32f2f' }}
                            >
                                {pesoTotal.toFixed(pesoTotal % 1 === 0 ? 0 : 1)}
                            </span>
                            <span className="text-[16px] font-bold text-[#9ba7ae] mb-0.5">%</span>
                        </div>

                        <div className="mt-2 h-2 bg-[#e1e3e4] rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-300"
                                style={{
                                    width: `${Math.min(pesoTotal, 100)}%`,
                                    backgroundColor: pesosValidos ? '#4caf50' : pesoTotal > 100 ? '#c62828' : '#d32f2f',
                                }}
                            />
                        </div>

                        <p className="text-[11px] mt-2" style={{ color: pesosValidos ? '#2e7d32' : pesoTotal > 100 ? '#c62828' : '#6b7b83' }}>
                            {pesosValidos
                                ? '✓ Los pesos suman 100%'
                                : pesoTotal > 100
                                    ? `Excede en ${(pesoTotal - 100).toFixed(1)}%`
                                    : `Faltan ${(100 - pesoTotal).toFixed(1)}%`
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

                    {/* Info de niveles */}
                    <div className="bg-white border border-[#e1e3e4] rounded-2xl p-4">
                        <p className="text-[11px] font-bold uppercase tracking-[0.6px] text-[#6b7b83] mb-3">
                            Niveles de Desempeño
                        </p>
                        <div className="flex flex-col gap-2">
                            {NIVELES.map(n => (
                                <div key={n.key} className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: n.color }} />
                                    <span className="text-[12px] font-semibold" style={{ color: n.color }}>{n.label}</span>
                                    <span className="text-[11px] text-[#9ba7ae] ml-auto">{n.pct}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}