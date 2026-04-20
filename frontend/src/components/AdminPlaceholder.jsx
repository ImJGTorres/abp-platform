export default function AdminPlaceholder() {
  return (
    <div
      className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center min-h-0 select-none"
      style={{ fontFamily: "'Manrope', sans-serif" }}
    >
      <div className="w-16 h-16 rounded-2xl bg-[#ffdad6] flex items-center justify-center mb-5">
        <svg viewBox="0 0 32 32" fill="none" className="w-8 h-8" stroke="#af101a" strokeWidth="1.6"
          strokeLinecap="round" strokeLinejoin="round">
          <rect x="4" y="6" width="24" height="20" rx="3" />
          <path d="M4 11h24" />
          <path d="M10 6V4M22 6V4" />
          <path d="M10 18h12M10 22h7" />
        </svg>
      </div>
      <h2 className="text-[17px] font-bold text-[#191c1d] mb-1.5">
        Selecciona una opción del menú
      </h2>
      <p className="text-[13px] text-[#9ba7ae] text-center max-w-[280px] leading-relaxed">
        Usa el sidebar para navegar entre las secciones del panel de administración.
      </p>
    </div>
  )
}