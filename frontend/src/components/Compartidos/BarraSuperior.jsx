import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { buildMediaUrl } from '../../services/api'
import AlertasBell from '../AlertasBell'


const NOMBRE_ROL = {
    administrador: 'Administrador',
    director: 'Director',
    docente: 'Docente',
    lider_equipo: 'Líder de Equipo',
    estudiante: 'Estudiante',
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

function IconLogout() {
    return (
        <svg viewBox="0 0 20 20" fill="none" className="w-5 h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 15l4-5-4-5" /><path d="M17 10H7" /><path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3" />
        </svg>
    )
}

/**
 * @param user          usuario de la sesión ({ nombre, tipo_rol, foto_perfil })
 * @param menuAbierto   estado del menú lateral en móvil
 * @param onToggleMenu  abre/cierra el menú lateral en móvil
 * @param onLogout      cierra la sesión
 * @param loggingOut    true mientras se cierra la sesión
 */
export default function BarraSuperior({ user, menuAbierto, onToggleMenu, onLogout, loggingOut }) {
    const [menuUsuario, setMenuUsuario] = useState(false)
    const refUsuario = useRef(null)

    // Cierra el menú de usuario al hacer clic fuera de él
    useEffect(() => {
        if (!menuUsuario) return
        function alHacerClic(e) {
            if (refUsuario.current && !refUsuario.current.contains(e.target)) setMenuUsuario(false)
        }
        document.addEventListener('mousedown', alHacerClic)
        return () => document.removeEventListener('mousedown', alHacerClic)
    }, [menuUsuario])

    const rol = user?.tipo_rol
    const conNotificaciones = rol === 'estudiante' || rol === 'lider_equipo'

    return (
        <header
            className="h-[60px] flex-shrink-0 bg-white border-b border-[#e1e3e4] flex items-center px-4 sm:px-6 gap-4"
            style={{ fontFamily: "'Manrope', sans-serif" }}
        >
            {onToggleMenu && (
                <button
                    className="lg:hidden flex items-center justify-center w-9 h-9 rounded-xl hover:bg-[#f0f2f3] transition-colors text-[#4c616c]"
                    onClick={e => { e.stopPropagation(); onToggleMenu() }}
                    aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
                >
                    {menuAbierto ? <IconX /> : <IconMenu />}
                </button>
            )}

            <div className="flex-1" />

            {user && <AlertasBell pollingMinutos={5} incluirNotificaciones={conNotificaciones} />}

            {user && (
                <div className="relative" ref={refUsuario}>
                    <button
                        onClick={e => { e.stopPropagation(); setMenuUsuario(o => !o) }}
                        className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
                    >
                        <div className="w-8 h-8 rounded-full bg-[#ffdad6] flex items-center justify-center overflow-hidden">
                            {user.foto_perfil
                                ? <img src={buildMediaUrl(user.foto_perfil)} alt="" className="w-full h-full object-cover" onError={e => { e.target.style.display = 'none' }} />
                                : <span className="text-[12px] font-bold text-[#af101a]">{user.nombre?.[0]?.toUpperCase() ?? '?'}</span>
                            }
                        </div>
                        <div className="hidden sm:block text-left">
                            <p className="text-[13px] font-semibold text-[#191c1d] leading-tight">{user.nombre ?? NOMBRE_ROL[rol] ?? 'Usuario'}</p>
                            <p className="text-[11px] text-[#9ba7ae] leading-tight">{NOMBRE_ROL[rol] ?? ''}</p>
                        </div>
                    </button>
                    {menuUsuario && (
                        <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-[#e1e3e4] shadow-lg overflow-hidden z-30">
                            <Link
                                to="/perfil"
                                onClick={() => setMenuUsuario(false)}
                                className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#191c1d] hover:bg-[#f0f2f3] transition-colors"
                            >
                                <IconProfile />Mi perfil
                            </Link>
                            <button
                                onClick={() => { setMenuUsuario(false); onLogout() }}
                                disabled={loggingOut}
                                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-[#ba1a1a] hover:bg-[#fff1f0] transition-colors disabled:opacity-60"
                            >
                                <IconLogout />{loggingOut ? 'Cerrando...' : 'Cerrar sesión'}
                            </button>
                        </div>
                    )}
                </div>
            )}
        </header>
    )
}
