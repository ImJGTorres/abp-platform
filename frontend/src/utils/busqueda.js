// Utilidades de la búsqueda global (HU-045)

export const GRUPOS_BUSQUEDA = [
    { clave: 'cursos',      titulo: 'Cursos' },
    { clave: 'proyectos',   titulo: 'Proyectos' },
    { clave: 'usuarios',    titulo: 'Usuarios' },
    { clave: 'entregables', titulo: 'Entregables' },
]

// Ruta de la página de resultados según el rol (o la sección en que se está)
export function rutaBusqueda(rol, pathname = '') {
    if (pathname.startsWith('/director')) return '/director/busqueda'
    return rol === 'administrador' ? '/admin/busqueda' : '/director/busqueda'
}

export function mensajeErrorBusqueda(err) {
    if (err?.type === 'network') return 'No hay conexión con el servidor. Revisa tu conexión e intenta de nuevo.'
    if (err?.status === 400 || err?.status === 403) {
        const m = err?.data?.error ?? err?.data?.detail
        if (typeof m === 'string') return m
    }
    return 'No se pudo realizar la búsqueda. Intenta de nuevo.'
}
