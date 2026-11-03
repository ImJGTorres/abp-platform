// ── Calendario unificado (HU-040): fechas y estilos compartidos ──────────────
// Las fechas del backend llegan como 'AAAA-MM-DD' (sin hora). Se manejan como
// fechas locales para que no se corran un día por la zona horaria.

export const MESES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

// Semana de lunes a domingo
export const DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS_LARGOS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

// Urgencia calculada por el backend: vencido rojo, próximo ámbar, normal azul
export const URGENCIA = {
    vencido: { label: 'Vencido', color: '#c62828', bg: '#ffebee', borde: '#d32f2f' },
    proximo: { label: 'Próximo', color: '#a15c00', bg: '#fff8e1', borde: '#f9a825' },
    normal:  { label: 'Normal',  color: '#1565c0', bg: '#e3f2fd', borde: '#1e88e5' },
}

export const TIPO_EVENTO = {
    hito: 'Hito',
    entrega: 'Entrega',
    revision: 'Revisión',
    actividad: 'Actividad',
}

/** Date → 'AAAA-MM-DD' (fecha local) */
export function aISO(fecha) {
    const m = String(fecha.getMonth() + 1).padStart(2, '0')
    const d = String(fecha.getDate()).padStart(2, '0')
    return `${fecha.getFullYear()}-${m}-${d}`
}

/** 'AAAA-MM-DD' → Date local */
export function desdeISO(texto) {
    const [a, m, d] = texto.split('-').map(Number)
    return new Date(a, m - 1, d)
}

export function inicioMes(fecha) {
    return new Date(fecha.getFullYear(), fecha.getMonth(), 1)
}

export function finMes(fecha) {
    return new Date(fecha.getFullYear(), fecha.getMonth() + 1, 0)
}

export function sumarMeses(fecha, n) {
    return new Date(fecha.getFullYear(), fecha.getMonth() + n, 1)
}

export function mismoDia(a, b) {
    return !!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

export function mismoMes(a, b) {
    return !!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
}

/** "Octubre 2026" */
export function tituloMes(fecha) {
    return `${MESES[fecha.getMonth()]} ${fecha.getFullYear()}`
}

/** "Miércoles 14 de octubre de 2026" */
export function fechaLarga(fecha) {
    return `${DIAS_LARGOS[fecha.getDay()]} ${fecha.getDate()} de ${MESES[fecha.getMonth()].toLowerCase()} de ${fecha.getFullYear()}`
}

/** "Mié 14" */
export function fechaCorta(fecha) {
    return `${DIAS_SEMANA[(fecha.getDay() + 6) % 7]} ${fecha.getDate()}`
}
