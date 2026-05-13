import { useState, useEffect } from 'react'
import { NavLink, Outlet, useNavigate, Link } from 'react-router-dom'
import { authApi, session, buildMediaUrl } from '../services/api'

function IconUsers() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 7a3 3 0 11-6 0 3 3 0 016 0z" />
      <path d="M3 17a7 7 0 0114 0" />
    </svg>
  )
}

function IconSettings() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="2.5" />
      <path d="M10 2v1.5M10 16.5V18M2 10h1.5M16.5 10H18M4.22 4.22l1.06 1.06M14.72 14.72l1.06 1.06M4.22 15.78l1.06-1.06M14.72 5.28l1.06-1.06" />
    </svg>
  )
}

function IconCalendar() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="16" height="14" rx="2" />
      <path d="M6 2v3M14 2v3M2 8h16" />
    </svg>
  )
}

function IconShield() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 2l7 3v5c0 4-3 6.5-7 8-4-1.5-7-4-7-8V5l7-3z" />
    </svg>
  )
}

function IconFileText() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 4V3a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v1" />
      <path d="M10 13V8a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v5" />
      <path d="M6 10V7a1 1 0 00-1-1 2 2 0 00-2 0 1 1 0 00-1 1v3" />
      <path d="M18 9v4a2 2 0 01-2 2 2 2 0 01-2-2v-4" />
      <path d="M2 10h16M2 14h16" />
    </svg>
  )
}

function IconBook() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a2 2 0 012 2v11a2 2 0 00-2 2H2z" />
      <path d="M18 3h-6a2 2 0 00-2 2v11a2 2 0 012 2h6z" />
    </svg>
  )
}

function IconLogout() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 15l4-5-4-5" />
      <path d="M17 10H7" />
      <path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3" />
    </svg>
  )
}

function IconProfile() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="7" r="3" />
      <path d="M3 17a7 7 0 0114 0" />
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

const NAV_ITEMS = [
  { label: 'Usuarios', to: '/admin/registro', icon: <IconUsers /> },
  { label: 'Cursos', to: '/admin/cursos', icon: <IconBook /> },
  { label: 'Configuración', to: '/admin/configuracion', icon: <IconSettings /> },
  { label: 'Períodos', to: '/admin/periodos', icon: <IconCalendar /> },
  { label: 'Bitácoras', to: '/admin/bitacoras', icon: <IconFileText /> },
  { label: 'Roles', to: '/admin/roles', icon: <IconShield /> },
]

function navLinkClass({ isActive }) {
  const base = 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer'
  return isActive
    ? `${base} bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.30)]`
    : `${base} text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]`
}

export default function AdminLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => session.getUser())
  const [collapsed, setCollapsed] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [topbarMenuOpen, setTopbarMenuOpen] = useState(false)

  useEffect(() => {
    const refresh = () => setUser(session.getUser())
    window.addEventListener('user-updated', refresh)
    return () => window.removeEventListener('user-updated', refresh)
  }, [])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await authApi.logout()
    } catch {
      // session.clear() ya fue llamado dentro de authApi.logout()
    } finally {
      setLoggingOut(false)
      navigate('/login', { replace: true })
    }
  }

  const sidebarW = collapsed ? 'w-[68px]' : 'w-[220px]'

  return (
    <div
      className="flex h-screen bg-[#f8f9fa] overflow-hidden"
      style={{ fontFamily: "'Manrope', sans-serif" }}
      onClick={() => setTopbarMenuOpen(false)}
    >

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={`${sidebarW} flex-shrink-0 flex flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>

        {/* Marca + Collapse */}
        {collapsed ? (
          <div className="flex items-center justify-center h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
            <button
              onClick={() => setCollapsed(c => !c)}
              className="flex items-center justify-center w-8 h-8 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
              title="Expandir menú"
            >
              <IconChevronRight />
            </button>
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
            <span className="text-[15px] font-extrabold text-[#191c1d] tracking-tight whitespace-nowrap">
              Projex ABP
            </span>
            <button
              onClick={() => setCollapsed(c => !c)}
              className="ml-auto flex items-center justify-center w-7 h-7 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
              title="Colapsar menú"
            >
              <IconChevronLeft />
            </button>
          </div>
        )}

        {/* Navegación */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
          {!collapsed && (
            <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">
              Administración
            </p>
          )}
          {NAV_ITEMS.map(({ label, to, icon }) => (
            <NavLink key={to} to={to} className={navLinkClass} title={collapsed ? label : undefined}>
              <span className="flex-shrink-0">{icon}</span>
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Perfil + Logout */}
        <div className="border-t border-[#e1e3e4] p-2 flex-shrink-0">
          <Link to="/perfil"
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d] transition-colors">
            <span className="flex-shrink-0"><IconProfile /></span>
            {!collapsed && <span>Mi perfil</span>}
          </Link>
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60">
            <span className="flex-shrink-0"><IconLogout /></span>
            {!collapsed && <span>{loggingOut ? 'Cerrando...' : 'Cerrar sesión'}</span>}
          </button>
        </div>
      </aside>

      {/* ── Área de contenido ─────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Topbar */}
        <header className="h-[60px] flex-shrink-0 bg-white border-b border-[#e1e3e4] flex items-center px-6 gap-4">
          <div className="flex-1" />
          {user && (
            <div className="relative">
              <button
                onClick={e => { e.stopPropagation(); setTopbarMenuOpen(o => !o) }}
                className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
              >
                <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center overflow-hidden">
                  {user.foto_perfil
                    ? <img src={buildMediaUrl(user.foto_perfil)} alt="" className="w-full h-full object-cover" onError={e => { e.target.style.display = 'none' }} />
                    : <span className="text-[12px] font-bold text-[#af101a]">{user.nombre?.[0]?.toUpperCase() ?? 'A'}</span>
                  }
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-[13px] font-semibold text-[#191c1d] leading-tight">
                    {user.nombre ?? 'Administrador'}
                  </p>
                  <p className="text-[11px] text-[#9ba7ae] leading-tight capitalize">
                    {user.tipo_rol?.replace('_', ' ') ?? 'admin'}
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
          <Outlet />
        </div>

      </main>
    </div>
  )
}