import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../services/api'

// ─── Subcomponente: input de contraseña con toggle ────────────────────────────
function PasswordInput({ id, label, value, onChange, error, placeholder = '••••••••' }) {
    const [ver, setVer] = useState(false)
    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor={id} className="text-[13px] font-semibold text-[#191c1d] pl-1">{label}</label>
            <div className="relative">
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(91,64,61,0.5)] pointer-events-none"
                    viewBox="0 0 16 16" fill="none">
                    <rect x="2.5" y="7" width="11" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
                    <path d="M5 7V5a3 3 0 016 0v2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                </svg>
                <input
                    id={id}
                    type={ver ? 'text' : 'password'}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    className={`w-full h-[52px] bg-[#e8eaeb] rounded-xl pl-11 pr-12 text-[14px] text-[#191c1d]
            placeholder:text-[rgba(91,64,61,0.45)] outline-none transition-shadow duration-150
            [&::-ms-reveal]:hidden [&::-webkit-credentials-auto-fill-button]:hidden
            focus:ring-2 ${error ? 'ring-2 ring-[#ba1a1a]/40' : 'focus:ring-[#d32f2f]/50'}`}
                />
                <button type="button" onClick={() => setVer(v => !v)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[rgba(91,64,61,0.5)] hover:text-[#5b403d] transition-colors"
                    aria-label={ver ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
                    {ver ? (
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                            <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                    ) : (
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                        </svg>
                    )}
                </button>
            </div>
            {error && (
                <p className="text-[12px] text-[#ba1a1a] pl-1 flex items-center gap-1">
                    <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 12 12" fill="currentColor">
                        <path fillRule="evenodd" clipRule="evenodd"
                            d="M6 1a5 5 0 100 10A5 5 0 006 1zm0 4a.75.75 0 01.75.75v2a.75.75 0 01-1.5 0v-2A.75.75 0 016 5zm0-1.5a.75.75 0 100-1.5.75.75 0 000 1.5z" />
                    </svg>
                    {error}
                </p>
            )}
        </div>
    )
}

// ─── Pantalla de éxito ────────────────────────────────────────────────────────
function PantallaExito({ navigate }) {
    return (
        <div className="flex flex-col gap-6 items-center text-center">
            <div className="w-16 h-16 rounded-full bg-[#e8f5e9] flex items-center justify-center">
                <svg className="w-8 h-8 text-[#2e7d32]" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                </svg>
            </div>
            <div>
                <h2 className="text-[20px] font-bold text-[#191c1d] mb-2" style={{ fontFamily: "'Manrope', sans-serif" }}>
                    Contraseña actualizada
                </h2>
                <p className="text-[13px] text-[#5b403d] leading-relaxed">
                    Tu contraseña fue cambiada correctamente. Ya puedes iniciar sesión con tu nueva contraseña.
                </p>
            </div>
            <button
                onClick={() => navigate('/login')}
                className="w-full h-[52px] rounded-xl font-bold text-[15px] text-white
          active:scale-[0.98] transition-transform duration-100"
                style={{
                    background: 'linear-gradient(172deg, #af101a 0%, #d32f2f 100%)',
                    boxShadow: '0 8px 20px -4px rgba(175,16,26,0.35)',
                    fontFamily: "'Manrope', sans-serif",
                }}
            >
                Ir al inicio de sesión
            </button>
        </div>
    )
}

// ─── Pantalla token inválido ───────────────────────────────────────────────────
function PantallaTokenInvalido({ navigate }) {
    return (
        <div className="flex flex-col gap-6 items-center text-center">
            <div className="w-16 h-16 rounded-full bg-[#fdf0ef] flex items-center justify-center">
                <svg className="w-8 h-8 text-[#ba1a1a]" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
            </div>
            <div>
                <h2 className="text-[20px] font-bold text-[#191c1d] mb-2" style={{ fontFamily: "'Manrope', sans-serif" }}>
                    Enlace inválido o expirado
                </h2>
                <p className="text-[13px] text-[#5b403d] leading-relaxed">
                    Este enlace de recuperación ya no es válido. Los enlaces expiran a los 30 minutos y solo pueden usarse una vez.
                </p>
            </div>
            <button onClick={() => navigate('/olvidar-contrasena')}
                className="w-full h-[52px] rounded-xl font-bold text-[15px] text-white
          active:scale-[0.98] transition-transform duration-100"
                style={{
                    background: 'linear-gradient(172deg, #af101a 0%, #d32f2f 100%)',
                    boxShadow: '0 8px 20px -4px rgba(175,16,26,0.35)',
                    fontFamily: "'Manrope', sans-serif",
                }}
            >
                Solicitar nuevo enlace
            </button>
            <button onClick={() => navigate('/login')}
                className="text-[13px] text-[#5b403d] hover:underline">
                Volver al inicio de sesión
            </button>
        </div>
    )
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function ResetContrasena() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const token = searchParams.get('token')

    const [form, setForm] = useState({ nueva: '', confirmar: '' })
    const [errores, setErrores] = useState({})
    const [errorGeneral, setErrorGeneral] = useState('')
    const [loading, setLoading] = useState(false)
    const [exitoso, setExitoso] = useState(false)
    const [tokenInvalido, setTokenInvalido] = useState(!token)

    // Si no hay token en la URL, mostrar pantalla de error inmediatamente
    useEffect(() => {
        if (!token) setTokenInvalido(true)
    }, [token])

    const validar = () => {
        const e = {}
        if (!form.nueva) e.nueva = 'La contraseña es obligatoria.'
        else if (form.nueva.length < 8) e.nueva = 'La contraseña debe tener al menos 8 caracteres.'
        if (!form.confirmar) e.confirmar = 'Confirma tu contraseña.'
        else if (form.nueva !== form.confirmar) e.confirmar = 'Las contraseñas no coinciden.'
        return e
    }

    const handleSubmit = async () => {
        const e = validar()
        if (Object.keys(e).length > 0) { setErrores(e); return }

        setLoading(true)
        setErrores({})
        setErrorGeneral('')

        try {
            await authApi.recuperarContrasena({
                token,
                nueva_contrasena: form.nueva,
                confirmar_contrasena: form.confirmar,
            })
            setExitoso(true)
        } catch (err) {
            if (err?.type === 'network') {
                setErrorGeneral('No se pudo conectar con el servidor.')
                return
            }
            // 400 con detail → token inválido/expirado
            if (err?.status === 400) {
                const detail = err?.data?.detail ?? ''
                if (detail.toLowerCase().includes('token')) {
                    setTokenInvalido(true)
                    return
                }
                // Errores de validación de contraseña del serializer
                const eConfirmar = err?.data?.confirmar_contrasena
                const eNueva = err?.data?.nueva_contrasena
                if (eConfirmar || eNueva) {
                    setErrores({
                        confirmar: Array.isArray(eConfirmar) ? eConfirmar[0] : eConfirmar,
                        nueva: Array.isArray(eNueva) ? eNueva[0] : eNueva,
                    })
                    return
                }
            }
            setErrorGeneral('Error inesperado. Intenta de nuevo.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative min-h-screen bg-[#f8f9fa] flex items-center justify-center px-6 py-8 overflow-hidden">
            {/* Fondos decorativos */}
            <div className="pointer-events-none absolute rounded-full bg-[#ffdad6] opacity-20"
                style={{ width: 600, height: 600, top: -200, left: -200, filter: 'blur(60px)' }} />
            <div className="pointer-events-none absolute rounded-full bg-[#cfe6f2] opacity-20"
                style={{ width: 600, height: 600, bottom: -200, right: -200, filter: 'blur(60px)' }} />
            <div className="pointer-events-none absolute border-4 border-[#4c616c] rounded-[32px] rotate-45 opacity-10"
                style={{ width: 120, height: 120, top: '12%', right: '8%' }} />
            <div className="pointer-events-none absolute border-4 border-[#af101a] rounded-full opacity-10"
                style={{ width: 80, height: 80, bottom: '12%', left: '8%' }} />

            <div className="relative z-10 flex flex-col items-center gap-8 w-full max-w-[440px]">
                {/* Marca */}
                <div className="flex flex-col items-center gap-2 w-full">
                    <div className="relative flex items-center justify-center w-14 h-14 bg-[#d32f2f] rounded-2xl shadow-lg">
                        <svg viewBox="0 0 28 24" className="w-7 h-6 text-white" fill="currentColor">
                            <path d="M14 0L28 8v8l-14 8L0 16V8L14 0z" opacity=".3" />
                            <path d="M14 3l11 6.5v7L14 23 3 16.5v-7L14 3z" opacity=".5" />
                            <path d="M14 7l7 4v4l-7 4-7-4v-4l7-4z" />
                        </svg>
                    </div>
                    <h1 className="text-[32px] font-extrabold text-[#191c1d] tracking-tight text-center"
                        style={{ fontFamily: "'Manrope', sans-serif" }}>
                        Projex ABP
                    </h1>
                </div>

                {/* Card */}
                <div className="w-full bg-white rounded-[28px] shadow-[0_12px_40px_rgba(25,28,29,0.08)] px-10 py-10">
                    {tokenInvalido && <PantallaTokenInvalido navigate={navigate} />}

                    {!tokenInvalido && exitoso && <PantallaExito navigate={navigate} />}

                    {!tokenInvalido && !exitoso && (
                        <div className="flex flex-col gap-6">
                            <div>
                                <h2 className="text-[22px] font-bold text-[#191c1d] mb-1"
                                    style={{ fontFamily: "'Manrope', sans-serif" }}>
                                    Nueva contraseña
                                </h2>
                                <p className="text-[13px] text-[#5b403d]">
                                    Elige una contraseña segura de al menos 8 caracteres.
                                </p>
                            </div>

                            <PasswordInput
                                id="nueva"
                                label="Nueva contraseña"
                                value={form.nueva}
                                onChange={e => { setForm(p => ({ ...p, nueva: e.target.value })); setErrores(p => ({ ...p, nueva: '' })) }}
                                error={errores.nueva}
                                placeholder="Mínimo 8 caracteres"
                            />

                            <PasswordInput
                                id="confirmar"
                                label="Confirmar contraseña"
                                value={form.confirmar}
                                onChange={e => { setForm(p => ({ ...p, confirmar: e.target.value })); setErrores(p => ({ ...p, confirmar: '' })) }}
                                error={errores.confirmar}
                                placeholder="Repite tu contraseña"
                            />

                            {errorGeneral && (
                                <div role="alert" className="flex items-center gap-2.5 bg-[rgba(255,218,214,0.5)]
                  border border-[#f5c4b3] rounded-xl px-4 py-3">
                                    <svg className="w-4 h-4 text-[#ba1a1a] flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" clipRule="evenodd"
                                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" />
                                    </svg>
                                    <p className="text-[13px] font-medium text-[#ba1a1a] leading-5">{errorGeneral}</p>
                                </div>
                            )}

                            <button
                                onClick={handleSubmit}
                                disabled={loading}
                                className="relative w-full h-[52px] rounded-xl flex items-center justify-center
                  gap-2 font-bold text-[15px] text-white disabled:opacity-70 disabled:cursor-not-allowed
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
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        Guardando...
                                    </>
                                ) : 'Cambiar contraseña'}
                            </button>

                            <button onClick={() => navigate('/login')}
                                className="text-[13px] text-[#5b403d] hover:underline text-center">
                                Volver al inicio de sesión
                            </button>
                        </div>
                    )}
                </div>

                <p className="text-[11px] text-[#5b403d] text-center">© 2026 Academic Management System.</p>
            </div>
        </div>
    )
}