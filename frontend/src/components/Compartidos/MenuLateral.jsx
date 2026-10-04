import { Link, useLocation } from 'react-router-dom'
import { MENU_POR_ROL } from '../../config/menuPorRol'

const svgProps = {
    viewBox: '0 0 20 20', fill: 'none', className: 'w-5 h-5', stroke: 'currentColor',
    strokeWidth: '1.6', strokeLinecap: 'round', strokeLinejoin: 'round',
}

const ICONOS = {
    inicio: (
        <svg {...svgProps}>
            <path d="M3 8.5L10 3l7 5.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V8.5z" />
            <path d="M8 18v-6h4v6" />
        </svg>
    ),
    usuarios: (
        <svg {...svgProps}>
            <path d="M13 7a3 3 0 11-6 0 3 3 0 016 0z" />
            <path d="M3 17a7 7 0 0114 0" />
        </svg>
    ),
    cursos: (
        <svg {...svgProps}>
            <path d="M2 3h6a2 2 0 012 2v11a2 2 0 00-2 2H2z" />
            <path d="M18 3h-6a2 2 0 00-2 2v11a2 2 0 012 2h6z" />
        </svg>
    ),
    calendario: (
        <svg {...svgProps}>
            <rect x="2" y="4" width="16" height="14" rx="2" />
            <path d="M6 2v3M14 2v3M2 8h16" />
        </svg>
    ),
    ajustes: (
        <svg {...svgProps}>
            <circle cx="10" cy="10" r="2.5" />
            <path d="M10 2v1.5M10 16.5V18M2 10h1.5M16.5 10H18M4.22 4.22l1.06 1.06M14.72 14.72l1.06 1.06M4.22 15.78l1.06-1.06M14.72 5.28l1.06-1.06" />
        </svg>
    ),
    institucion: (
        <svg {...svgProps}>
            <path d="M2 18h16M3 8l7-5 7 5" />
            <path d="M5 8v8M8.5 8v8M11.5 8v8M15 8v8" />
        </svg>
    ),
    escudo: (
        <svg {...svgProps}>
            <path d="M10 2l7 3v5c0 4-3 6.5-7 8-4-1.5-7-4-7-8V5l7-3z" />
        </svg>
    ),
    bitacora: (
        <svg {...svgProps}>
            <path d="M14 4V3a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v1" />
            <path d="M10 13V8a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v5" />
            <path d="M6 10V7a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v3" />
            <path d="M18 9v4a2 2 0 01-2 2 2 2 0 01-2-2v-4" />
            <path d="M2 10h16M2 14h16" />
        </svg>
    ),
    alerta: (
        <svg {...svgProps}>
            <path d="M10 2L1.5 17h17L10 2z" />
            <path d="M10 8v4" />
            <circle cx="10" cy="14" r="0.6" fill="currentColor" />
        </svg>
    ),
    reportes: (
        <svg {...svgProps}>
            <rect x="3" y="4" width="14" height="14" rx="2" />
            <path d="M7 2h6v4H7z" />
            <path d="M7 10h6M7 13h4" />
        </svg>
    ),
    estudiantes: (
        <svg {...svgProps}>
            <circle cx="7" cy="7" r="3" />
            <path d="M1 17a6 6 0 0112 0" />
            <path d="M13 5a3 3 0 110 6" opacity="0.7" />
            <path d="M16 17a5 5 0 00-3-4.6" opacity="0.7" />
        </svg>
    ),
    proyectos: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="7" height="7" rx="1.5" />
            <rect x="11" y="3" width="7" height="7" rx="1.5" />
            <rect x="2" y="12" width="7" height="5" rx="1.5" />
            <rect x="11" y="12" width="7" height="5" rx="1.5" />
        </svg>
    ),
    reorganizar: (
        <svg {...svgProps}>
            <path d="M3 6h11M11 4l3 2-3 2" />
            <path d="M17 14H6M9 12l-3 2 3 2" />
        </svg>
    ),
    desempeno: (
        <svg {...svgProps}>
            <path d="M10 3a7 7 0 100 14A7 7 0 0010 3z" />
            <path d="M10 7v4" />
            <path d="M10 13h.01" strokeWidth="2" strokeLinecap="round" />
            <path d="M7 10l1.5 1.5L11 8" />
        </svg>
    ),
    tablero: (
        <svg {...svgProps}>
            <rect x="2" y="2" width="7" height="7" rx="1.5" />
            <rect x="11" y="2" width="7" height="7" rx="1.5" />
            <rect x="2" y="11" width="7" height="7" rx="1.5" />
            <rect x="11" y="11" width="7" height="7" rx="1.5" />
        </svg>
    ),
    objetivo: (
        <svg {...svgProps}>
            <circle cx="10" cy="10" r="7" />
            <circle cx="10" cy="10" r="4" />
            <circle cx="10" cy="10" r="1" fill="currentColor" />
        </svg>
    ),
    distribucion: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="6" height="5" rx="1" />
            <rect x="12" y="3" width="6" height="5" rx="1" />
            <rect x="2" y="12" width="6" height="5" rx="1" />
            <rect x="12" y="12" width="6" height="5" rx="1" />
            <path d="M8 5.5h4M8 14.5h4" />
        </svg>
    ),
    agenda: (
        <svg {...svgProps}>
            <rect x="3" y="4" width="14" height="14" rx="2" />
            <path d="M3 8h14M7 2v4M13 2v4" />
        </svg>
    ),
    progreso: (
        <svg {...svgProps}>
            <path d="M3 14l4-4 4 4 6-6M17 8v-4h-4" />
        </svg>
    ),
    kanban: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="4" height="14" rx="1" />
            <rect x="8" y="3" width="4" height="8" rx="1" />
            <rect x="14" y="3" width="4" height="11" rx="1" />
        </svg>
    ),
    // ── Menú del proyecto (docente) ──
    diana: (
        <svg {...svgProps}>
            <circle cx="10" cy="10" r="8" /><circle cx="10" cy="10" r="5" /><circle cx="10" cy="10" r="2" />
        </svg>
    ),
    rap: (
        <svg {...svgProps}>
            <rect x="5" y="2" width="10" height="3" rx="1" /><rect x="3" y="4" width="14" height="14" rx="2" />
            <path d="M7 10h6M7 13h4" />
        </svg>
    ),
    cronograma: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M2 7h16M6 2v3M14 2v3" />
        </svg>
    ),
    fases: (
        <svg {...svgProps}>
            <path d="M2 5h16M2 10h16M2 15h16" />
            <circle cx="5" cy="5" r="1.5" fill="currentColor" />
            <circle cx="5" cy="10" r="1.5" fill="currentColor" />
            <circle cx="5" cy="15" r="1.5" fill="currentColor" />
        </svg>
    ),
    miembros: (
        <svg {...svgProps}>
            <circle cx="8" cy="6" r="3" /><path d="M1 17a7 7 0 0114 0" />
            <circle cx="15" cy="7" r="2.5" /><path d="M15 13c2.5 0 4 1.5 4 4" />
        </svg>
    ),
    monitoreo: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="16" height="11" rx="2" />
            <path d="M7 17h6M10 14v3" />
            <path d="M5 10l3-3 2 2 3-3 2 2" />
        </svg>
    ),
    autoeval: (
        <svg {...svgProps}>
            <circle cx="8" cy="6" r="3" />
            <path d="M2 17a6 6 0 0112 0" />
            <path d="M14 9l2 2 4-4" strokeWidth="1.8" />
        </svg>
    ),
    coeval: (
        <svg {...svgProps}>
            <circle cx="7" cy="5" r="2.5" />
            <path d="M1 15a6 6 0 0112 0" />
            <circle cx="14" cy="6" r="2" />
            <path d="M14 11c2.5 0 4 1.5 4 4" />
        </svg>
    ),
    // ── Proyecto (estudiante) ──
    actividadesEst: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M6 7h8M6 10h6M6 13h4" />
        </svg>
    ),
    kanbanEst: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="4" height="14" rx="1" />
            <rect x="8" y="3" width="4" height="9" rx="1" />
            <rect x="14" y="3" width="4" height="11" rx="1" />
        </svg>
    ),
    progresoEst: (
        <svg {...svgProps}>
            <path d="M3 14l4-5 3 3 4-6 3 4" />
            <path d="M2 17h16" />
        </svg>
    ),
    autoevalEst: (
        <svg {...svgProps}>
            <circle cx="10" cy="7" r="3" />
            <path d="M3 17a7 7 0 0114 0" />
            <circle cx="10" cy="7" r="1" fill="currentColor" stroke="none" />
        </svg>
    ),
    coevalEst: (
        <svg {...svgProps}>
            <circle cx="7" cy="6" r="2.5" />
            <path d="M1 16a6 6 0 0112 0" />
            <circle cx="14" cy="7" r="2" />
            <path d="M14 12c2 0 3.5 1.2 3.5 3.5" />
        </svg>
    ),
    dianaEst: (
        <svg {...svgProps}>
            <circle cx="10" cy="10" r="7" />
            <circle cx="10" cy="10" r="3.5" />
            <circle cx="10" cy="10" r="1" fill="currentColor" stroke="none" />
        </svg>
    ),
    repartir: (
        <svg {...svgProps}>
            <circle cx="4" cy="10" r="2" />
            <circle cx="16" cy="5" r="2" />
            <circle cx="16" cy="15" r="2" />
            <path d="M6 10h4M10 10l4-3.5M10 10l4 3.5" />
        </svg>
    ),
    asignar: (
        <svg {...svgProps}>
            <circle cx="8" cy="6" r="2.5" />
            <path d="M2 16a6 6 0 0110.5-4" />
            <path d="M14 12l2 2 3-3" />
        </svg>
    ),
    // ── Actividad (docente) ──
    actividad: (
        <svg {...svgProps}>
            <rect x="3" y="3" width="14" height="14" rx="2" />
            <path d="M7 10l2 2 4-4" />
        </svg>
    ),
    entregable: (
        <svg {...svgProps}>
            <path d="M7 3H5a1 1 0 00-1 1v12a1 1 0 001 1h10a1 1 0 001-1V4a1 1 0 00-1-1h-2" />
            <path d="M7 3a2 2 0 014 0H7z" />
            <path d="M7 10h6M7 13h4" />
        </svg>
    ),
    rubrica: (
        <svg {...svgProps}>
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M6 8h8M6 11h8M6 14h5" />
            <path d="M2 8h2M2 11h2M2 14h2" />
        </svg>
    ),
    historial: (
        <svg {...svgProps}>
            <circle cx="10" cy="10" r="8" />
            <path d="M10 6v4l3 2" />
        </svg>
    ),
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function estaActivo(item, pathname) {
    if (item.activo) return item.activo(pathname)
    if (item.exact) return pathname === item.to
    return pathname === item.to || pathname.startsWith(`${item.to}/`)
}

function navLinkClass(isActive) {
    const base = 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer'
    return isActive
        ? `${base} bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.30)]`
        : `${base} text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]`
}


export default function MenuLateral({ rol, itemsContextuales = [], mostrarFijos = true, collapsed = false, onNavClick }) {
    const { pathname } = useLocation()
    const fijos = mostrarFijos ? (MENU_POR_ROL[rol] ?? []) : []
    const items = [...fijos, ...itemsContextuales]

    return items.map(item => item.seccion ? (
        collapsed
            ? <div key={`sec-${item.seccion}`} className="my-2 border-t border-[#f0f2f3]" />
            : (
                <p key={`sec-${item.seccion}`} className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-3">
                    {item.seccion}
                </p>
            )
    ) : (
        <Link
            key={item.to}
            to={item.to}
            state={item.state}
            className={navLinkClass(estaActivo(item, pathname))}
            title={collapsed ? item.label : undefined}
            onClick={onNavClick}
        >
            <span className="flex-shrink-0">{ICONOS[item.icon]}</span>
            {!collapsed && <span>{item.label}</span>}
        </Link>
    ))
}
