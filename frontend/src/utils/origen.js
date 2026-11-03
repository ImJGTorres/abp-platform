// Origen de navegación: quien enlaza a una pantalla de detalle manda en location.state.origen
// la pantalla de la que viene ({ to, label }); el destino la usa en su botón "volver" y en las
// migas de pan. Sin origen, cada pantalla vuelve a su lugar de siempre.
// Uso: <Link to={...} state={conOrigen(location, 'Calendario', { ...otroEstado })} />
export function conOrigen(location, label, extra = {}) {
    return { ...extra, origen: { to: `${location.pathname}${location.search}`, label } }
}

// Quita el origen del estado al salir de la jerarquía (p. ej. de la actividad al curso),
// para que la pantalla siguiente no herede un "volver" que no le corresponde.
export function sinOrigen(state) {
    if (!state?.origen) return state
    // eslint-disable-next-line no-unused-vars
    const { origen, ...resto } = state
    return resto
}
