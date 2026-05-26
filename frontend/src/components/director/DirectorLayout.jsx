import { useState, useEffect } from 'react'
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom'
import { authApi, session } from '../../services/api'

// ── Iconos ────────────────────────────────────────────────────────────────────

function IconHome() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 8.5L10 3l7 5.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V8.5z" />
            <path d="M8 18v-6h4v6" />
        </svg>
    )
}

function IconChart() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="11" width="4" height="7" rx="1" />
            <rect x="8" y="6" width="4" height="12" rx="1" />
            <rect x="14" y="2" width="4" height="16" rx="1" />
        </svg>
    )
}

function IconClipboard() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="14" height="14" rx="2" />
            <path d="M7 2h6v4H7z" />
            <path d="M7 10h6M7 13h4" />
        </svg>
    )
}

function IconSettings() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="2.5" />
            <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42" />
        </svg>
    )
}

function IconProfile() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="7" r="3" /><path d="M3 17a7 7 0 0114 0" />
        </svg>
    )
}

function IconLogout() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 15l4-5-4-5" /><path d="M17 10H7" /><path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3" />
        </svg>
    )
}

function IconMenu() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M3 5h14M3 10h14M3 15h14" />
        </svg>
    )
}

function IconX() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M4 4l12 12M16 4L4 16" />
        </svg>
    )
}

function IconChevronLeft() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 4L6 10l6 6" /></svg>
    )
}

function IconChevronRight() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 4l6 6-6 6" /></svg>
    )
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
    { label: 'Dashboard', to: '/director', icon: <IconHome />, exact: true },
    { label: 'Indicadores', to: '/director/indicadores', icon: <IconChart /> },
    { label: 'Reportes', to: '/director/reportes', icon: <IconClipboard /> },
]

function SidebarContent({ collapsed, onCollapse, loggingOut, handleLogout, onNavClick, user }) {
    const location = useLocation()
    const esAdmin = user?.tipo_rol === 'administrador'

    return (
        <>
            {collapsed ? (
                <div className="flex items-center justify-center h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
                    <button onClick={onCollapse}
                        className="flex items-center justify-center w-8 h-8 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
                        title="Expandir menú">
                        <IconChevronRight />
                    </button>
                </div>
            ) : (
                <div className="flex items-center gap-2.5 px-4 h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
                    <div className="flex-shrink-0 w-8 h-8 bg-[#1565c0] rounded-lg flex items-center justify-center shadow-sm">
                        <svg viewBox="0 0 24 24" className="w-8 h-6 text-white" fill="currentColor">
                            <path d="M12 2L2 7l10 5 10-5-10-5z" />
                            <path d="M6 10v4c0 2.5 3.5 4 6 4s6-1.5 6-4v-4l-6 3-6-3z" opacity="0.9" />
                        </svg>
                    </div>
                    <span className="text-[15px] font-extrabold text-[#191c1d] tracking-tight whitespace-nowrap">Projex ABP</span>
                    <button onClick={onCollapse}
                        className="ml-auto flex items-center justify-center w-7 h-7 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
                        title="Colapsar menú">
                        <IconChevronLeft />
                    </button>
                </div>
            )}

            <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
                {!collapsed && (
                    <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">Director</p>
                )}
                {NAV_ITEMS.map(({ label, to, icon, exact }) => {
                    const isActive = exact
                        ? location.pathname === to
                        : location.pathname.startsWith(to)
                    const classes = isActive
                        ? 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer bg-[#1565c0] text-white shadow-[0_4px_12px_rgba(21,101,192,0.30)]'
                        : 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]'
                    return (
                        <Link key={to} to={to} className={classes} title={collapsed ? label : undefined} onClick={onNavClick}>
                            <span className="flex-shrink-0">{icon}</span>
                            {!collapsed && <span>{label}</span>}
                        </Link>
                    )
                })}

                {/* Sección de administración — visible solo para administrador */}
                {esAdmin && (
                    <>
                        {!collapsed && (
                            <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-4">Administración</p>
                        )}
                        {collapsed && <div className="my-2 border-t border-[#f0f2f3]" />}
                        <Link
                            to="/admin"
                            onClick={onNavClick}
                            title={collapsed ? 'Administración' : undefined}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer ${
                                location.pathname.startsWith('/admin')
                                    ? 'bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.25)]'
                                    : 'text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]'
                            }`}
                        >
                            <span className="flex-shrink-0"><IconSettings /></span>
                            {!collapsed && <span>Administración</span>}
                        </Link>
                    </>
                )}
            </nav>

            <div className="border-t border-[#e1e3e4] p-2 flex-shrink-0">
                <Link to="/perfil" onClick={onNavClick}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d] transition-colors">
                    <span className="flex-shrink-0"><IconProfile /></span>
                    {!collapsed && <span>Mi perfil</span>}
                </Link>
                <button onClick={handleLogout} disabled={loggingOut}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60">
                    <span className="flex-shrink-0"><IconLogout /></span>
                    {!collapsed && <span>{loggingOut ? 'Cerrando...' : 'Cerrar sesión'}</span>}
                </button>
            </div>
        </>
    )
}

// ── Layout principal ──────────────────────────────────────────────────────────

export default function DirectorLayout() {
    const navigate = useNavigate()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [loggingOut, setLoggingOut] = useState(false)
    const [user, setUser] = useState(() => session.getUser())

    useEffect(() => {
        const refresh = () => setUser(session.getUser())
        window.addEventListener('user-updated', refresh)
        return () => window.removeEventListener('user-updated', refresh)
    }, [])

    async function handleLogout() {
        setLoggingOut(true)
        try { await authApi.logout() } catch { /* ignored */ }
        navigate('/login', { replace: true })
    }

    return (
        <div className="flex h-screen bg-[#f8f9fa] overflow-hidden">
            {/* Sidebar escritorio */}
            <aside className={`hidden md:flex flex-col bg-white border-r border-[#e1e3e4] transition-all duration-200 ${collapsed ? 'w-[60px]' : 'w-[220px]'}`}>
                <SidebarContent
                    collapsed={collapsed}
                    onCollapse={() => setCollapsed(c => !c)}
                    loggingOut={loggingOut}
                    handleLogout={handleLogout}
                    onNavClick={() => {}}
                    user={user}
                />
            </aside>

            {/* Sidebar móvil */}
            {mobileOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <div className="absolute inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
                    <aside className="relative z-50 flex flex-col w-[220px] h-full bg-white border-r border-[#e1e3e4]">
                        <SidebarContent
                            collapsed={false}
                            loggingOut={loggingOut}
                            handleLogout={handleLogout}
                            onNavClick={() => setMobileOpen(false)}
                            user={user}
                        />
                    </aside>
                </div>
            )}

            {/* Contenido */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Topbar móvil */}
                <header className="md:hidden flex items-center gap-3 h-[56px] px-4 bg-white border-b border-[#e1e3e4] flex-shrink-0">
                    <button onClick={() => setMobileOpen(true)} className="text-[#4c616c] hover:text-[#191c1d] transition-colors">
                        <IconMenu />
                    </button>
                    <span className="text-[15px] font-extrabold text-[#191c1d] tracking-tight">Projex ABP</span>
                    {user?.nombre && (
                        <span className="ml-auto text-[12px] text-[#9ba7ae]">
                            {user.nombre}
                        </span>
                    )}
                </header>

                <main className="flex-1 overflow-y-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
