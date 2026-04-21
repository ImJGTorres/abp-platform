import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'

// ─── Subcomponente: campo de correo con ícono ─────────────────────────────────
function CampoCorreo({ value, onChange, disabled }) {
    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor="correo" className="text-[13px] font-semibold text-[#191c1d] pl-1">
                Correo electrónico
            </label>
            <div className="relative">
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(91,64,61,0.5)] pointer-events-none"
                    viewBox="0 0 16 16" fill="none">
                    <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.3" />
                    <path d="M1 6l7 4 7-4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                </svg>
                <input
                    id="correo"
                    type="email"
                    value={value}
                    onChange={onChange}
                    disabled={disabled}
                    placeholder="nombre@ejemplo.com"
                    autoComplete="email"
                    className="w-full h-[52px] bg-[#e8eaeb] rounded-xl pl-11 pr-4 text-[14px] text-[#191c1d]
            placeholder:text-[rgba(91,64,61,0.45)] outline-none focus:ring-2 focus:ring-[#d32f2f]/50
            transition-shadow duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
                />
            </div>
        </div>
    )
}

// ─── Vista de confirmación tras enviar ────────────────────────────────────────
function PantallaConfirmacion({ correo, onReenviar, reenviando, onEditarCorreo, navigate }) {
    return (
        <div className="flex flex-col gap-6">
            {/* Ícono de éxito */}
            <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-[#e8f5e9] flex items-center justify-center">
                    <svg className="w-8 h-8 text-[#2e7d32]" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2" />
                        <path d="M3 7l9 6 9-6" />
                    </svg>
                </div>
            </div>

            <div className="text-center">
                <h2 className="text-[20px] font-bold text-[#191c1d] mb-2" style={{ fontFamily: "'Manrope', sans-serif" }}>
                    Revisa tu correo
                </h2>
                <p className="text-[13px] text-[#5b403d] leading-relaxed">
                    Si el correo <strong>{correo}</strong> está registrado, recibirás un enlace en los próximos minutos.
                </p>
            </div>

            {/* Recomendaciones */}
            <div className="bg-[#fdf6f0] rounded-xl p-4 flex flex-col gap-2.5">
                {[
                    { texto: '• Revisa también tu carpeta de spam o correo no deseado.' },
                    { texto: '• El enlace expira en 30 minutos.' },
                    { texto: '• Por seguridad, el enlace es de un solo uso.' },
                ].map(({ icon, texto }) => (
                    <div key={texto} className="flex items-start gap-2.5">
                        <span className="text-base leading-none mt-0.5">{icon}</span>
                        <p className="text-[12px] text-[#5b403d] leading-relaxed">{texto}</p>
                    </div>
                ))}
            </div>

            {/* Botón reenviar */}
            <button
                onClick={onReenviar}
                disabled={reenviando}
                className="w-full h-[48px] rounded-xl border-2 border-[#d32f2f] text-[#d32f2f] font-semibold
          text-[14px] hover:bg-[#fdf0ef] transition-colors disabled:opacity-60 disabled:cursor-not-allowed
          flex items-center justify-center gap-2"
                style={{ fontFamily: "'Manrope', sans-serif" }}
            >
                {reenviando ? (
                    <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Enviando...
                    </>
                ) : (
                    <>
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 .49-3.82" />
                        </svg>
                        Reenviar correo
                    </>
                )}
            </button>
            <button
                onClick={onEditarCorreo}
                className="w-full h-[48px] rounded-xl border border-gray-300 text-gray-700 font-semibold text-[14px]
  hover:bg-gray-50 transition-colors"
                style={{ fontFamily: "'Manrope', sans-serif" }}
            >
                Cambiar correo
            </button>

            {/* Volver al login */}
            <button
                onClick={() => navigate('/login')}
                className="w-full h-[48px] rounded-xl bg-[#f0f0f0] text-[#5b403d] font-semibold text-[14px]
          hover:bg-[#e5e5e5] transition-colors"
                style={{ fontFamily: "'Manrope', sans-serif" }}
            >
                Volver al inicio de sesión
            </button>
        </div>
    )
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function OlvidarContrasena() {
    const navigate = useNavigate()
    const [correo, setCorreo] = useState('')
    const [enviado, setEnviado] = useState(false)
    const [loading, setLoading] = useState(false)
    const [reenviando, setReenviando] = useState(false)
    const [error, setError] = useState('')

    const enviar = async (esReenvio = false) => {
        if (!correo.trim()) { setError('Ingresa tu correo electrónico.'); return }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) { setError('Formato de correo inválido.'); return }

        esReenvio ? setReenviando(true) : setLoading(true)
        setError('')

        try {
            await authApi.olvidarContrasena(correo.trim().toLowerCase())
            setEnviado(true)
        } catch (err) {
            if (err?.type === 'network') {
                setError('No se pudo conectar con el servidor.')
            } else {
                // El backend siempre responde 200 — solo llegaríamos aquí con 400 (correo inválido)
                const msg = err?.data?.correo?.[0] ?? 'Error al enviar el correo. Intenta de nuevo.'
                setError(msg)
            }
        } finally {
            esReenvio ? setReenviando(false) : setLoading(false)
        }
    }

    return (
        <div className="relative min-h-screen bg-[#f8f9fa] flex items-center justify-center px-6 py-8 overflow-hidden">
            {/* Fondos decorativos — mismo estilo que LoginForm */}
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
                    {!enviado ? (
                        <div className="flex flex-col gap-6">
                            <div>
                                <h2 className="text-[22px] font-bold text-[#191c1d] mb-1"
                                    style={{ fontFamily: "'Manrope', sans-serif" }}>
                                    ¿Olvidaste tu contraseña?
                                </h2>
                                <p className="text-[13px] text-[#5b403d]">
                                    Ingresa tu correo y te enviaremos un enlace para restablecerla.
                                </p>
                            </div>

                            <CampoCorreo
                                value={correo}
                                onChange={e => { setCorreo(e.target.value); setError('') }}
                                disabled={loading}
                            />

                            {error && (
                                <div role="alert" className="flex items-center gap-2.5 bg-[rgba(255,218,214,0.5)]
                  border border-[#f5c4b3] rounded-xl px-4 py-3">
                                    <svg className="w-4 h-4 text-[#ba1a1a] flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" clipRule="evenodd"
                                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" />
                                    </svg>
                                    <p className="text-[13px] font-medium text-[#ba1a1a] leading-5">{error}</p>
                                </div>
                            )}

                            <button
                                onClick={() => enviar(false)}
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
                                        Enviando...
                                    </>
                                ) : 'Enviar enlace'}
                            </button>

                            <button onClick={() => navigate('/login')}
                                className="text-[13px] text-[#5b403d] hover:underline text-center">
                                Volver al inicio de sesión
                            </button>
                        </div>
                    ) : (
                        <PantallaConfirmacion
                            correo={correo}
                            onReenviar={() => enviar(true)}
                            reenviando={reenviando}
                            onEditarCorreo={() => {
                                setEnviado(false)
                                setError('')
                            }}
                            navigate={navigate}
                        />
                    )}
                </div>

                {/* Footer */}
                <p className="text-[11px] text-[#5b403d] text-center">© 2026 Academic Management System.</p>
            </div>
        </div>
    )
}