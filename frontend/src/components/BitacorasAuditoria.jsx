import { useState, useEffect, useCallback } from 'react'
import { bitacoraApi } from '../services/api'
import { Search, ShieldAlert, Trash2, Shield, LogIn, LogOut, Eye, Plus, RefreshCw } from 'lucide-react'

const MODULOS = ['Usuarios', 'Autenticacion', 'Configuracion', 'Periodos', 'Cursos', 'Roles']
const ACCIONES = ['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'ACCESS_DENIED', 'ACCESS']
const PAGE_SIZE = 50

const ACCION_CONFIG = {
  CREATE:        { label: 'CREATE',    bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-200',  Icon: Plus },
  UPDATE:        { label: 'UPDATE',    bg: 'bg-blue-100',   text: 'text-blue-700',   border: 'border-blue-200',   Icon: RefreshCw },
  DELETE:        { label: 'DELETE',    bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-200',    Icon: Trash2 },
  LOGIN:         { label: 'LOGIN',     bg: 'bg-gray-100',   text: 'text-gray-700',   border: 'border-gray-200',   Icon: LogIn },
  LOGOUT:        { label: 'LOGOUT',    bg: 'bg-gray-100',   text: 'text-gray-500',   border: 'border-gray-200',   Icon: LogOut },
  ACCESS_DENIED: { label: 'DENEGADO',  bg: 'bg-red-50',     text: 'text-red-800',    border: 'border-red-400',    Icon: ShieldAlert },
  ACCESS:        { label: 'CONSULTA',  bg: 'bg-purple-50',  text: 'text-purple-700', border: 'border-purple-200', Icon: Eye },
}

const ROW_HIGHLIGHT = {
  ACCESS_DENIED: 'bg-red-50',
  DELETE:        'bg-orange-50',
}

const MODULO_COLORS = {
  Usuarios:      'bg-blue-100 text-blue-700',
  Autenticacion: 'bg-purple-100 text-purple-700',
  Configuracion: 'bg-orange-100 text-orange-700',
  Periodos:      'bg-green-100 text-green-700',
  Cursos:        'bg-teal-100 text-teal-700',
  Roles:         'bg-yellow-100 text-yellow-700',
}

const AVATAR_COLORS = [
  'bg-blue-500', 'bg-green-500', 'bg-purple-500',
  'bg-orange-500', 'bg-teal-500', 'bg-pink-500',
]

function formatFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const date = d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const time = d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true })
  return `${date} ${time}`
}

function AvatarInitials({ nombre }) {
  const initials = nombre
    ? nombre.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : '?'
  const color = AVATAR_COLORS[(nombre?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length]
  return (
    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-white text-xs font-bold shrink-0 ${color}`}>
      {initials}
    </span>
  )
}

function ActionBadge({ accion }) {
  const cfg = ACCION_CONFIG[accion] ?? { label: accion, bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-200', Icon: null }
  const { label, bg, text, border, Icon } = cfg
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded border ${bg} ${text} ${border}`}>
      {Icon && <Icon size={11} />}
      {label}
    </span>
  )
}

function ModuloBadge({ modulo }) {
  const cls = MODULO_COLORS[modulo] ?? 'bg-gray-100 text-gray-700'
  return (
    <span className={`text-xs font-medium px-2 py-1 rounded ${cls} whitespace-nowrap`}>
      Módulo: {modulo}
    </span>
  )
}

function Pagination({ count, page, onChange }) {
  const totalPages = Math.ceil(count / PAGE_SIZE)
  if (totalPages <= 1) return null

  const near = new Set([1, totalPages, page - 1, page, page + 1].filter(p => p >= 1 && p <= totalPages))
  const sorted = [...near].sort((a, b) => a - b)

  const withGaps = []
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) withGaps.push('…')
    withGaps.push(sorted[i])
  }

  return (
    <div className="flex items-center gap-1">
      <button
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        className="w-8 h-8 flex items-center justify-center rounded border border-gray-200 text-gray-500 disabled:opacity-40 hover:bg-gray-50 text-sm"
      >
        ‹
      </button>
      {withGaps.map((p, i) =>
        p === '…'
          ? <span key={`gap-${i}`} className="px-1 text-gray-400 text-sm">…</span>
          : <button
              key={p}
              onClick={() => onChange(p)}
              className={`w-8 h-8 rounded text-sm font-medium ${
                p === page
                  ? 'bg-red-600 text-white'
                  : 'border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
      )}
      <button
        disabled={page === Math.ceil(count / PAGE_SIZE)}
        onClick={() => onChange(page + 1)}
        className="w-8 h-8 flex items-center justify-center rounded border border-gray-200 text-gray-500 disabled:opacity-40 hover:bg-gray-50 text-sm"
      >
        ›
      </button>
    </div>
  )
}

const EMPTY_FILTERS = { modulo: '', accion: '', fecha_desde: '', fecha_hasta: '' }

export default function BitacorasAuditoria() {
  const [draft, setDraft]     = useState(EMPTY_FILTERS)
  const [applied, setApplied] = useState(EMPTY_FILTERS)
  const [search, setSearch]   = useState('')
  const [page, setPage]       = useState(1)
  const [data, setData]       = useState({ count: 0, results: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const fetchData = useCallback(async (filters, pageNum) => {
    setLoading(true)
    setError(null)
    try {
      const result = await bitacoraApi.listar({ ...filters, page: pageNum })
      setData(result)
    } catch (e) {
      setError(e?.data?.detail ?? 'Error al cargar las bitácoras')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(applied, page)
  }, [applied, page, fetchData])

  const handleApply = () => {
    setPage(1)
    setApplied({ ...draft })
  }

  const handleClear = () => {
    setDraft(EMPTY_FILTERS)
    setApplied(EMPTY_FILTERS)
    setSearch('')
    setPage(1)
  }

  const removeChip = (key) => {
    const next = { ...applied, [key]: '' }
    setDraft(prev => ({ ...prev, [key]: '' }))
    setApplied(next)
    setPage(1)
  }

  const CHIP_LABELS = { modulo: 'Módulo', accion: 'Acción', fecha_desde: 'Desde', fecha_hasta: 'Hasta' }
  const activeChips = Object.entries(applied)
    .filter(([, v]) => v)
    .map(([k, v]) => ({ key: k, label: `${CHIP_LABELS[k]}: ${v}` }))

  const q = search.trim().toLowerCase()
  const filtered = q
    ? data.results.filter(r =>
        r.nombre_usuario?.toLowerCase().includes(q) ||
        r.descripcion?.toLowerCase().includes(q) ||
        r.id_usuario?.correo?.toLowerCase().includes(q)
      )
    : data.results

  const from = Math.min((page - 1) * PAGE_SIZE + 1, data.count)
  const to   = Math.min(page * PAGE_SIZE, data.count)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Bitácoras de Auditoría</h1>
          <p className="text-sm text-gray-500 mt-1 max-w-xl">
            Visualice y analice el registro histórico de todas las acciones realizadas en la plataforma
            ABP Avanzado para garantizar la transparencia y seguridad.
          </p>
        </div>

        {/* Filter bar */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-3">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por usuario o descripción..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
              />
            </div>

            <select
              value={draft.modulo}
              onChange={e => setDraft(p => ({ ...p, modulo: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
            >
              <option value="">Usuarios</option>
              {MODULOS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>

            <select
              value={draft.accion}
              onChange={e => setDraft(p => ({ ...p, accion: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
            >
              <option value="">Todas</option>
              {ACCIONES.map(a => <option key={a} value={a}>{a}</option>)}
            </select>

            <input
              type="date"
              value={draft.fecha_desde}
              onChange={e => setDraft(p => ({ ...p, fecha_desde: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
            />
            <input
              type="date"
              value={draft.fecha_hasta}
              onChange={e => setDraft(p => ({ ...p, fecha_hasta: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
            />
          </div>
        </div>

        {/* Chips + action buttons */}
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2 min-h-[32px]">
          <div className="flex flex-wrap gap-2">
            {activeChips.map(chip => (
              <span
                key={chip.key}
                className="inline-flex items-center gap-1 bg-red-50 text-red-700 border border-red-200 text-xs px-3 py-1 rounded-full"
              >
                {chip.label}
                <button
                  onClick={() => removeChip(chip.key)}
                  className="ml-0.5 hover:text-red-900 font-bold leading-none"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2 ml-auto">
            <button
              onClick={handleClear}
              className="text-sm text-gray-500 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Limpiar
            </button>
            <button
              onClick={handleApply}
              className="text-sm bg-red-600 text-white px-4 py-1.5 rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Aplicar filtros
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {error && (
            <div className="px-6 py-3 text-sm text-red-600 bg-red-50 border-b border-red-100">
              {error}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-6 py-3">Usuario</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Módulo</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Acción</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Descripción</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">IP</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Fecha / Hora</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td colSpan={6} className="text-center text-gray-400 py-16 text-sm">
                      Cargando registros...
                    </td>
                  </tr>
                )}

                {!loading && filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center text-gray-400 py-16 text-sm">
                      No hay registros que coincidan con los filtros aplicados.
                    </td>
                  </tr>
                )}

                {!loading && filtered.map(r => {
                  const rowCls      = ROW_HIGHLIGHT[r.accion] ?? ''
                  const isPermChange = r.accion === 'UPDATE' && r.modulo === 'Roles'

                  return (
                    <tr
                      key={r.id}
                      className={`border-b border-gray-50 hover:bg-gray-50/80 transition-colors ${rowCls}`}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2.5">
                          <AvatarInitials nombre={r.nombre_usuario} />
                          <div>
                            <div className="font-medium text-gray-800">{r.nombre_usuario}</div>
                            {r.id_usuario?.correo && (
                              <div className="text-xs text-gray-400 mt-0.5">{r.id_usuario.correo}</div>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <ModuloBadge modulo={r.modulo} />
                      </td>

                      <td className="px-4 py-4">
                        <div className="flex flex-col gap-1.5">
                          <ActionBadge accion={r.accion} />
                          {isPermChange && (
                            <span className="inline-flex items-center gap-1 text-xs text-amber-600 font-medium">
                              <Shield size={11} />
                              Cambio de permiso
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-4 text-gray-600 max-w-[220px]">
                        <span className="line-clamp-2">{r.descripcion ?? '—'}</span>
                      </td>

                      <td className="px-4 py-4 font-mono text-xs text-gray-500 whitespace-nowrap">
                        {r.ip_origen ?? '—'}
                      </td>

                      <td className="px-4 py-4 text-gray-500 whitespace-nowrap text-xs">
                        {formatFecha(r.fecha_hora)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          {!loading && data.count > 0 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
              <span className="text-sm text-gray-500">
                Mostrando {from}–{to} de {data.count} registros
              </span>
              <Pagination count={data.count} page={page} onChange={setPage} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
