import { useState, useEffect } from 'react'
import { NavLink, Outlet, useNavigate, Link, useParams, useLocation } from 'react-router-dom'
import { authApi, session, buildMediaUrl } from '../../services/api'

function IconTarget() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="8" /><circle cx="10" cy="10" r="5" /><circle cx="10" cy="10" r="2" />
        </svg>
    )
}

function IconClipboard() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="2" width="10" height="3" rx="1" /><rect x="3" y="4" width="14" height="14" rx="2" />
            <path d="M7 10h6M7 13h4" />
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

function IconProfile() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="7" r="3" /><path d="M3 17a7 7 0 0114 0" />
        </svg>
    )
}

function IconCalendar() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M2 7h16M6 2v3M14 2v3" />
        </svg>
    )
}

function IconPhases() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 5h16M2 10h16M2 15h16" />
            <circle cx="5" cy="5" r="1.5" fill="currentColor" />
            <circle cx="5" cy="10" r="1.5" fill="currentColor" />
            <circle cx="5" cy="15" r="1.5" fill="currentColor" />
        </svg>
    )
}

function IconUsers() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="6" r="3" /><path d="M1 17a7 7 0 0114 0" />
            <circle cx="15" cy="7" r="2.5" /><path d="M15 13c2.5 0 4 1.5 4 4" />
        </svg>
    )
}

function IconChevronLeft() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 4L6 10l6 6" />
        </svg>
    )
}

function IconChevronRight() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 4l6 6-6 6" />
        </svg>
    )
}

function navLinkClass({ isActive }) {
    const base = 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer'
    return isActive
        ? `${base} bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.30)]`
        : `${base} text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]`
}

function SidebarContent({ collapsed, onCollapse, loggingOut, handleLogout, onNavClick, proyectoId, nombreProyecto, periodoNombre, cursoId, cursoNombre, navState }) {
    const NAV_ITEMS = [
        { label: 'Objetivos', to: `/docente/proyectos/${proyectoId}/objetivos`, icon: <IconTarget /> },
        { label: 'Resultados de Aprendizaje', to: `/docente/proyectos/${proyectoId}/raps`, icon: <IconClipboard /> },
        { label: 'Cronograma', to: `/docente/proyectos/${proyectoId}/cronograma`, icon: <IconCalendar /> },
        { label: 'Perfiles y Roles', to: `/docente/proyectos/${proyectoId}/perfiles-roles`, icon: <IconUsers /> },
        { label: 'Fases', to: `/docente/proyectos/${proyectoId}/fases`, icon: <IconPhases /> },
    ]

    return (
        <>
            {/* Header proyecto + Collapse */}
            {collapsed ? (
                <div className="flex items-center justify-center h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
                    {onCollapse && (
                        <button onClick={onCollapse}
                            className="flex items-center justify-center w-8 h-8 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
                            title="Expandir menú">
                            <IconChevronRight />
                        </button>
                    )}
                </div>
            ) : (
                <div className="px-4 py-4 border-b border-[#e1e3e4] flex-shrink-0">
                    <div className="flex items-center gap-2.5 mb-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-[#d32f2f] rounded-lg flex items-center justify-center shadow-sm">
                            <svg viewBox="0 0 24 24" className="w-8 h-6 text-white" fill="currentColor">
                                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                <path d="M6 10v4c0 2.5 3.5 4 6 4s6-1.5 6-4v-4l-6 3-6-3z" opacity="0.9" />
                                <path d="M22 7v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                <circle cx="22" cy="14" r="1" fill="currentColor" />
                            </svg>
                        </div>
                        <span className="text-[15px] font-extrabold text-[#191c1d] tracking-tight whitespace-nowrap">Projex ABP</span>
                        {onCollapse && (
                            <button onClick={onCollapse}
                                className="ml-auto flex items-center justify-center w-7 h-7 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
                                title="Colapsar menú">
                                <IconChevronLeft />
                            </button>
                        )}
                    </div>
                    <h2 className="text-[14px] font-bold text-[#191c1d] leading-tight mb-1 line-clamp-2">{nombreProyecto || 'Proyecto'}</h2>
                    <p className="text-[11px] text-[#9ba7ae]">{periodoNombre || 'Sin periodo'}</p>
                </div>
            )}

            {/* Navegación */}
            <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
                {!collapsed && cursoId && (
                    <Link
                        to={`/docente/cursos/${cursoId}`}
                        onClick={onNavClick}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-semibold text-[#9ba7ae] tracking-[0.6px] uppercase hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-all mb-1 truncate">
                        <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3 flex-shrink-0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                        <span className="truncate">{cursoNombre || 'Curso'}</span>
                    </Link>
                )}
                {!collapsed && (
                    <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">Proyecto</p>
                )}
                {NAV_ITEMS.map(({ label, to, icon }) => (
                    <NavLink key={to} to={to} state={navState} className={navLinkClass} title={collapsed ? label : undefined} onClick={onNavClick}>
                        <span className="flex-shrink-0">{icon}</span>
                        {!collapsed && <span>{label}</span>}
                    </NavLink>
                ))}
            </nav>

            {/* Perfil + Logout */}
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

export default function ProyectoLayout() {
    const navigate = useNavigate()
    const location = useLocation()
    const { proyectoId } = useParams()
    const [user, setUser] = useState(() => session.getUser())
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [loggingOut, setLoggingOut] = useState(false)
    const [topbarMenuOpen, setTopbarMenuOpen] = useState(false)
    const [proyecto, setProyecto] = useState(null)
    const [savedNavState, setSavedNavState] = useState(null)

    useEffect(() => {
        const refresh = () => setUser(session.getUser())
        window.addEventListener('user-updated', refresh)
        return () => window.removeEventListener('user-updated', refresh)
    }, [])

    useEffect(() => {
        const state = location.state
        if (state?.nombre) {
            setProyecto({ nombre: state.nombre, periodo: state.periodo ?? '' })
            setSavedNavState(state)
        }
    }, [location.state, proyectoId])

    async function handleLogout() {
        setLoggingOut(true)
        try { await authApi.logout() } catch { }
        finally {
            setLoggingOut(false)
            navigate('/login', { replace: true })
        }
    }

    const sidebarW = collapsed ? 'w-[68px]' : 'w-[220px]'

    return (
        <div className="flex h-screen bg-[#f8f9fa] overflow-hidden" style={{ fontFamily: "'Manrope', sans-serif" }}
            onClick={() => { setTopbarMenuOpen(false); setMobileOpen(false) }}>

            {/* Overlay móvil */}
            {mobileOpen && (
                <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
            )}

            {/* Sidebar desktop */}
            <aside className={`hidden lg:flex ${sidebarW} flex-shrink-0 flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>
                <SidebarContent collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)}
                    loggingOut={loggingOut} handleLogout={handleLogout} onNavClick={undefined}
                    proyectoId={proyectoId} nombreProyecto={proyecto?.nombre} periodoNombre={proyecto?.periodo}
                    cursoId={savedNavState?.cursoId} cursoNombre={savedNavState?.cursoNombre}
                    navState={savedNavState} />
            </aside>

            {/* Sidebar móvil */}
            <aside className={`lg:hidden fixed top-0 left-0 h-full w-[260px] flex flex-col bg-white border-r border-[#e1e3e4] z-40 transition-transform duration-200 ease-in-out ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
                onClick={e => e.stopPropagation()}>
                <SidebarContent collapsed={false} onCollapse={null}
                    loggingOut={loggingOut} handleLogout={handleLogout}
                    onNavClick={() => setMobileOpen(false)} proyectoId={proyectoId} nombreProyecto={proyecto?.nombre} periodoNombre={proyecto?.periodo}
                    cursoId={savedNavState?.cursoId} cursoNombre={savedNavState?.cursoNombre}
                    navState={savedNavState} />
            </aside>

            {/* Contenido */}
            <main className="flex-1 flex flex-col overflow-hidden min-w-0">
                <header className="h-[60px] flex-shrink-0 bg-white border-b border-[#e1e3e4] flex items-center px-4 sm:px-6 gap-4">
                    <button className="lg:hidden flex items-center justify-center w-9 h-9 rounded-xl hover:bg-[#f0f2f3] transition-colors text-[#4c616c]"
                        onClick={e => { e.stopPropagation(); setMobileOpen(o => !o) }}>
                        {mobileOpen ? <IconX /> : <IconMenu />}
                    </button>
                    <div className="flex-1" />
                    {user && (
                        <div className="relative">
                            <button onClick={e => { e.stopPropagation(); setTopbarMenuOpen(o => !o) }}
                                className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
                                <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center overflow-hidden">
                                    {user.foto_perfil
                                        ? <img src={buildMediaUrl(user.foto_perfil)} alt="" className="w-full h-full object-cover" onError={e => { e.target.style.display = 'none' }} />
                                        : <span className="text-[12px] font-bold text-[#af101a]">{user.nombre?.[0]?.toUpperCase() ?? 'D'}</span>
                                    }
                                </div>
                                <div className="hidden sm:block text-left">
                                    <p className="text-[13px] font-semibold text-[#191c1d] leading-tight">{user.nombre ?? 'Docente'}</p>
                                    <p className="text-[11px] text-[#9ba7ae] leading-tight">Docente</p>
                                </div>
                            </button>
                            {topbarMenuOpen && (
                                <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-[#e1e3e4] shadow-lg overflow-hidden z-30">
                                    <Link to="/perfil" onClick={() => setTopbarMenuOpen(false)}
                                        className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#191c1d] hover:bg-[#f0f2f3] transition-colors">
                                        <IconProfile />Mi perfil
                                    </Link>
                                    <button onClick={() => { setTopbarMenuOpen(false); handleLogout() }} disabled={loggingOut}
                                        className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60">
                                        <IconLogout />{loggingOut ? 'Cerrando...' : 'Cerrar sesión'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </header>

                <div className="flex-1 overflow-hidden flex flex-col">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}