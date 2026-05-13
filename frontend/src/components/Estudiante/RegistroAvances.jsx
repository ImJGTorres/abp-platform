import { useState } from 'react'
import { avancesApi } from '../../services/estudianteApi'

function Modal({ open, title, children }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
                <div className="px-6 py-4 border-b border-[#e1e3e4]">
                    <h3 className="text-[17px] font-bold text-[#191c1d]">{title}</h3>
                </div>
                {children}
            </div>
        </div>
    )
}

export default function RegistroAvance({ actividadId, actividadNombre, onSuccess, open, onClose }) {
    const [form, setForm] = useState({
        descripcion: '',
        porcentaje_completado: 0,
        url_referencia: '',
    })
    const [guardando, setGuardando] = useState(false)

    async function guardar() {
        if (!form.descripcion.trim()) {
            alert('La descripción es requerida')
            return
        }
        setGuardando(true)
        try {
            await avancesApi.crear(actividadId, form)
            setForm({ descripcion: '', porcentaje_completado: 0, url_referencia: '' })
            onSuccess?.()
            onClose()
        } catch (err) {
            alert(err.data?.detail || 'Error al registrar avance')
        } finally {
            setGuardando(false)
        }
    }

    return (
        <Modal open={open} title={`Registrar Avance: ${actividadNombre}`}>
            <div className="p-6 space-y-4">
                <div>
                    <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">Descripción del avance *</label>
                    <textarea value={form.descripcion} onChange={e => setForm({ ...form, descripcion: e.target.value })} rows={4}
                        placeholder="Describe el trabajo realizado, resultados obtenidos, obstáculos encontrados..."
                        className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]" />
                </div>

                <div>
                    <div className="flex items-center justify-between mb-2">
                        <label className="text-[13px] font-semibold text-[#191c1d]">Porcentaje de avance</label>
                        <span className="text-[20px] font-extrabold text-[#d32f2f]">{form.porcentaje_completado}%</span>
                    </div>
                    <input type="range" min="0" max="100" step="5" value={form.porcentaje_completado}
                        onChange={e => setForm({ ...form, porcentaje_completado: +e.target.value })}
                        className="w-full h-2 bg-[#e1e3e4] rounded-full appearance-none cursor-pointer
                            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#d32f2f]
                            [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:cursor-pointer
                            [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
                            [&::-moz-range-thumb]:bg-[#d32f2f] [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:shadow-md" />
                    <div className="flex justify-between text-[10px] text-[#9ba7ae] mt-1">
                        <span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span>
                    </div>
                </div>

                <div>
                    <label className="block text-[13px] font-semibold text-[#191c1d] mb-1.5">URL de referencia (opcional)</label>
                    <input type="url" value={form.url_referencia} onChange={e => setForm({ ...form, url_referencia: e.target.value })}
                        placeholder="https://github.com/usuario/repo/pull/123"
                        className="w-full px-3 py-2.5 border border-[#e1e3e4] rounded-xl text-[14px] focus:outline-none focus:ring-2 focus:ring-[#d32f2f]/20 focus:border-[#d32f2f]" />
                    <p className="text-[11px] text-[#9ba7ae] mt-1">Enlace a commit, PR, documento, etc.</p>
                </div>
            </div>

            <div className="px-6 py-4 border-t border-[#e1e3e4] flex gap-2">
                <button onClick={onClose} disabled={guardando}
                    className="flex-1 px-4 py-2.5 border border-[#e1e3e4] text-[#4c616c] rounded-xl hover:bg-[#f0f2f3] transition-colors text-[13px] font-semibold disabled:opacity-50">
                    Cancelar
                </button>
                <button onClick={guardar} disabled={guardando || !form.descripcion.trim()}
                    className="flex-1 px-4 py-2.5 bg-[#d32f2f] text-white rounded-xl hover:bg-[#ba1a1a] transition-colors text-[13px] font-semibold disabled:opacity-50">
                    {guardando ? 'Guardando...' : 'Registrar Avance'}
                </button>
            </div>
        </Modal>
    )
}