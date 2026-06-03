import { useState, useEffect } from 'react'
import { NavLink, Outlet, useNavigate, Link, useParams, useLocation, useMatch } from 'react-router-dom'
import { authApi, session, buildMediaUrl } from '../../services/api'
import { estudianteProyectosApi, coevaluacionApi } from '../../services/estudianteApi'

// ── Icons ─────────────────────────────────────────────────────────────────────

function IconActivity() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="16" height="14" rx="2" />
            <path d="M6 7h8M6 10h6M6 13h4" />
        </svg>
    )
}

function IconSelf() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="7" r="3" />
            <path d="M3 17a7 7 0 0114 0" />
            <circle cx="10" cy="7" r="1" fill="currentColor" stroke="none" />
        </svg>
    )
}

function IconPeers() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="7" cy="6" r="2.5" />
            <path d="M1 16a6 6 0 0112 0" />
            <circle cx="14" cy="7" r="2" />
            <path d="M14 12c2 0 3.5 1.2 3.5 3.5" />
        </svg>
    )
}

function IconKanban() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="4" height="14" rx="1" />
            <rect x="8" y="3" width="4" height="9" rx="1" />
            <rect x="14" y="3" width="4" height="11" rx="1" />
        </svg>
    )
}

function IconProgress() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 14l4-5 3 3 4-6 3 4" />
            <path d="M2 17h16" />
        </svg>
    )
}

function IconHistory() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="8" />
            <path d="M10 6v4l3 2" />
        </svg>
    )
}

function IconTarget() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="7" />
            <circle cx="10" cy="10" r="3.5" />
            <circle cx="10" cy="10" r="1" fill="currentColor" stroke="none" />
        </svg>
    )
}

function IconDistribute() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="4" cy="10" r="2" />
            <circle cx="16" cy="5" r="2" />
            <circle cx="16" cy="15" r="2" />
            <path d="M6 10h4M10 10l4-3.5M10 10l4 3.5" />
        </svg>
    )
}

function IconAssign() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="6" r="2.5" />
            <path d="M2 16a6 6 0 0110.5-4" />
            <path d="M14 12l2 2 3-3" />
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

// ── Sidebar Content ───────────────────────────────────────────────────────────

function SidebarContent({
    collapsed, onCollapse, loggingOut, handleLogout, onNavClick,
    proyectoId, proyectoNombre, periodoNombre,
    esCoevaluacion, companeros, selectedEvaluadoId, onSelectEvaluado,
    user,
}) {
    const esLider = user?.tipo_rol === 'lider_equipo'

    const NAV_ITEMS = [
        { label: 'Actividades',    to: `/estudiante/proyectos/${proyectoId}/actividades`,    icon: <IconActivity /> },
        { label: 'Kanban',         to: `/estudiante/proyectos/${proyectoId}/kanban`,         icon: <IconKanban /> },
        { label: 'Progreso',       to: `/estudiante/proyectos/${proyectoId}/progreso`,       icon: <IconProgress /> },
        { label: 'Autoevaluación', to: `/estudiante/proyectos/${proyectoId}/autoevaluacion`, icon: <IconSelf /> },
        { label: 'Coevaluación',   to: `/estudiante/proyectos/${proyectoId}/coevaluacion`,   icon: <IconPeers /> },
        { label: 'Historial',      to: `/estudiante/proyectos/${proyectoId}/historial`,      icon: <IconHistory /> },
    ]

    const LIDER_ITEMS = [
        { label: 'Dashboard Equipo',     to: `/estudiante/proyectos/${proyectoId}/equipo/dashboard`,   icon: <IconTarget /> },
        { label: 'Distribución',         to: `/estudiante/proyectos/${proyectoId}/equipo/distribucion`, icon: <IconDistribute /> },
        { label: 'Responsables',         to: `/estudiante/proyectos/${proyectoId}/equipo/responsables`, icon: <IconAssign /> },
    ]

    return (
        <>
            {/* Header */}
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
                    <h2 className="text-[14px] font-bold text-[#191c1d] leading-tight mb-0.5 line-clamp-2">{proyectoNombre || 'Proyecto'}</h2>
                    <p className="text-[11px] text-[#9ba7ae]">{periodoNombre || 'Sin periodo'}</p>
                </div>
            )}

            {/* Navegación */}
            <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
                {!collapsed && (
                    <Link
                        to="/estudiante/dashboard"
                        onClick={onNavClick}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-semibold text-[#9ba7ae] tracking-[0.6px] uppercase hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-all mb-1 truncate">
                        <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3 flex-shrink-0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                        <span className="truncate">Inicio</span>
                    </Link>
                )}
                {collapsed && (
                    <Link to="/estudiante/dashboard" onClick={onNavClick}
                        title="← Inicio"
                        className="flex items-center justify-center w-full py-2 rounded-xl text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-all mb-1">
                        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                    </Link>
                )}

                {!collapsed && (
                    <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">Proyecto</p>
                )}

                {NAV_ITEMS.map(({ label, to, icon }) => (
                    <NavLink key={to} to={to} className={navLinkClass} title={collapsed ? label : undefined} onClick={onNavClick}>
                        <span className="flex-shrink-0">{icon}</span>
                        {!collapsed && <span>{label}</span>}
                    </NavLink>
                ))}

                {/* Compañeros para coevaluación */}
                {!collapsed && esCoevaluacion && companeros.length > 0 && (
                    <div className="mt-3">
                        <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5">
                            Equipo
                        </p>
                        {companeros.map(c => {
                            const seleccionado = selectedEvaluadoId === c.id
                            return (
                                <button
                                    key={c.id}
                                    onClick={() => { onSelectEvaluado(c.id); onNavClick?.() }}
                                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-all ${
                                        seleccionado
                                            ? 'bg-[#fff1f0] text-[#d32f2f]'
                                            : 'text-[#4c616c] hover:bg-[#f0f2f3]'
                                    }`}>
                                    <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-[12px] font-bold ${
                                        seleccionado ? 'bg-[#ffdad6] text-[#af101a]' : 'bg-[#e1e3e4] text-[#4c616c]'
                                    }`}>
                                        {c.nombre?.[0]?.toUpperCase() ?? '?'}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-[12.5px] font-semibold truncate">{c.nombre}</p>
                                        {c.yaEvaluado && (
                                            <p className="text-[10px] text-[#2e7d32]">✓ Evaluado</p>
                                        )}
                                    </div>
                                </button>
                            )
                        })}
                    </div>
                )}

                {/* Sección exclusiva para Líder de Equipo */}
                {esLider && (
                    <div className="mt-3">
                        {!collapsed && (
                            <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">
                                Gestión de Equipo
                            </p>
                        )}
                        {collapsed && <div className="h-px bg-[#e1e3e4] mx-2 my-2" />}
                        {LIDER_ITEMS.map(({ label, to, icon }) => (
                            <NavLink key={to} to={to} className={navLinkClass} title={collapsed ? label : undefined} onClick={onNavClick}>
                                <span className="flex-shrink-0">{icon}</span>
                                {!collapsed && <span>{label}</span>}
                            </NavLink>
                        ))}
                    </div>
                )}
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

// ── Layout principal ──────────────────────────────────────────────────────────

export default function ProyectoEstudianteLayout() {
    const navigate  = useNavigate()
    const location  = useLocation()
    const { proyectoId } = useParams()

    const [user,          setUser]          = useState(() => session.getUser())
    const [collapsed,     setCollapsed]     = useState(false)
    const [mobileOpen,    setMobileOpen]    = useState(false)
    const [loggingOut,    setLoggingOut]    = useState(false)
    const [topbarMenuOpen, setTopbarMenuOpen] = useState(false)

    const [proyecto,      setProyecto]      = useState(null)
    const [companeros,    setCompaneros]    = useState([])
    const [coevals,       setCoevals]       = useState([])
    const [selectedEvaluadoId, setSelectedEvaluadoId] = useState(null)

    const esCoevaluacion = location.pathname.includes('/coevaluacion')

    useEffect(() => {
        const refresh = () => setUser(session.getUser())
        window.addEventListener('user-updated', refresh)
        return () => window.removeEventListener('user-updated', refresh)
    }, [])

    useEffect(() => {
        if (proyectoId) cargarProyecto()
    }, [proyectoId])

    async function cargarProyecto() {
        try {
            const p = await estudianteProyectosApi.obtener(proyectoId)
            setProyecto(p)
            if (p.equipo?.miembros) {
                await cargarCompaneros(p)
            }
        } catch { }
    }

    // Recibe el objeto proyecto completo (con equipo.miembros ya cargados)
    async function cargarCompaneros(proyectoData) {
        try {
            const coevsData = await coevaluacionApi.listar(proyectoId).catch(() => [])

            const yo  = session.getUser()
            // proyecto.equipo.miembros viene de EquipoDetalleSerializer → MiembroDetalleSerializer
            // Campos: usuario_id, nombre_completo, rol_interno, estado
            const miembros = proyectoData?.equipo?.miembros ?? []

            const companerosFiltrados = miembros
                .filter(m => m.usuario_id !== yo?.id)
                .map(m => ({
                    id:     m.usuario_id,
                    nombre: m.nombre_completo,
                }))

            const coevsArr = Array.isArray(coevsData) ? coevsData : (coevsData.results ?? [])
            setCoevals(coevsArr)

            const evaluadosIds = coevsArr
                .filter(c => c.id_evaluador === yo?.id)
                .map(c => c.id_evaluado)

            const conEstado = companerosFiltrados.map(c => ({
                ...c,
                yaEvaluado: evaluadosIds.includes(c.id),
            }))

            setCompaneros(conEstado)
            const primero = conEstado.find(c => !c.yaEvaluado) ?? conEstado[0]
            if (primero) setSelectedEvaluadoId(primero.id)
        } catch { }
    }

    async function handleLogout() {
        setLoggingOut(true)
        try { await authApi.logout() } catch { }
        finally {
            setLoggingOut(false)
            navigate('/login', { replace: true })
        }
    }

    const sidebarW = collapsed ? 'w-[68px]' : 'w-[240px]'

    const outletCtx = {
        proyectoId,
        proyecto,
        companeros,
        selectedEvaluadoId,
        setSelectedEvaluadoId,
        coevals,
        recargarCompaneros: () => proyecto && cargarCompaneros(proyecto),
    }

    return (
        <div className="flex h-screen bg-[#f8f9fa] overflow-hidden" style={{ fontFamily: "'Manrope', sans-serif" }}
            onClick={() => { setTopbarMenuOpen(false); setMobileOpen(false) }}>

            {mobileOpen && (
                <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
            )}

            {/* Sidebar desktop */}
            <aside className={`hidden lg:flex ${sidebarW} flex-shrink-0 flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>
                <SidebarContent collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)}
                    loggingOut={loggingOut} handleLogout={handleLogout} onNavClick={undefined}
                    proyectoId={proyectoId}
                    proyectoNombre={proyecto?.nombre}
                    periodoNombre={proyecto?.periodo ?? proyecto?.id_curso?.periodo ?? ''}
                    esCoevaluacion={esCoevaluacion}
                    companeros={companeros}
                    selectedEvaluadoId={selectedEvaluadoId}
                    onSelectEvaluado={setSelectedEvaluadoId}
                    user={user} />
            </aside>

            {/* Sidebar móvil */}
            <aside className={`lg:hidden fixed top-0 left-0 h-full w-[260px] flex flex-col bg-white border-r border-[#e1e3e4] z-40 transition-transform duration-200 ease-in-out ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
                onClick={e => e.stopPropagation()}>
                <SidebarContent collapsed={false} onCollapse={null}
                    loggingOut={loggingOut} handleLogout={handleLogout}
                    onNavClick={() => setMobileOpen(false)}
                    proyectoId={proyectoId}
                    proyectoNombre={proyecto?.nombre}
                    periodoNombre={proyecto?.periodo ?? proyecto?.id_curso?.periodo ?? ''}
                    esCoevaluacion={esCoevaluacion}
                    companeros={companeros}
                    selectedEvaluadoId={selectedEvaluadoId}
                    onSelectEvaluado={id => { setSelectedEvaluadoId(id); setMobileOpen(false) }}
                    user={user} />
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
                                        : <span className="text-[12px] font-bold text-[#af101a]">{user.nombre?.[0]?.toUpperCase() ?? 'E'}</span>
                                    }
                                </div>
                                <div className="hidden sm:block text-left">
                                    <p className="text-[13px] font-semibold text-[#191c1d] leading-tight">{user.nombre ?? 'Estudiante'}</p>
                                    <p className="text-[11px] text-[#9ba7ae] leading-tight">
                                        {user?.tipo_rol === 'lider_equipo' ? 'Líder de Equipo' : 'Estudiante'}
                                    </p>
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
                    <Outlet context={outletCtx} />
                </div>
            </main>
        </div>
    )
}