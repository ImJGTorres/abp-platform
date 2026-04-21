import { useState } from 'react'
import { NavLink, Outlet, useNavigate, Link } from 'react-router-dom'
import { authApi, session } from '../services/api'

// ── Íconos SVG inline ─────────────────────────────────────────────────────────

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

function IconLogout() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 15l4-5-4-5" />
      <path d="M17 10H7" />
      <path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3" />
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

function IconChevron() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 8l-3 3-3-3" />
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

// ── Ítems del sidebar ─────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { label: 'Usuarios',      to: '/admin/registro',      icon: <IconUsers />    },
  { label: 'Configuración', to: '/admin/configuracion', icon: <IconSettings /> },
  { label: 'Períodos',      to: '/admin/periodos',      icon: <IconCalendar /> },
  { label: 'Bitácoras',     to: '/admin/bitacoras',     icon: <IconFileText /> },
  { label: 'Roles',         to: '/admin/roles',         icon: <IconShield />   },
]

function navLinkClass({ isActive }) {
  const base = 'flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer'
  return isActive
    ? `${base} bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.30)]`
    : `${base} text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]`
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function AdminLayout() {
  const navigate = useNavigate()
  const user = session.getUser()
  const [collapsed, setCollapsed] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

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
    // onClick en el root cierra el menú de usuario al hacer click fuera
    <div
      className="flex h-screen bg-[#f8f9fa] overflow-hidden"
      style={{ fontFamily: "'Manrope', sans-serif" }}
      onClick={() => setUserMenuOpen(false)}
    >

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={`${sidebarW} flex-shrink-0 flex flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>

        {/* Marca */}
        <div className="flex items-center gap-2.5 px-4 h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
          <div className="flex-shrink-0 w-8 h-8 bg-[#d32f2f] rounded-lg flex items-center justify-center shadow-sm">
            <svg viewBox="0 0 28 24" className="w-4 h-3.5 text-white" fill="currentColor">
              <path d="M14 0L28 8v8l-14 8L0 16V8L14 0z" opacity=".3" />
              <path d="M14 3l11 6.5v7L14 23 3 16.5v-7L14 3z" opacity=".5" />
              <path d="M14 7l7 4v4l-7 4-7-4v-4l7-4z" />
            </svg>
          </div>
          {!collapsed && (
            <span className="text-[15px] font-extrabold text-[#191c1d] tracking-tight whitespace-nowrap">
              Projex ABP
            </span>
          )}
        </div>

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

        {/* Usuario + Logout */}
        <div className="border-t border-[#e1e3e4] p-2 flex-shrink-0">
          {!collapsed && user && (
            <div
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-[#f0f2f3] cursor-pointer transition-colors mb-1 relative"
              onClick={e => { e.stopPropagation(); setUserMenuOpen(o => !o) }}
            >
              <div className="w-7 h-7 rounded-full bg-[#ffdad6] flex items-center justify-center flex-shrink-0">
                <span className="text-[11px] font-bold text-[#af101a]">
                  {user.nombre?.[0]?.toUpperCase() ?? 'A'}
                </span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[12px] font-semibold text-[#191c1d] truncate leading-tight">
                  {user.nombre ?? 'Administrador'}
                </p>
                <p className="text-[10px] text-[#9ba7ae] truncate leading-tight capitalize">
                  {user.tipo_rol?.replace('_', ' ') ?? 'admin'}
                </p>
              </div>
              <IconChevron />

              {/* Mini menú */}
              {userMenuOpen && (
                <div className="absolute bottom-full left-0 w-full mb-1 bg-white rounded-xl border border-[#e1e3e4] shadow-lg overflow-hidden z-30">
                  <Link
                    to="/perfil"
                    onClick={e => e.stopPropagation()}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#191c1d] hover:bg-[#f0f2f3] transition-colors"
                  >
                    <IconProfile />
                    Mi perfil
                  </Link>
                  <button
                    onClick={e => { e.stopPropagation(); handleLogout() }}
                    disabled={loggingOut}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60"
                  >
                    <IconLogout />
                    {loggingOut ? 'Cerrando...' : 'Cerrar sesión'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Botón collapse */}
          <button
            onClick={() => setCollapsed(c => !c)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors text-[12px] font-medium"
            title={collapsed ? 'Expandir menú' : 'Colapsar menú'}
          >
            <IconMenu />
            {!collapsed && <span>Colapsar</span>}
          </button>
        </div>
      </aside>

      {/* ── Área de contenido ─────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Topbar */}
        <header className="h-[60px] flex-shrink-0 bg-white border-b border-[#e1e3e4] flex items-center px-6 gap-4">
          <div className="flex-1" />
          {user && (
            <Link to="/perfil" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center">
                <span className="text-[12px] font-bold text-[#af101a]">
                  {user.nombre?.[0]?.toUpperCase() ?? 'A'}
                </span>
              </div>
              <div className="hidden sm:block">
                <p className="text-[13px] font-semibold text-[#191c1d] leading-tight">
                  {user.nombre ?? 'Administrador'}
                </p>
                <p className="text-[11px] text-[#9ba7ae] leading-tight capitalize">
                  {user.tipo_rol?.replace('_', ' ') ?? 'admin'}
                </p>
              </div>
            </Link>
          )}
        </header>

        {/* Contenido — sin padding: cada página gestiona el suyo.
            GestionRoles usa h-screen internamente y necesita este contenedor
            sin padding para no romper su layout de panel lateral. */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <Outlet />
        </div>

      </main>
    </div>
  )
}