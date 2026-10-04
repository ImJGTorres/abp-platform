import { Link } from 'react-router-dom'

// ──Breadcrumbs──────────────────────────────────────────────────────────────

function Separador() {
    return (
        <svg className="w-3 h-3 text-[#9ba7ae] flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 3l5 5-5 5" />
        </svg>
    )
}

export default function MigasDePan({ items, className = 'mb-4' }) {
    const visibles = items.filter(item => item && item.label)

    return (
        <nav aria-label="Ubicación" className={`flex items-center gap-2 text-[13px] flex-wrap min-w-0 ${className}`}>
            {visibles.map((item, i) => {
                const esActual = i === visibles.length - 1
                return (
                    <span key={`${i}-${item.label}`} className="flex items-center gap-2 min-w-0">
                        {i > 0 && <Separador />}
                        {esActual || !item.to ? (
                            <span
                                className={`truncate max-w-[240px] ${esActual ? 'text-[#191c1d] font-medium' : 'text-[#9ba7ae]'}`}
                                aria-current={esActual ? 'page' : undefined}
                            >
                                {item.label}
                            </span>
                        ) : (
                            <Link
                                to={item.to}
                                state={item.state}
                                className="text-[#9ba7ae] hover:text-[#4c616c] transition-colors truncate max-w-[240px]"
                            >
                                {item.label}
                            </Link>
                        )}
                    </span>
                )
            })}
        </nav>
    )
}
