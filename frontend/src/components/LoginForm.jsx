// Componente React de login

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, rutaPorRol } from '../services/api'

export default function LoginForm() {
    const navigate = useNavigate()

    const [form, setForm] = useState({ correo: '', contrasena: '' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [verPass, setVerPass] = useState(false)

    //Handlers

    function handleChange(e) {
        const { name, value } = e.target
        setForm(prev => ({ ...prev, [name]: value }))
        setError('')  // limpiar error al escribir
    }

    async function handleSubmit(e) {
        e.preventDefault()

        if (!form.correo.trim() || !form.contrasena) {
            setError('Completa todos los campos.')
            return
        }

        setLoading(true)
        setError('')

        try {
            // authApi.login() guarda tokens y devuelve usuario con tipo_rol
            const user = await authApi.login(form.correo.trim().toLowerCase(), form.contrasena)

            // Redirección según tipo_rol del JWT
            navigate(rutaPorRol(user.tipo_rol), { replace: true })

        } catch (err) {
            // Mensajes claros por tipo de error

            if (err?.type === 'network') {
                setError('No se pudo conectar con el servidor. Verifica tu conexión.')
                return
            }

            if (err?.status === 401) {
                const msg = err?.data?.detail?.toLowerCase()

                if (msg?.includes('inactivo')) {
                    setError('Tu cuenta está inactiva. Contacta al administrador.')
                } else {
                    setError('Credenciales inválidas, por favor intente de nuevo.')
                }
                return
            }

            setError('Error inesperado. Intenta de nuevo.')

        } finally {
            setLoading(false)
        }
    }

    //Render

    return (
        <div className="relative min-h-screen bg-[#f8f9fa] flex items-center justify-center
                    px-6 py-8 overflow-hidden">

            {/* Fondos decorativos  */}
            <div
                className="pointer-events-none absolute rounded-full bg-[#ffdad6] opacity-20"
                style={{ width: 600, height: 600, top: -200, left: -200, filter: 'blur(60px)' }}
            />
            <div
                className="pointer-events-none absolute rounded-full bg-[#cfe6f2] opacity-20"
                style={{ width: 600, height: 600, bottom: -200, right: -200, filter: 'blur(60px)' }}
            />
            {/* Rombo superior derecha */}
            <div
                className="pointer-events-none absolute border-4 border-[#4c616c] rounded-[32px] rotate-45 opacity-10"
                style={{ width: 120, height: 120, top: '12%', right: '8%' }}
            />
            {/* Círculo inferior izquierda */}
            <div
                className="pointer-events-none absolute border-4 border-[#af101a] rounded-full opacity-10"
                style={{ width: 80, height: 80, bottom: '12%', left: '8%' }}
            />

            {/* Contenedor central */}
            <div className="relative z-10 flex flex-col items-center gap-8 w-full max-w-[440px]">

                {/* Marca  */}
                <div className="flex flex-col items-center gap-2 w-full">
                    {/* Ícono logo rojo */}
                    <div className="relative flex items-center justify-center w-14 h-14 bg-[#d32f2f] rounded-2xl shadow-lg">
                        <svg viewBox="0 0 24 24" className="w-10 h-9 text-white" fill="currentColor">
                            <path d="M12 2L2 7l10 5 10-5-10-5z" />
                            <path d="M6 10v4c0 2.5 3.5 4 6 4s6-1.5 6-4v-4l-6 3-6-3z" opacity="0.9" />
                            <path d="M22 7v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            <circle cx="22" cy="14" r="1" fill="currentColor" />
                        </svg>
                    </div>

                    {/* Título */}
                    <h1
                        className="text-[32px] font-extrabold text-[#191c1d] tracking-tight text-center"
                        style={{ fontFamily: "'Manrope', sans-serif" }}
                    >
                        Projex ABP
                    </h1>
                </div>

                {/* Card principal */}
                <div className="w-full bg-white rounded-[28px] shadow-[0_12px_40px_rgba(25,28,29,0.08)]
                        px-10 py-10">
                    <div className="flex flex-col gap-7">

                        {/* Encabezado del formulario */}
                        <div>
                            <h2
                                className="text-[22px] font-bold text-[#191c1d] mb-1"
                                style={{ fontFamily: "'Manrope', sans-serif" }}
                            >
                                Bienvenido
                            </h2>
                            <p className="text-[13px] text-[#5b403d]">
                                Por favor ingrese sus credenciales para acceder.
                            </p>
                        </div>

                        {/*  Formulario  */}
                        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">

                            {/* Campo Email */}
                            <div className="flex flex-col gap-1.5">
                                <label
                                    htmlFor="correo"
                                    className="text-[13px] font-semibold text-[#191c1d] pl-1"
                                >
                                    Email
                                </label>
                                <div className="relative">
                                    {/* Ícono email */}
                                    <svg
                                        className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(91,64,61,0.5)] pointer-events-none"
                                        viewBox="0 0 16 16" fill="none"
                                    >
                                        <rect x="1" y="3" width="14" height="10" rx="2"
                                            stroke="currentColor" strokeWidth="1.3" />
                                        <path d="M1 6l7 4 7-4" stroke="currentColor"
                                            strokeWidth="1.3" strokeLinecap="round" />
                                    </svg>
                                    <input
                                        id="correo"
                                        name="correo"
                                        type="email"
                                        placeholder="nombre@ejemplo.com"
                                        value={form.correo}
                                        onChange={handleChange}
                                        autoComplete="email"
                                        className="w-full h-[52px] bg-[#e8eaeb] rounded-xl pl-11 pr-4 text-[14px] text-[#191c1d] placeholder:text-[rgba(91,64,61,0.45)] outline-none focus:ring-2 focus:ring-[#d32f2f]/50 transition-shadow duration-150"
                                    />
                                </div>
                            </div>

                            {/* Campo Contraseña */}
                            <div className="flex flex-col gap-1.5">
                                <div className="flex items-center justify-between pl-1">
                                    <label htmlFor="contrasena"
                                        className="text-[13px] font-semibold text-[#191c1d]">
                                        Contraseña
                                    </label>
                                    <button
                                        type="button"
                                        onClick={() => navigate('/olvidar-contrasena')}
                                        className="text-[11px] font-semibold text-[#af101a] hover:underline"
                                    >
                                        ¿Olvidó su contraseña?
                                    </button>
                                </div>
                                <div className="relative">
                                    {/* Ícono candado */}
                                    <svg
                                        className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(91,64,61,0.5)] pointer-events-none"
                                        viewBox="0 0 16 16" fill="none"
                                    >
                                        <rect x="2.5" y="7" width="11" height="8" rx="1.5"
                                            stroke="currentColor" strokeWidth="1.3" />
                                        <path d="M5 7V5a3 3 0 016 0v2"
                                            stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                                    </svg>
                                    <input
                                        id="contrasena"
                                        name="contrasena"
                                        type={verPass ? 'text' : 'password'}
                                        placeholder="••••••••"
                                        value={form.contrasena}
                                        onChange={handleChange}
                                        autoComplete="current-password"
                                        className="w-full h-[52px] bg-[#e8eaeb] rounded-xl pl-11 pr-12
                            text-[14px] text-[#191c1d] placeholder:text-[rgba(91,64,61,0.45)]
                            outline-none focus:ring-2 focus:ring-[#d32f2f]/50
                            transition-shadow duration-150
                            [&::-ms-reveal]:hidden [&::-webkit-credentials-auto-fill-button]:hidden"
                                    />
                                    {/* Toggle ver contraseña */}
                                    <button
                                        type="button"
                                        onClick={() => setVerPass(v => !v)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-[rgba(91,64,61,0.5)] hover:text-[#5b403d] transition-colors"
                                        aria-label={verPass ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                    >
                                        {verPass ? (
                                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" strokeWidth="2"
                                                strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8 a18.45 18.45 0 015.06-5.94" />
                                                <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8
                                a18.5 18.5 0 01-2.16 3.19"/>
                                                <line x1="1" y1="1" x2="23" y2="23" />
                                            </svg>
                                        ) : (
                                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" strokeWidth="2"
                                                strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                <circle cx="12" cy="12" r="3" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* ── Banner de error — HU-002 ST-11 ──────────────────────── */}
                            {error && (
                                <div
                                    role="alert"
                                    className="flex items-center gap-2.5 bg-[rgba(255,218,214,0.5)] border border-[#f5c4b3] rounded-xl px-4 py-3"
                                >
                                    <svg className="w-4 h-4 text-[#ba1a1a] flex-shrink-0"
                                        viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" clipRule="evenodd"
                                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" />
                                    </svg>
                                    <p className="text-[13px] font-medium text-[#ba1a1a] leading-5">{error}</p>
                                </div>
                            )}

                            {/* ── Botón Iniciar sesión  */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="relative w-full h-[52px] rounded-xl flex items-center justify-center
                        gap-2 font-bold text-[15px] text-white mt-1 disabled:opacity-70 disabled:cursor-not-allowed
                        active:scale-[0.98] transition-transform duration-100"
                                style={{
                                    background: 'linear-gradient(172deg, #af101a 0%, #d32f2f 100%)',
                                    boxShadow: '0 8px 20px -4px rgba(175,16,26,0.35)',
                                    fontFamily: "'Manrope', sans-serif",
                                }}
                            >
                                {loading ? (
                                    <>
                                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10"
                                                stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor"
                                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        <span>Ingresando...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Iniciar sesión</span>
                                        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
                                            <path d="M3 8h10M9 4l4 4-4 4"
                                                stroke="currentColor" strokeWidth="1.8"
                                                strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                    </>
                                )}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex flex-col items-center gap-3 pb-4">
                    <p className="text-[11px] text-[#5b403d] text-center leading-relaxed">
                        © 2026 Academic Management System.
                    </p>
                    <div className="flex gap-5">
                        {['Privacidad', 'Términos', 'Soporte'].map(link => (
                            <button key={link} type="button"
                                className="text-[11px] text-[#5b403d] hover:underline">
                                {link}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}