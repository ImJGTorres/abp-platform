import { useState, useEffect } from 'react'
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom'
import { authApi, session } from '../../services/api'
import MenuLateral from '../Compartidos/MenuLateral'
import { getMiEquipo } from '../../services/liderEquipoApi'
import BarraSuperior from '../Compartidos/BarraSuperior'

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

function IconLogout() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 15l4-5-4-5" /><path d="M17 10H7" /><path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3" />
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

function IconUsers() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            className="w-5 h-5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            {/* Usuarios */}
            <path d="M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
            <path d="M15 13a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />

            {/* Base usuarios */}
            <path d="M4 19c0-3 2.5-5 5-5s5 2 5 5" />
            <path d="M14 19c.3-2 1.8-3.5 4-3.5 1 0 1.9.3 2.6.8" />
        </svg>
    )
}

function SidebarContent({ collapsed, onCollapse, loggingOut, handleLogout, onNavClick, proyectoId }) {
    // Ítems del proyecto abierto (dependen de proyectoId)
    const itemsProyecto = proyectoId ? [
        { label: 'Tablero Kanban', to: `/lider/proyectos/${proyectoId}/kanban`, icon: 'kanban' },
    ] : []

    return (
        <>
            {/* Marca + Collapse */}
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
                <div className="flex items-center gap-2.5 px-4 h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
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
            )}

            {/* Navegación */}
            {/* Sin enlace "volver": todas las pantallas del líder muestran este menú, que ya incluye Inicio */}
            <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
                {!collapsed && (
                    <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">Líder de Equipo</p>
                )}
                <MenuLateral rol="lider_equipo" itemsContextuales={itemsProyecto} collapsed={collapsed} onNavClick={onNavClick} />
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

export default function LiderLayout() {
    const navigate = useNavigate()
    const location = useLocation()
    const [user, setUser] = useState(() => session.getUser())
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [loggingOut, setLoggingOut] = useState(false)
    const [proyectoId, setProyectoId] = useState(() => {
        const match = location.pathname.match(/^\/lider\/proyectos\/(\d+)/)
        return match?.[1] ?? null
    })

    useEffect(() => {
        getMiEquipo()
            .then(data => { if (data?.proyecto?.id) setProyectoId(String(data.proyecto.id)) })
            .catch(() => {})
    }, [])

    useEffect(() => {
        const refresh = () => setUser(session.getUser())
        window.addEventListener('user-updated', refresh)
        return () => window.removeEventListener('user-updated', refresh)
    }, [])

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
            onClick={() => setMobileOpen(false)}>

            {/* Overlay móvil */}
            {mobileOpen && (
                <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
            )}

            {/* Sidebar desktop */}
            <aside className={`hidden lg:flex ${sidebarW} flex-shrink-0 flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>
                <SidebarContent collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)}
                    loggingOut={loggingOut} handleLogout={handleLogout} onNavClick={undefined}
                    proyectoId={proyectoId} />
            </aside>

            {/* Sidebar móvil */}
            <aside className={`lg:hidden fixed top-0 left-0 h-full w-[260px] flex flex-col bg-white border-r border-[#e1e3e4] z-40 transition-transform duration-200 ease-in-out ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
                onClick={e => e.stopPropagation()}>
                <SidebarContent collapsed={false} onCollapse={null}
                    loggingOut={loggingOut} handleLogout={handleLogout}
                    onNavClick={() => setMobileOpen(false)}
                    proyectoId={proyectoId} />
            </aside>

            {/* Contenido */}
            <main className="flex-1 flex flex-col overflow-hidden min-w-0">
                <BarraSuperior user={user} menuAbierto={mobileOpen} onToggleMenu={() => setMobileOpen(o => !o)}
                    onLogout={handleLogout} loggingOut={loggingOut} />

                <div className="flex-1 overflow-hidden flex flex-col">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}