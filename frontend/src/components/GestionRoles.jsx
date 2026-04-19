import { useState, useCallback, useEffect } from 'react'
import { rolesApi } from '../services/api'

// Helpers
const cap = s => s.charAt(0).toUpperCase() + s.slice(1)

function buildPermsMap(todosPermisos, permisosDelRol) {
    const asignadosIds = new Set((permisosDelRol ?? []).map(p => p.id))
    const map = {}
    for (const p of todosPermisos) {
        if (!map[p.modulo]) map[p.modulo] = {}
        const accion = p.codigo.split('.')[1]
        map[p.modulo][accion] = { id: p.id, checked: asignadosIds.has(p.id) }
    }
    return map
}

// Subcomponentes

function Badge({ estado }) {
    const cls = estado === 'activo'
        ? 'bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full font-medium'
        : 'bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full font-medium'
    return <span className={cls}>{estado}</span>
}

function ModalEliminar({ rol, onConfirm, onCancel }) {
    const count = rol.total_usuarios ?? 0
    return (
        <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50" onClick={onCancel}>
            <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-sm w-full mx-4" onClick={e => e.stopPropagation()}>
                <h3 className="font-medium text-base mb-2">Eliminar rol</h3>
                <p className="text-sm text-gray-500 mb-3 leading-relaxed">
                    ¿Estás seguro de que deseas eliminar el rol <strong>{rol.nombre}</strong>? Esta acción no se puede deshacer.
                </p>
                {count > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700 mb-4">
                        Este rol tiene <strong>{count}</strong> usuario{count !== 1 ? 's' : ''} vinculado{count !== 1 ? 's' : ''}.
                        Eliminar el rol desvinculará a todos los usuarios asociados.
                    </div>
                )}
                <div className="flex gap-2 justify-end">
                    <button onClick={onCancel} className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-500 hover:bg-gray-50">
                        Cancelar
                    </button>
                    <button onClick={onConfirm} className="text-xs border border-red-200 rounded-lg px-3 py-1.5 text-red-700 hover:bg-red-50">
                        Eliminar
                    </button>
                </div>
            </div>
        </div>
    )
}

/**
 * Panel de permisos — trabaja con el catálogo real de permisos del backend.
 *
 * permsMap shape: { modulo: { accion: { id, checked } } }
 * Al guardar envía permiso_ids: [id, ...] de los permisos marcados.
 */
function PanelPermisos({ rol, todosPermisos, onClose, onSave, onReset }) {
    const [permsMap, setPermsMap] = useState(() =>
        buildPermsMap(todosPermisos, rol.permisos ?? [])
    )

    // Agrupa los módulos disponibles en el catálogo (orden del seed)
    const modulos = [...new Set(todosPermisos.map(p => p.modulo))]

    const toggle = (modulo, accion) =>
        setPermsMap(prev => ({
            ...prev,
            [modulo]: {
                ...prev[modulo],
                [accion]: { ...prev[modulo][accion], checked: !prev[modulo][accion].checked },
            },
        }))

    const handleSave = () => {
        const permiso_ids = []
        for (const mod of Object.values(permsMap))
            for (const { id, checked } of Object.values(mod))
                if (checked) permiso_ids.push(id)
        onSave(rol.id, permiso_ids)
    }

    const handleReset = () => {
        setPermsMap(buildPermsMap(todosPermisos, []))
        onReset(rol.id)
    }

    return (
        <div className="flex flex-col h-full">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <div>
                    <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-0.5">Configuración</p>
                    <h2 className="text-base font-medium">Configurar permisos</h2>
                </div>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-lg leading-none">×</button>
            </div>

            <div className="mx-6 mt-4 bg-gray-50 rounded-lg px-3 py-2.5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-red-100 text-red-700 flex items-center justify-center text-sm font-medium flex-shrink-0">
                    {rol.nombre[0]}
                </div>
                <div>
                    <p className="text-sm font-medium">Rol seleccionado: {rol.nombre}</p>
                    <p className="text-xs text-gray-400">Personalizando accesos específicos</p>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
                {modulos.map(modulo => {
                    const acciones = permsMap[modulo] ?? {}
                    return (
                        <div key={modulo} className="mb-4">
                            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-2">
                                Módulo: {modulo}
                            </p>
                            <div className="grid grid-cols-2 gap-1.5">
                                {Object.entries(acciones).map(([accion, { checked }]) => (
                                    <label key={accion} className="flex items-center gap-1.5 text-sm cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={checked}
                                            onChange={() => toggle(modulo, accion)}
                                            className="w-3.5 h-3.5 accent-red-700"
                                        />
                                        {cap(accion)}
                                    </label>
                                ))}
                            </div>
                            <hr className="mt-3 border-gray-100" />
                        </div>
                    )
                })}
            </div>

            <div className="px-6 py-4 border-t border-gray-100">
                <button onClick={handleSave} className="w-full bg-gray-900 text-white rounded-lg py-3 text-sm font-medium hover:bg-gray-700 mb-2">
                    Guardar cambios
                </button>
                <button onClick={handleReset} className="w-full text-sm text-gray-400 hover:text-gray-700 py-1.5">
                    Restablecer valores
                </button>
            </div>
        </div>
    )
}

function PanelForm({ rol, onClose, onSave }) {
    const [nombre, setNombre] = useState(rol?.nombre ?? '')
    const [descripcion, setDescripcion] = useState(rol?.descripcion ?? '')
    const [estado, setEstado] = useState(rol?.estado ?? 'activo')
    const [error, setError] = useState('')
    const esEdicion = !!rol

    const handleSubmit = () => {
        if (!nombre.trim()) { setError('El nombre es requerido'); return }
        onSave({ nombre: nombre.trim(), descripcion: descripcion.trim(), ...(esEdicion ? { estado } : {}) })
    }

    return (
        <div className="flex flex-col h-full">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <div>
                    <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-0.5">
                        {esEdicion ? 'Editar rol' : 'Nuevo rol'}
                    </p>
                    <h2 className="text-base font-medium">{esEdicion ? rol.nombre : 'Crear rol'}</h2>
                </div>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-lg leading-none">×</button>
            </div>

            <div className="flex-1 px-6 py-4 overflow-y-auto">
                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Nombre del rol</label>
                    <input
                        type="text" maxLength={100} value={nombre}
                        onChange={e => { setNombre(e.target.value); setError('') }}
                        placeholder="Ej: Director académico"
                        className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-700 ${error ? 'border-red-400' : 'border-gray-200'}`}
                    />
                    {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
                </div>
                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Descripción operativa</label>
                    <textarea
                        rows={3} value={descripcion}
                        onChange={e => setDescripcion(e.target.value)}
                        placeholder="Describe las responsabilidades de este rol..."
                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-red-700"
                    />
                </div>
                {esEdicion && (
                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
                        <select value={estado} onChange={e => setEstado(e.target.value)}
                            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-700">
                            <option value="activo">Activo</option>
                            <option value="inactivo">Inactivo</option>
                        </select>
                    </div>
                )}
            </div>

            <div className="px-6 py-4 border-t border-gray-100">
                <button onClick={handleSubmit} className="w-full bg-gray-900 text-white rounded-lg py-3 text-sm font-medium hover:bg-gray-700 mb-2">
                    {esEdicion ? 'Guardar cambios' : 'Crear rol'}
                </button>
                <button onClick={onClose} className="w-full text-sm text-gray-400 hover:text-gray-700 py-1.5">
                    Cancelar
                </button>
            </div>
        </div>
    )
}

// Componente principal
export default function GestionRoles() {
    const [roles, setRoles] = useState([])
    const [todosPermisos, setTodosPermisos] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [panel, setPanel] = useState(null)        // null | { mode: 'permisos'|'editar'|'crear', rolId? }
    const [deleteTarget, setDeleteTarget] = useState(null)
    const [toast, setToast] = useState('')

    const showToast = msg => {
        setToast(msg)
        setTimeout(() => setToast(''), 2500)
    }

    // Rol seleccionado en panel — incluye permisos completos si ya los cargamos
    const selectedRol = panel?.rolId ? roles.find(r => r.id === panel.rolId) : null

    // Carga inicial: roles + catálogo de permisos en paralelo
    useEffect(() => {
        Promise.all([rolesApi.listar(), rolesApi.listarPermisos()])
            .then(([rolesData, permisosData]) => {
                setRoles(rolesData)
                setTodosPermisos(permisosData)
            })
            .catch(() => setError('No se pudieron cargar los datos. Verifica tu conexión.'))
            .finally(() => setLoading(false))
    }, [])

    // Al abrir el panel de permisos, carga el detalle del rol (incluye permisos anidados)
    const openPermisos = useCallback(async (id) => {
        setPanel({ mode: 'permisos', rolId: id })
        try {
            const detalle = await rolesApi.obtener(id)
            setRoles(prev => prev.map(r => r.id === id ? { ...r, permisos: detalle.permisos } : r))
        } catch {
            showToast('No se pudieron cargar los permisos del rol')
        }
    }, [])

    // Handlers CRUD

    const handleCreate = useCallback(async ({ nombre, descripcion }) => {
        try {
            const nuevo = await rolesApi.crear({ nombre, descripcion })
            setRoles(prev => [...prev, { ...nuevo, total_usuarios: 0 }])
            setPanel(null)
            showToast('Rol creado exitosamente')
        } catch (err) {
            const msg = err?.data?.nombre?.[0] ?? 'Error al crear el rol'
            showToast(msg)
        }
    }, [])

    const handleEdit = useCallback(async (id, campos) => {
        try {
            const actualizado = await rolesApi.editar(id, campos)
            setRoles(prev => prev.map(r => r.id === id ? { ...r, ...actualizado } : r))
            setPanel(null)
            showToast('Rol actualizado correctamente')
        } catch (err) {
            const msg = err?.data?.nombre?.[0] ?? 'Error al actualizar el rol'
            showToast(msg)
        }
    }, [])

    const handleDelete = useCallback(async () => {
        try {
            await rolesApi.eliminar(deleteTarget)
            setRoles(prev => prev.filter(r => r.id !== deleteTarget))
            if (panel?.rolId === deleteTarget) setPanel(null)
            setDeleteTarget(null)
            showToast('Rol eliminado')
        } catch {
            showToast('Error al eliminar el rol')
            setDeleteTarget(null)
        }
    }, [deleteTarget, panel])

    /**
     * Guarda permisos — recibe permiso_ids: [id, ...] desde PanelPermisos
     * Usa PATCH con permiso_ids, el serializer reemplaza todos los permisos del rol.
     */
    const handleSavePerms = useCallback(async (id, permiso_ids) => {
        try {
            const actualizado = await rolesApi.editar(id, { permiso_ids })
            setRoles(prev => prev.map(r => r.id === id ? { ...r, permisos: actualizado.permisos } : r))
            showToast('Permisos guardados correctamente')
        } catch {
            showToast('Error al guardar permisos')
        }
    }, [])

    const handleResetPerms = useCallback(async (id) => {
        try {
            const actualizado = await rolesApi.editar(id, { permiso_ids: [] })
            setRoles(prev => prev.map(r => r.id === id ? { ...r, permisos: actualizado.permisos } : r))
            showToast('Permisos restablecidos')
        } catch {
            showToast('Error al restablecer permisos')
        }
    }, [])

    // Renderizado

    return (
        <div className="flex h-screen bg-gray-50 relative">

            {/* Tabla principal */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="flex justify-between items-start mb-8">
                    <div>
                        <h1 className="text-2xl font-medium mb-1">Gestión de roles</h1>
                        <p className="text-sm text-gray-500">Define las capacidades y accesos para los colaboradores del entorno editorial.</p>
                    </div>
                    <button
                        onClick={() => setPanel({ mode: 'crear' })}
                        className="bg-red-700 hover:bg-red-800 text-white text-sm font-medium px-4 py-2.5 rounded-lg flex items-center gap-1.5"
                    >
                        + Nuevo rol
                    </button>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
                )}

                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                    {loading && (
                        <div className="px-4 py-8 text-center text-sm text-gray-400">Cargando roles...</div>
                    )}
                    <table className="w-full" style={{ display: loading ? 'none' : undefined }}>
                        <thead>
                            <tr className="border-b border-gray-100">
                                <th className="text-left text-[10px] font-medium text-gray-400 uppercase tracking-widest px-4 py-3">Identificador del rol</th>
                                <th className="text-left text-[10px] font-medium text-gray-400 uppercase tracking-widest px-4 py-3">Descripción operativa</th>
                                <th className="text-left text-[10px] font-medium text-gray-400 uppercase tracking-widest px-4 py-3">Usuarios</th>
                                <th className="text-left text-[10px] font-medium text-gray-400 uppercase tracking-widest px-4 py-3">Estado</th>
                                <th className="px-4 py-3" />
                            </tr>
                        </thead>
                        <tbody>
                            {roles.map((rol, i) => (
                                <tr
                                    key={rol.id}
                                    onClick={() => openPermisos(rol.id)}
                                    className={`cursor-pointer transition-colors ${panel?.rolId === rol.id ? 'bg-gray-50' : 'hover:bg-gray-50'} ${i < roles.length - 1 ? 'border-b border-gray-100' : ''}`}
                                >
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-2">
                                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${rol.estado === 'activo' ? 'bg-green-500' : 'bg-gray-300'}`} />
                                            <span className="font-medium text-sm">{rol.nombre}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 max-w-xs text-sm text-gray-500">{rol.descripcion || '—'}</td>
                                    <td className="px-4 py-4">
                                        {/* total_usuarios viene de RolListSerializer */}
                                        <span className="bg-gray-100 text-gray-600 text-xs px-2.5 py-0.5 rounded-full">
                                            {String(rol.total_usuarios ?? 0).padStart(2, '0')}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4"><Badge estado={rol.estado} /></td>
                                    <td className="px-4 py-4">
                                        <div className="flex gap-2 justify-end">
                                            <button
                                                onClick={e => { e.stopPropagation(); setPanel({ mode: 'editar', rolId: rol.id }) }}
                                                className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-500 hover:bg-gray-50"
                                            >
                                                Editar
                                            </button>
                                            <button
                                                onClick={e => { e.stopPropagation(); setDeleteTarget(rol.id) }}
                                                className="text-xs border border-red-200 rounded-lg px-3 py-1.5 text-red-700 hover:bg-red-50"
                                            >
                                                Eliminar
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Panel lateral */}
            {panel && (
                <div className="w-80 bg-white border-l border-gray-100 flex flex-col overflow-hidden">
                    {panel.mode === 'permisos' && selectedRol && todosPermisos.length > 0 && (
                        <PanelPermisos
                            key={selectedRol.id}
                            rol={selectedRol}
                            todosPermisos={todosPermisos}
                            onClose={() => setPanel(null)}
                            onSave={handleSavePerms}
                            onReset={handleResetPerms}
                        />
                    )}
                    {panel.mode === 'permisos' && (!selectedRol || todosPermisos.length === 0) && (
                        <div className="flex items-center justify-center h-full text-sm text-gray-400">
                            Cargando permisos...
                        </div>
                    )}
                    {panel.mode === 'editar' && selectedRol && (
                        <PanelForm
                            key={`edit-${selectedRol.id}`}
                            rol={selectedRol}
                            onClose={() => setPanel(null)}
                            onSave={campos => handleEdit(selectedRol.id, campos)}
                        />
                    )}
                    {panel.mode === 'crear' && (
                        <PanelForm
                            key="crear"
                            rol={null}
                            onClose={() => setPanel(null)}
                            onSave={handleCreate}
                        />
                    )}
                </div>
            )}

            {/* Modal eliminar */}
            {deleteTarget && (
                <ModalEliminar
                    rol={roles.find(r => r.id === deleteTarget)}
                    onConfirm={handleDelete}
                    onCancel={() => setDeleteTarget(null)}
                />
            )}

            {/* Toast */}
            {toast && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-full z-50 pointer-events-none">
                    {toast}
                </div>
            )}
        </div>
    )
}