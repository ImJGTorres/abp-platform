import { useState, useEffect } from 'react'
import { getMiEquipo, distribucionApi } from '../../services/liderEquipoApi'

const ESTADO_CONFIG = {
    pendiente:   { label: 'Pendiente',   color: 'bg-gray-100 text-gray-600' },
    en_progreso: { label: 'En progreso', color: 'bg-blue-100 text-blue-700' },
    completada:  { label: 'Completada',  color: 'bg-green-100 text-green-700' },
    bloqueada:   { label: 'Bloqueada',   color: 'bg-red-100 text-red-700' },
}

const PRIORIDAD_CONFIG = {
    alta:  { label: 'Alta',  color: 'bg-red-100 text-red-700' },
    media: { label: 'Media', color: 'bg-amber-100 text-amber-700' },
    baja:  { label: 'Baja',  color: 'bg-blue-100 text-blue-700' },
}

function Badge({ config, value }) {
    const cfg = config[value] ?? { label: value, color: 'bg-gray-100 text-gray-600' }
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wide ${cfg.color}`}>
            {cfg.label}
        </span>
    )
}

function Modal({ open, title, children }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[85vh] flex flex-col">
                <div className="px-6 py-4 border-b border-[#e1e3e4] flex-shrink-0">
                    <h3 className="text-[16px] font-bold text-[#191c1d]">{title}</h3>
                </div>
                {children}
            </div>
        </div>
    )
}

export default function AsignarResponsables() {
    const [loading, setLoading] = useState(true)
    const [equipoId, setEquipoId] = useState(null)
    const [actividades, setActividades] = useState([])
    const [miembros, setMiembros] = useState([])
    const [filtroEstado, setFiltroEstado] = useState('')

    // modal
    const [modalAct, setModalAct] = useState(null)
    const [seleccionados, setSeleccionados] = useState([])
    const [guardando, setGuardando] = useState(false)
    const [modalError, setModalError] = useState('')

    useEffect(() => { cargar() }, [])

    async function cargar() {
        setLoading(true)
        try {
            const miEquipo = await getMiEquipo()
            if (!miEquipo) return
            const id = miEquipo.equipo.id
            setEquipoId(id)

            const [progreso, acts] = await Promise.all([
                distribucionApi.obtenerPorEquipo(id),
                distribucionApi.obtenerActividades(id),
            ])
            setMiembros(progreso.miembros || [])
            setActividades(acts)
        } catch {
            // sin equipo
        } finally {
            setLoading(false)
        }
    }

    function abrirModal(actividad) {
        setModalError('')
        setModalAct(actividad)
        setSeleccionados((actividad.responsables || []).map(r => typeof r === 'object' ? r.id : r))
    }

    function cerrarModal() {
        if (guardando) return
        setModalAct(null)
        setSeleccionados([])
        setModalError('')
    }

    function toggleMiembro(id) {
        setSeleccionados(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        )
    }

    async function guardar() {
        setModalError('')
        setGuardando(true)
        try {
            const actualizada = await distribucionApi.asignarResponsable(modalAct.id, seleccionados)
            setActividades(prev => prev.map(a => a.id === actualizada.id ? actualizada : a))
            cerrarModal()
        } catch (err) {
            const detail = err.data?.detail || err.data?.responsables?.[0] || 'Error al guardar.'
            setModalError(detail)
        } finally {
            setGuardando(false)
        }
    }

    function nombreMiembro(uid) {
        if (typeof uid === 'object' && uid !== null) {
            return uid.nombre ?? `Usuario #${uid.id}`
        }
        return miembros.find(m => m.id_usuario === uid)?.nombre ?? `Usuario #${uid}`
    }

    const actividadesFiltradas = filtroEstado
        ? actividades.filter(a => a.estado === filtroEstado)
        : actividades

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-[26px] font-extrabold text-[#191c1d] mb-1">Asignar Responsables</h1>
                <p className="text-[14px] text-[#9ba7ae] mb-6">
                    Asigna uno o más integrantes del equipo como responsables de cada actividad.
                </p>

                {/* Filtro */}
                <div className="mb-4">
                    <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}
                        className="px-3 py-2 border border-[#e1e3e4] rounded-xl text-[13px] bg-white focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20">
                        <option value="">Todos los estados</option>
                        <option value="pendiente">Pendiente</option>
                        <option value="en_progreso">En progreso</option>
                        <option value="completada">Completada</option>
                        <option value="bloqueada">Bloqueada</option>
                    </select>
                </div>

                {loading ? (
                    <div className="text-center py-16 text-[#9ba7ae]">Cargando actividades...</div>
                ) : !equipoId ? (
                    <div className="text-center py-16 text-[#9ba7ae]">No tienes un equipo asignado.</div>
                ) : actividadesFiltradas.length === 0 ? (
                    <div className="text-center py-16 text-[#9ba7ae]">
                        {actividades.length === 0 ? 'No hay actividades en el proyecto.' : 'Sin actividades con ese estado.'}
                    </div>
                ) : (
                    <div className="space-y-2">
                        {actividadesFiltradas.map(a => {
                            const tieneResponsables = a.responsables?.length > 0
                            return (
                                <div key={a.id} className="bg-white border border-[#e1e3e4] rounded-xl p-4 flex items-start gap-4 hover:shadow-sm transition-shadow">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                            <p className="text-[15px] font-bold text-[#191c1d]">{a.nombre}</p>
                                            <Badge config={ESTADO_CONFIG} value={a.estado} />
                                            <Badge config={PRIORIDAD_CONFIG} value={a.prioridad} />
                                        </div>
                                        {a.fecha_limite && (
                                            <p className="text-[12px] text-[#9ba7ae] mb-2">
                                                Fecha límite: {new Date(a.fecha_limite + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                                            </p>
                                        )}
                                        {tieneResponsables ? (
                                            <div className="flex flex-wrap gap-1.5">
                                                {a.responsables.map(uid => {
                                                    const key = typeof uid === 'object' ? uid.id : uid
                                                    return (
                                                        <span key={key} className="inline-flex items-center gap-1.5 px-2 py-1 bg-[#ffdad6] text-[#af101a] rounded-lg text-[11px] font-semibold">
                                                            <span className="w-4 h-4 rounded-full bg-[#af101a] text-white flex items-center justify-center text-[9px] font-bold flex-shrink-0">
                                                                {nombreMiembro(uid)?.[0]?.toUpperCase()}
                                                            </span>
                                                            {nombreMiembro(uid)}
                                                        </span>
                                                    )
                                                })}
                                            </div>
                                        ) : (
                                            <p className="text-[12px] text-[#9ba7ae] italic">Sin responsables asignados</p>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => abrirModal(a)}
                                        className="flex-shrink-0 px-3 py-1.5 border border-[#d32f2f] text-[#d32f2f] rounded-lg text-[12px] font-semibold hover:bg-[#d32f2f] hover:text-white transition-colors">
                                        {tieneResponsables ? 'Editar' : 'Asignar'}
                                    </button>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Modal asignación */}
            <Modal open={!!modalAct} title={`Asignar responsables`}>
                {modalError && (
                    <div className="mx-6 mt-4 px-3 py-2.5 bg-[#fff1f0] border border-[#ffc9c5] rounded-xl text-[13px] text-[#ba1a1a] font-medium flex-shrink-0">
                        {modalError}
                    </div>
                )}
                <div className="px-6 pt-4 pb-2 flex-shrink-0">
                    <p className="text-[13px] font-semibold text-[#191c1d] truncate">{modalAct?.nombre}</p>
                    <p className="text-[12px] text-[#9ba7ae] mt-0.5">
                        {seleccionados.length === 0
                            ? 'Ningún responsable seleccionado'
                            : `${seleccionados.length} responsable${seleccionados.length !== 1 ? 's' : ''} seleccionado${seleccionados.length !== 1 ? 's' : ''}`}
                    </p>
                </div>
                <div className="flex-1 overflow-y-auto px-6 py-2">
                    {miembros.length === 0 ? (
                        <p className="text-[13px] text-[#9ba7ae] text-center py-4">No hay miembros en el equipo.</p>
                    ) : (
                        <div className="border border-[#e1e3e4] rounded-xl divide-y divide-[#e1e3e4]">
                            {miembros.map(m => (
                                <label key={m.id_usuario} className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-[#f8f9fa] transition-colors">
                                    <input
                                        type="checkbox"
                                        checked={seleccionados.includes(m.id_usuario)}
                                        onChange={() => toggleMiembro(m.id_usuario)}
                                        className="w-4 h-4 accent-[#d32f2f] flex-shrink-0"
                                    />
                                    <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center flex-shrink-0">
                                        <span className="text-[12px] font-bold text-[#af101a]">{m.nombre?.[0]?.toUpperCase()}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[13px] font-semibold text-[#191c1d] truncate">{m.nombre}</p>
                                        {m.rol_interno && (
                                            <p className="text-[11px] text-[#9ba7ae] capitalize">{m.rol_interno}</p>
                                        )}
                                    </div>
                                </label>
                            ))}
                        </div>
                    )}
                </div>
                <div className="px-6 py-4 border-t border-[#e1e3e4] flex gap-2 flex-shrink-0">
                    <button onClick={cerrarModal} disabled={guardando}
                        className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        Cancelar
                    </button>
                    <button onClick={guardar} disabled={guardando}
                        className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                        {guardando ? 'Guardando...' : 'Guardar'}
                    </button>
                </div>
            </Modal>
        </div>
    )
}
