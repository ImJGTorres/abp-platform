// ── Migas de pan del docente ──────────────────────────────────────────────────
// Niveles comunes para <MigasDePan />. Los nombres llegan en location.state
// (DetalleCurso → proyecto → fase → actividad); si no están (p. ej. tras recargar)
// se muestra el nombre genérico del nivel.

/** Mis cursos › Curso */
export function migasCurso(cursoId, cursoNombre) {
    return [
        { label: 'Mis cursos', to: '/docente/cursos' },
        cursoId && { label: cursoNombre ?? 'Curso', to: `/docente/cursos/${cursoId}` },
    ]
}

/** Mis cursos › Curso › Proyecto  (state = location.state de las vistas del proyecto).
 *  Si se entró desde otra pantalla (state.origen, ver utils/origen.js), esa pantalla reemplaza a Mis cursos › Curso. */
export function migasProyecto(proyectoId, state) {
    return [
        ...(state?.origen
            ? [{ label: state.origen.label, to: state.origen.to }]
            : migasCurso(state?.cursoId, state?.cursoNombre)),
        {
            label: state?.nombre ?? 'Proyecto',
            to: `/docente/proyectos/${proyectoId}/monitoreo`,
            state,
        },
    ]
}

/** … › Proyecto › Fases › Fase  (vistas de una fase o de una actividad) */
export function migasFase(proyectoId, faseId, state) {
    return [
        ...migasProyecto(proyectoId, state),
        { label: 'Fases', to: `/docente/proyectos/${proyectoId}/fases`, state },
        {
            label: state?.faseNombre ?? 'Fase',
            to: `/docente/proyectos/${proyectoId}/fases/${faseId}/actividades`,
            state,
        },
    ]
}
