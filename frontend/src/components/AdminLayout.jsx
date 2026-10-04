import { useState, useEffect } from 'react'
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom'
import { authApi, session } from '../services/api'
import MenuLateral from './Compartidos/MenuLateral'
import BarraSuperior from './Compartidos/BarraSuperior'

function IconChart() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="11" width="4" height="7" rx="1" />
      <rect x="8" y="6" width="4" height="12" rx="1" />
      <rect x="14" y="2" width="4" height="16" rx="1" />
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

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState(() => session.getUser())
  const [collapsed, setCollapsed] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

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

  // Contenido del menú lateral; se usa en escritorio y en el panel móvil
  function contenidoSidebar(colapsado, alColapsar, alNavegar) {
    return (
      <>
        {/* Marca + Collapse */}
        {colapsado ? (
          <div className="flex items-center justify-center h-[60px] border-b border-[#e1e3e4] flex-shrink-0">
            <button
              onClick={alColapsar}
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
            {alColapsar && (
              <button
                onClick={alColapsar}
                className="ml-auto flex items-center justify-center w-7 h-7 rounded-lg text-[#9ba7ae] hover:bg-[#f0f2f3] hover:text-[#4c616c] transition-colors"
                title="Colapsar menú"
              >
                <IconChevronLeft />
              </button>
            )}
          </div>
        )}

        {/* Navegación */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
          {!colapsado && (
            <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-1">
              Administración
            </p>
          )}
          <MenuLateral rol="administrador" collapsed={colapsado} onNavClick={alNavegar} />

          {/* Sección Director */}
          {!colapsado && (
            <p className="text-[10px] font-semibold text-[#9ba7ae] tracking-[0.8px] uppercase px-3 pb-1.5 pt-4">Director</p>
          )}
          {colapsado && <div className="my-2 border-t border-[#f0f2f3]" />}
          <Link
            to="/director"
            onClick={alNavegar}
            title={colapsado ? 'Director' : undefined}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-150 select-none cursor-pointer ${
              location.pathname.startsWith('/director')
                ? 'bg-[#d32f2f] text-white shadow-[0_4px_12px_rgba(211,47,47,0.25)]'
                : 'text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d]'
            }`}
          >
            <span className="flex-shrink-0"><IconChart /></span>
            {!colapsado && <span>Director</span>}
          </Link>
        </nav>

        {/* Perfil + Logout */}
        <div className="border-t border-[#e1e3e4] p-2 flex-shrink-0">
          <Link to="/perfil" onClick={alNavegar}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#4c616c] hover:bg-[#f0f2f3] hover:text-[#191c1d] transition-colors">
            <span className="flex-shrink-0"><IconProfile /></span>
            {!colapsado && <span>Mi perfil</span>}
          </Link>
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60">
            <span className="flex-shrink-0"><IconLogout /></span>
            {!colapsado && <span>{loggingOut ? 'Cerrando...' : 'Cerrar sesión'}</span>}
          </button>
        </div>
      </>
    )
  }

  return (
    <div
      className="flex h-screen bg-[#f8f9fa] overflow-hidden"
      style={{ fontFamily: "'Manrope', sans-serif" }}
      onClick={() => setMobileOpen(false)}
    >

      {/* ── Overlay móvil ─────────────────────────────────────────────────── */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      {/* ── Sidebar escritorio ────────────────────────────────────────────── */}
      <aside className={`hidden lg:flex ${sidebarW} flex-shrink-0 flex-col bg-white border-r border-[#e1e3e4] transition-[width] duration-200 ease-in-out z-20 relative`}>
        {contenidoSidebar(collapsed, () => setCollapsed(c => !c), undefined)}
      </aside>

      {/* ── Sidebar móvil (drawer) ────────────────────────────────────────── */}
      <aside className={`lg:hidden fixed top-0 left-0 h-full w-[260px] flex flex-col bg-white border-r border-[#e1e3e4] z-40 transition-transform duration-200 ease-in-out ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
        onClick={e => e.stopPropagation()}>
        {contenidoSidebar(false, null, () => setMobileOpen(false))}
      </aside>

      {/* ── Área de contenido ─────────────────────────────────────────────── */}
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