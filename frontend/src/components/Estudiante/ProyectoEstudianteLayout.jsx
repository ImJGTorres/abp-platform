import { useState, useEffect } from 'react'
import { Outlet, useNavigate, Link, useParams, useLocation, useMatch } from 'react-router-dom'
import { authApi, session } from '../../services/api'
import { estudianteProyectosApi, coevaluacionApi } from '../../services/estudianteApi'
import BarraSuperior from '../Compartidos/BarraSuperior'
import MenuLateral from '../Compartidos/MenuLateral'

// ── Icons ─────────────────────────────────────────────────────────────────────

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

// ── Sidebar Content ───────────────────────────────────────────────────────────

function SidebarContent({
    collapsed, onCollapse, loggingOut, handleLogout, onNavClick,
    proyectoId, proyectoNombre, periodoNombre,
    esCoevaluacion, companeros, selectedEvaluadoId, onSelectEvaluado,
    user,
}) {
    const esLider = user?.tipo_rol === 'lider_equipo'
    // Volver a la lista de proyectos de la zona del usuario
    const rutaMisProyectos = esLider ? '/lider/proyectos' : '/estudiante/proyectos'

    const base = `/estudiante/proyectos/${proyectoId}`

    // Ítems del proyecto
    const itemsProyecto = [
        { label: 'Actividades',    to: `${base}/actividades`,    icon: 'actividadesEst' },
        { label: 'Kanban',         to: `${base}/kanban`,         icon: 'kanbanEst' },
        { label: 'Progreso',       to: `${base}/progreso`,       icon: 'progresoEst' },
        { label: 'Autoevaluación', to: `${base}/autoevaluacion`, icon: 'autoevalEst' },
        { label: 'Coevaluación',   to: `${base}/coevaluacion`,   icon: 'coevalEst' },
        { label: 'Historial',      to: `${base}/historial`,      icon: 'historial' },
    ]

    // Gestión del equipo (solo líder)
    const itemsLider = [
        { label: 'Dashboard Equipo', to: `${base}/equipo/dashboard`,    icon: 'dianaEst' },
        { label: 'Distribución',     to: `${base}/equipo/distribucion`, icon: 'repartir' },
        { label: 'Responsables',     to: `${base}/equipo/responsables`, icon: 'asignar' },
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
                        to={rutaMisProyectos}
                        onClick={onNavClick}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-semibold text-[#9ba7ae] tracking-[0.6px] uppercase hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-all mb-1 truncate">
                        <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3 flex-shrink-0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                        <span className="truncate">Mis proyectos</span>
                    </Link>
                )}
                {collapsed && (
                    <Link to={rutaMisProyectos} onClick={onNavClick}
                        title="← Mis proyectos"
                        className="flex items-center justify-center w-full py-2 rounded-xl text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-all mb-1">
                        <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M10 3L5 8l5 5" /></svg>
                    </Link>
                )}

                {!collapsed && (
                    <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">Proyecto</p>
                )}

                <MenuLateral rol="estudiante" mostrarFijos={false} itemsContextuales={itemsProyecto} collapsed={collapsed} onNavClick={onNavClick} />

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
                        <MenuLateral rol="lider_equipo" mostrarFijos={false} itemsContextuales={itemsLider} collapsed={collapsed} onNavClick={onNavClick} />
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
            onClick={() => setMobileOpen(false)}>

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
                <BarraSuperior user={user} menuAbierto={mobileOpen} onToggleMenu={() => setMobileOpen(o => !o)}
                    onLogout={handleLogout} loggingOut={loggingOut} />

                <div className="flex-1 overflow-hidden flex flex-col">
                    <Outlet context={outletCtx} />
                </div>
            </main>
        </div>
    )
}