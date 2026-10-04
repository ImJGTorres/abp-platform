// ── Menú lateral por rol (HU-038) ─────────────────────────────────────────────
// Ítems fijos de cada rol, en el orden en que se muestran.
// Los ítems que dependen de cursoId/proyectoId los arma cada layout y se pasan a
// <MenuLateral /> como `itemsContextuales`.
//
// Cada ítem: { label, to, icon, exact }
//   icon  → nombre de un ícono definido en Compartidos/MenuLateral.jsx
//   exact → true: activo solo si la URL coincide exactamente; si no, también en subrutas

export const MENU_POR_ROL = {
    administrador: [
        { label: 'Inicio',        to: '/admin',               icon: 'inicio',      exact: true },
        { label: 'Usuarios',      to: '/admin/registro',      icon: 'usuarios' },
        { label: 'Cursos',        to: '/admin/cursos',        icon: 'cursos' },
        { label: 'Períodos',      to: '/admin/periodos',      icon: 'calendario' },
        { label: 'Configuración', to: '/admin/configuracion', icon: 'ajustes' },
        { label: 'Identidad',     to: '/admin/identidad',     icon: 'institucion' },
        { label: 'Roles',         to: '/admin/roles',         icon: 'escudo' },
        { label: 'Bitácoras',     to: '/admin/bitacoras',     icon: 'bitacora' },
    ],
    director: [
        { label: 'Inicio',   to: '/director',          icon: 'inicio', exact: true },
        { label: 'Riesgo',   to: '/director/riesgo',   icon: 'alerta' },
        { label: 'Reportes', to: '/director/reportes', icon: 'reportes' },
    ],
    docente: [
        { label: 'Mis cursos', to: '/docente/cursos', icon: 'cursos', exact: true },
    ],
    lider_equipo: [
        { label: 'Inicio',               to: '/lider/inicio',               icon: 'tablero' },
        { label: 'Dashboard',            to: '/lider/dashboard',            icon: 'objetivo' },
        { label: 'Distribución',         to: '/lider/distribucion',         icon: 'distribucion' },
        { label: 'Asignar responsables', to: '/lider/asignar-responsables', icon: 'agenda' },
    ],
    estudiante: [
        { label: 'Inicio', to: '/estudiante/dashboard', icon: 'tablero' },
    ],
}
