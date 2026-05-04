import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { equiposApi, proyectosApi } from '../../services/docenteApi'

const AVATAR_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#0097a7', '#5d4037', '#37474f']
const TEAM_COLORS   = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f', '#0097a7']
const NOMBRES_MES   = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const ESTADOS = [
    { key: 'pendiente',   label: 'Pendiente',   bg: 'bg-[#f0f2f3]', text: 'text-[#4c616c]', dot: 'bg-[#9ba7ae]', bar: '#c8d0d3' },
    { key: 'en_progreso', label: 'En progreso', bg: 'bg-[#e3f2fd]', text: 'text-[#1565c0]', dot: 'bg-[#1976d2]', bar: '#1976d2' },
    { key: 'completado',  label: 'Completado',  bg: 'bg-[#e8f5e9]', text: 'text-[#2e7d32]', dot: 'bg-[#388e3c]', bar: '#388e3c' },
    { key: 'vencido',     label: 'Vencido',     bg: 'bg-[#ffdad6]', text: 'text-[#ba1a1a]', dot: 'bg-[#d32f2f]', bar: '#d32f2f' },
]

const FORM_VACIO = { nombre: '', descripcion: '', fecha_inicio: '', fecha_fin: '', responsable: '', estado: 'pendiente' }

function estadoInfo(key) {
    return ESTADOS.find(e => e.key === key) ?? ESTADOS[0]
}

function generarMeses(inicio, cantidad = 6) {
    const lista = []
    let año = inicio.getFullYear()
    let mes  = inicio.getMonth()
    for (let i = 0; i < cantidad; i++) {
        lista.push({ label: NOMBRES_MES[mes], short: NOMBRES_MES[mes].slice(0, 3), mes, año })
        if (++mes > 11) { mes = 0; año++ }
    }
    return lista
}

function formatFecha(iso) {
    if (!iso) return '—'
    return new Date(iso + 'T00:00:00').toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
}

function IconLeft()  { return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5"/></svg> }
function IconRight() { return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5"/></svg> }
function IconPlus()  { return <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M8 3v10M3 8h10"/></svg> }
function IconX()     { return <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg> }
function IconTrash() { return <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M2 4h12M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1M6 7v5M10 7v5M3 4l1 9a1 1 0 001 1h6a1 1 0 001-1l1-9"/></svg> }

function ModalCrearHito({ miembros, onGuardar, onCancelar }) {
    const [form, setForm]       = useState(FORM_VACIO)
    const [errores, setErrores] = useState({})

    function set(campo, valor) {
        setForm(f => ({ ...f, [campo]: valor }))
        setErrores(e => ({ ...e, [campo]: '' }))
    }

    function validar() {
        const e = {}
        if (!form.nombre.trim()) e.nombre = 'El nombre del hito es obligatorio.'
        else if (form.nombre.trim().length < 3) e.nombre = 'El nombre debe tener al menos 3 caracteres.'
        if (!form.fecha_inicio) e.fecha_inicio = 'La fecha de inicio es obligatoria.'
        if (!form.fecha_fin) e.fecha_fin = 'La fecha de fin es obligatoria.'
        else if (form.fecha_inicio && form.fecha_fin <= form.fecha_inicio) e.fecha_fin = 'La fecha de fin debe ser posterior a la de inicio.'
        return e
    }

    function handleGuardar() {
        const e = validar()
        if (Object.keys(e).length) { setErrores(e); return }
        onGuardar({
            id: Date.now(),
            nombre: form.nombre.trim(),
            descripcion: form.descripcion.trim(),
            fecha_inicio: form.fecha_inicio,
            fecha_fin: form.fecha_fin,
            responsable: form.responsable || null,
            estado: form.estado,
        })
    }

    const campo = 'h-11 px-4 rounded-xl border-2 text-[14px] outline-none transition-all'
    const ok    = `${campo} border-[#e1e3e4] focus:border-[#d32f2f] bg-white`
    const err   = `${campo} border-[#ba1a1a] bg-[#fff8f7]`

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={onCancelar}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="flex items-start justify-between p-6 border-b border-[#e1e3e4]">
                    <div><h2 className="text-[18px] font-bold text-[#191c1d]">Nuevo hito</h2><p className="text-[13px] text-[#9ba7ae] mt-0.5">Define un hito para el cronograma</p></div>
                    <button onClick={onCancelar} className="w-8 h-8 rounded-xl text-[#9ba7ae] hover:bg-[#f0f2f3] flex items-center justify-center transition-colors"><IconX /></button>
                </div>
                <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto">
                    <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Nombre del hito <span className="text-[#d32f2f]">*</span></label>
                        <input type="text" value={form.nombre} onChange={e => set('nombre', e.target.value)} placeholder="Ej: Entrega del diseño" className={errores.nombre ? err : ok} />
                        {errores.nombre && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.nombre}</p>}
                    </div>
                    <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Descripción <span className="text-[#9ba7ae] font-normal">(opcional)</span></label>
                        <textarea value={form.descripcion} onChange={e => set('descripcion', e.target.value)} placeholder="Describe el alcance..." rows={3} className="px-4 py-3 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] transition-all resize-none" />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Fecha inicio <span className="text-[#d32f2f]">*</span></label>
                            <input type="date" value={form.fecha_inicio} onChange={e => set('fecha_inicio', e.target.value)} className={errores.fecha_inicio ? err : ok} />
                            {errores.fecha_inicio && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.fecha_inicio}</p>}
                        </div>
                        <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Fecha fin <span className="text-[#d32f2f]">*</span></label>
                            <input type="date" value={form.fecha_fin} min={form.fecha_inicio || undefined} onChange={e => set('fecha_fin', e.target.value)} className={errores.fecha_fin ? err : ok} />
                            {errores.fecha_fin && <p className="text-[12px] text-[#ba1a1a] pl-1">{errores.fecha_fin}</p>}
                        </div>
                    </div>
                    {form.fecha_inicio && form.fecha_fin && form.fecha_fin <= form.fecha_inicio && !errores.fecha_fin && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-[#fff8f7] border border-[#ffdad6] rounded-xl text-[12px] text-[#ba1a1a]"><svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 5v3M8 10.5v.5"/></svg>La fecha de fin debe ser posterior a la de inicio.</div>
                    )}
                    <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Responsable <span className="text-[#9ba7ae] font-normal">(opcional)</span></label>
                        <select value={form.responsable} onChange={e => set('responsable', e.target.value)} className="h-11 px-4 rounded-xl border-2 border-[#e1e3e4] text-[14px] outline-none focus:border-[#d32f2f] bg-white transition-all">
                            <option value="">Sin responsable</option>
                            {miembros.map(m => <option key={m.id} value={m.usuario_id}>{m.nombre_completo}</option>)}
                        </select>
                    </div>
                    <div className="flex flex-col gap-1.5"><label className="text-[13px] font-semibold text-[#191c1d] pl-1">Estado inicial</label>
                        <div className="flex flex-wrap gap-2">
                            {ESTADOS.map(est => (
                                <button key={est.key} type="button" onClick={() => set('estado', est.key)}
                                    className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border-2 text-[13px] font-semibold transition-all ${form.estado === est.key ? `${est.bg} ${est.text} border-current` : 'border-[#e1e3e4] text-[#4c616c] hover:bg-[#f8f9fa]'}`}>
                                    <span className={`w-2 h-2 rounded-full ${est.dot}`} />{est.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
                <div className="flex gap-2 p-4 bg-[#f8f9fa] border-t border-[#e1e3e4]">
                    <button onClick={onCancelar} className="flex-1 h-11 rounded-xl border-2 border-[#e1e3e4] text-[#4c616c] font-semibold text-[14px] hover:bg-white transition-colors">Cancelar</button>
                    <button onClick={handleGuardar} className="flex-1 h-11 rounded-xl bg-[#d32f2f] text-white font-semibold text-[14px] hover:bg-[#af101a] transition-colors flex items-center justify-center gap-2"><IconPlus /> Crear hito</button>
                </div>
            </div>
        </div>
    )
}

function FilaHito({ hito, meses, onEliminar }) {
    const info    = estadoInfo(hito.estado)
    const start   = new Date(hito.fecha_inicio + 'T00:00:00')
    const end     = new Date(hito.fecha_fin + 'T00:00:00')
    return (
        <div className="flex border-b border-[#f0f2f3] last:border-0 hover:bg-[#fafbfc] transition-colors group">
            <div className="w-52 flex-shrink-0 px-4 py-3 border-r border-[#e1e3e4]">
                <div className="flex items-start justify-between gap-1"><p className="text-[13px] font-semibold text-[#191c1d] truncate leading-tight">{hito.nombre}</p>
                    <button onClick={() => onEliminar(hito.id)} className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-lg text-[#9ba7ae] hover:text-[#ba1a1a] hover:bg-[#ffdad6] flex items-center justify-center transition-all flex-shrink-0"><IconTrash /></button>
                </div>
                <p className="text-[11px] text-[#9ba7ae] mt-0.5 leading-tight">{formatFecha(hito.fecha_inicio)} — {formatFecha(hito.fecha_fin)}</p>
                <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold mt-1 ${info.bg} ${info.text}`}><span className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />{info.label}</span>
            </div>
            <div className="flex-1 flex min-w-0">
                {meses.map((m, i) => {
                    const mesStart = new Date(m.año, m.mes, 1), mesEnd = new Date(m.año, m.mes + 1, 0)
                    const overlap = start <= mesEnd && end >= mesStart
                    if (!overlap) return <div key={i} className="flex-1 border-r border-[#f0f2f3] last:border-0" />
                    const diasMes = mesEnd.getDate(), diaStart = start > mesStart ? start.getDate() - 1 : 0, diaEnd = end < mesEnd ? end.getDate() : diasMes
                    const leftPct = (diaStart / diasMes) * 100, widthPct = ((diaEnd - diaStart) / diasMes) * 100
                    return (
                        <div key={i} className="flex-1 border-r border-[#f0f2f3] last:border-0 relative py-4 px-1">
                            <div title={hito.nombre} style={{ left: `${leftPct}%`, width: `${widthPct}%`, backgroundColor: info.bar, opacity: 0.85 }} className="absolute top-1/2 -translate-y-1/2 h-5 rounded-md min-w-[4px]" />
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

function FilaPlaceholder({ meses, altPattern }) {
    return (
        <div className="flex border-b border-[#f0f2f3] last:border-0 opacity-30 pointer-events-none">
            <div className="w-52 flex-shrink-0 px-4 py-3 border-r border-[#e1e3e4]"><div className="h-3 w-28 bg-[#e1e3e4] rounded-full" /><div className="h-2 w-20 bg-[#f0f2f3] rounded-full mt-2" /></div>
            <div className="flex-1 flex">{meses.map((_, i) => (
                <div key={i} className="flex-1 border-r border-[#f0f2f3] last:border-0 relative py-4 px-1">
                    {((altPattern ? i === 2 : i === 1) || (altPattern ? i === 4 : i === 3)) && <div className="absolute top-1/2 -translate-y-1/2 h-5 rounded-md bg-[#e1e3e4]" style={{ left: '5%', width: altPattern ? '80%' : '90%' }} />}
                </div>
            ))}
            </div>
        </div>
    )
}

export default function CronogramaHitos() {
    const { cursoId, proyectoId } = useParams()
    const navigate = useNavigate()
    const [info, setInfo] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [offsetMeses, setOffsetMeses] = useState(0)
    const [modalAbierto, setModalAbierto] = useState(false)
    const [hitos, setHitos] = useState([])

    useEffect(() => {
        cargarTodo()
    }, [proyectoId])

    async function cargarTodo() {
        setLoading(true); setError(null)
        try {
            const [infoRes, hitosRes] = await Promise.all([
                equiposApi.obtenerPorProyecto(proyectoId),
                proyectosApi.listarHitos(proyectoId),
            ])
            setInfo({ proyecto: infoRes.proyecto, curso: infoRes.curso, equipo: infoRes.equipos?.[0] ?? null })
            setHitos(hitosRes)
        } catch {
            setError('No se pudo cargar la información del proyecto.')
        } finally {
            setLoading(false)
        }
    }

    async function agregarHito(hito) {
        setModalAbierto(false)
        try {
            await proyectosApi.crearHito(proyectoId, hito)
            await cargarTodo()
        } catch (err) {
            setError(err?.data?.detail ?? 'Error al crear el hito.')
            setModalAbierto(true)
        }
    }

    async function eliminarHito(id) {
        if (!window.confirm('¿Eliminar este hito?')) return
        try {
            await proyectosApi.eliminarHito(id)
            setHitos(prev => prev.filter(h => h.id !== id))
        } catch (err) {
            setError(err?.data?.detail ?? 'Error al eliminar el hito.')
        }
    }

    const hoy = new Date(), inicio = new Date(hoy.getFullYear(), hoy.getMonth() + offsetMeses, 1), meses = generarMeses(inicio, 6)
    const equipo = info?.equipo, proyecto = info?.proyecto, curso = info?.curso, color = TEAM_COLORS[0], miembros = equipo?.miembros ?? []
    const completados = hitos.filter(h => h.estado === 'completado').length

    if (loading) return <div className="flex-1 flex items-center justify-center"><svg className="w-8 h-8 animate-spin text-[#d32f2f]" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div>

    if (error) return <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-4"><p className="text-[14px] text-[#ba1a1a]">{error}</p><button onClick={cargarTodo} className="h-9 px-4 rounded-xl bg-[#d32f2f] text-white text-[13px] font-semibold hover:bg-[#af101a] transition-colors">Reintentar</button></div>

    return (
        <div className="flex-1 overflow-y-auto p-6" style={{ fontFamily: "'Manrope', sans-serif" }}>
            <div className="mb-4 flex items-center gap-2 text-[13px] flex-wrap">
                <button onClick={() => navigate(-1)} className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors flex items-center gap-1.5"><IconLeft /> Equipos</button>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5"/></svg>
                <span className="text-[#9ba7ae]">{equipo?.nombre ?? proyecto?.nombre ?? 'Equipo'}</span>
                <svg className="w-3 h-3 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 3l5 5-5 5"/></svg>
                <span className="font-semibold text-[#191c1d]">Cronograma de Hitos</span>
                <span className="ml-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#e8f5e9] text-[#2e7d32]">Cronograma</span>
            </div>

            <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 mb-5">
                <div className="flex items-center gap-4 flex-wrap">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-[18px] font-bold flex-shrink-0" style={{ backgroundColor: color }}>{(equipo?.nombre ?? proyecto?.nombre ?? 'E')[0].toUpperCase()}</div>
                    <div className="flex-1 min-w-0"><h1 className="text-[20px] font-bold text-[#191c1d] leading-tight">{equipo?.nombre ?? 'Sin equipo'}</h1><p className="text-[13px] text-[#9ba7ae] mt-0.5">{proyecto?.nombre ?? '—'}{curso?.nombre ? ` · ${curso.nombre}` : ''}</p></div>
                    {miembros.length > 0 && (
                        <div className="flex -space-x-2 flex-shrink-0">
                            {miembros.slice(0, 5).map((m, i) => (
                                <div key={m.id} title={m.nombre_completo} style={{ backgroundColor: AVATAR_COLORS[i % AVATAR_COLORS.length] }} className="w-8 h-8 rounded-full border-2 border-white flex items-center justify-center text-white text-[10px] font-bold">{m.iniciales}</div>
                            ))}
                            {miembros.length > 5 && <div className="w-8 h-8 rounded-full border-2 border-white bg-[#f0f2f3] flex items-center justify-center text-[10px] font-semibold text-[#4c616c]">+{miembros.length - 5}</div>}
                        </div>
                    )}
                    <button onClick={() => setModalAbierto(true)} className="h-10 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors flex items-center gap-2 shadow-sm flex-shrink-0"><IconPlus /> Nuevo hito</button>
                </div>
                <div className="flex items-center gap-5 mt-4 pt-4 border-t border-[#e1e3e4] flex-wrap">
                    <div className="flex items-center gap-1.5 text-[13px] text-[#5b403d]"><svg className="w-4 h-4 text-[#9ba7ae]" viewBox="0 0 16 16" fill="currentColor"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-6 6s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z"/></svg><strong>{miembros.length}</strong> miembro{miembros.length !== 1 ? 's' : ''}</div>
                    <div className="flex items-center gap-1.5 text-[13px] text-[#5b403d]"><svg className="w-4 h-4 text-[#9ba7ae]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="2" y="3" width="12" height="11" rx="1.5"/><path d="M2 6h12M5 2v2M11 2v2"/></svg><strong>{hitos.length}</strong> hito{hitos.length !== 1 ? 's' : ''} definido{hitos.length !== 1 ? 's' : ''}</div>
                    <div className="flex items-center gap-1.5 text-[13px] text-[#5b403d]"><svg className="w-4 h-4 text-[#388e3c]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><strong>{completados}</strong> completado{completados !== 1 ? 's' : ''}</div>
                </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap mb-4">
                {ESTADOS.map(e => (
                    <span key={e.key} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px] font-semibold ${e.bg} ${e.text}`}><span className={`w-2 h-2 rounded-full ${e.dot}`} />{e.label}</span>
                ))}
            </div>

            <div className="bg-white rounded-2xl border border-[#e1e3e4] overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3 border-b border-[#e1e3e4] bg-[#f8f9fa]">
                    <h2 className="text-[14px] font-bold text-[#191c1d]">{meses[0].short} {meses[0].año} — {meses[meses.length - 1].short} {meses[meses.length - 1].año}</h2>
                    <div className="flex items-center gap-1">
                        <button onClick={() => setOffsetMeses(o => o - 1)} className="w-8 h-8 rounded-lg text-[#4c616c] hover:bg-[#e1e3e4] flex items-center justify-center transition-colors"><IconLeft /></button>
                        <button onClick={() => setOffsetMeses(0)} className="h-7 px-3 rounded-lg text-[12px] font-semibold text-[#4c616c] hover:bg-[#e1e3e4] transition-colors">Hoy</button>
                        <button onClick={() => setOffsetMeses(o => o + 1)} className="w-8 h-8 rounded-lg text-[#4c616c] hover:bg-[#e1e3e4] flex items-center justify-center transition-colors"><IconRight /></button>
                    </div>
                </div>
                <div className="flex border-b border-[#e1e3e4]">
                    <div className="w-52 flex-shrink-0 px-4 py-2.5 border-r border-[#e1e3e4]"><p className="text-[11px] font-bold text-[#9ba7ae] uppercase tracking-wide">Hito</p></div>
                    {meses.map((m, i) => {
                        const esHoy = m.mes === hoy.getMonth() && m.año === hoy.getFullYear()
                        return (
                            <div key={i} className={`flex-1 py-2.5 text-center border-r border-[#e1e3e4] last:border-0 ${esHoy ? 'bg-[#fff8f7]' : ''}`}>
                                <p className={`text-[12px] font-bold ${esHoy ? 'text-[#d32f2f]' : 'text-[#4c616c]'}`}>{m.short}</p>
                                <p className={`text-[10px] ${esHoy ? 'text-[#d32f2f]' : 'text-[#9ba7ae]'}`}>{m.año}</p>
                            </div>
                        )
                    })}
                </div>
                <div className="max-h-[500px] overflow-y-auto">
                    {hitos.length > 0 ? (
                        hitos.map(hito => <FilaHito key={hito.id} hito={hito} meses={meses} onEliminar={eliminarHito} />)
                    ) : (
                        <>
                            <FilaPlaceholder meses={meses} altPattern={false} />
                            <FilaPlaceholder meses={meses} altPattern={true} />
                            <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
                                <div className="w-14 h-14 rounded-2xl bg-[#f0f2f3] flex items-center justify-center mb-3"><svg className="w-7 h-7 text-[#9ba7ae]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M3 9h18M9 4v5M15 4v5M8 14h4M8 17h6"/></svg></div>
                                <h3 className="text-[15px] font-bold text-[#191c1d] mb-1">No hay hitos definidos</h3>
                                <p className="text-[13px] text-[#9ba7ae] max-w-xs leading-relaxed mb-4">Crea el primer hito para visualizarlo en el cronograma del equipo.</p>
                                <button onClick={() => setModalAbierto(true)} className="inline-flex items-center gap-2 h-9 px-4 rounded-xl bg-[#d32f2f] text-white font-semibold text-[13px] hover:bg-[#af101a] transition-colors"><IconPlus /> Crear primer hito</button>
                            </div>
                            <FilaPlaceholder meses={meses} altPattern={false} />
                        </>
                    )}
                </div>
            </div>

            {miembros.length > 0 && (
                <div className="mt-5 bg-white rounded-2xl border border-[#e1e3e4] p-5">
                    <h3 className="text-[14px] font-bold text-[#191c1d] mb-3">Miembros del equipo</h3>
                    <div className="flex flex-wrap gap-3">
                        {miembros.map((m, i) => (
                            <div key={m.id} className="flex items-center gap-2.5 px-3 py-2 bg-[#f8f9fa] rounded-xl border border-[#e1e3e4]">
                                <div style={{ backgroundColor: AVATAR_COLORS[i % AVATAR_COLORS.length] }} className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">{m.iniciales}</div>
                                <div><p className="text-[12px] font-semibold text-[#191c1d] leading-tight">{m.nombre_completo}</p>{m.rol_interno && <p className="text-[11px] text-[#9ba7ae] capitalize">{m.rol_interno}</p>}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {modalAbierto && <ModalCrearHito miembros={miembros} onGuardar={agregarHito} onCancelar={() => setModalAbierto(false)} />}
        </div>
    )
}