// ── Semáforo único de la plataforma ───────────────────────────────────────────
// Mismos colores y textos en todas las vistas. El nivel lo decide quien llama
// (idealmente el backend); este componente solo lo pinta.

export const SEMAFORO_NIVELES = {
    verde: { color: '#2e7d32', bg: '#f1f8e9', texto: 'Óptimo' },
    amarillo: { color: '#f9a825', bg: '#fffde7', texto: 'Alerta preventiva' },
    rojo: { color: '#c62828', bg: '#ffebee', texto: 'Riesgo crítico' },
}

const TAMANOS = {
    sm: { punto: 'w-2 h-2', texto: 'text-[10px]', pill: 'gap-1 px-2 py-0.5 rounded-lg' },
    md: { punto: 'w-2.5 h-2.5', texto: 'text-[11px]', pill: 'gap-1.5 px-2.5 py-1 rounded-xl' },
}

// TODO HU-042: respaldo temporal para vistas que aún no reciben `nivel` del backend.
// Eliminar cuando el backend envíe el nivel en todos los endpoints.
// eslint-disable-next-line react-refresh/only-export-components
export function nivelPorPorcentaje(p) {
    const valor = Number(p ?? 0)
    if (valor >= 60) return 'verde'
    if (valor >= 30) return 'amarillo'
    return 'rojo'
}

export default function Semaforo({ nivel, size = 'md', mostrarTexto = true }) {
    const n = SEMAFORO_NIVELES[nivel] ?? SEMAFORO_NIVELES.rojo
    const t = TAMANOS[size] ?? TAMANOS.md

    if (!mostrarTexto) {
        return (
            <span
                className={`inline-block rounded-full flex-shrink-0 ${t.punto}`}
                style={{ backgroundColor: n.color }}
                title={n.texto}
                aria-label={n.texto}
                role="img"
            />
        )
    }

    return (
        <span className={`inline-flex items-center flex-shrink-0 ${t.pill}`} style={{ backgroundColor: n.bg }}>
            <span className={`rounded-full flex-shrink-0 ${t.punto}`} style={{ backgroundColor: n.color }} />
            <span className={`font-bold whitespace-nowrap ${t.texto}`} style={{ color: n.color }}>{n.texto}</span>
        </span>
    )
}
