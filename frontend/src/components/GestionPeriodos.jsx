import { useState, useEffect } from "react";
import {
  Plus, Pencil, Trash2, X, AlertCircle,
  BarChart2, ChevronLeft, ChevronRight,
} from "lucide-react";
import { periodosApi } from "../services/api";

const estadoOptions = [
  { value: "activo",   label: "Activo"   },
  { value: "inactivo", label: "Inactivo" },
  { value: "cerrado",  label: "Cerrado"  },
];

const estadoConfig = {
  activo:   { label: "ACTIVO",   bg: "#dcfce7", color: "#16a34a" },
  inactivo: { label: "INACTIVO", bg: "#f3f4f6", color: "#6b7280" },
  cerrado:  { label: "CERRADO",  bg: "#fef2f2", color: "#dc2626" },
};

function formatDate(str) {
  if (!str) return "";
  const [y, m, d] = str.split("-");
  return `${d}/${m}/${y}`;
}

function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
    >
      <div className="bg-white rounded-xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

function ConfirmModal({ isOpen, onClose, onConfirm, nombre }) {
  if (!isOpen) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
    >
      <div className="bg-white rounded-xl w-full max-w-sm shadow-2xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
            <AlertCircle size={20} className="text-red-600" />
          </div>
          <h3 className="text-base font-semibold text-gray-800">Eliminar Periodo</h3>
        </div>
        <p className="text-sm text-gray-500 mb-6 leading-relaxed">
          ¿Está seguro que desea eliminar el periodo{" "}
          <span className="font-medium text-gray-700">"{nombre}"</span>?{" "}
          Esta acción no se puede deshacer.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-medium text-white rounded-lg"
            style={{ backgroundColor: "#c0392b" }}
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  );
}

function PeriodoForm({ periodo, onSave, onCancel }) {
  const [nombre,      setNombre]      = useState(periodo?.nombre       || "");
  const [fechaInicio, setFechaInicio] = useState(periodo?.fecha_inicio || "");
  const [fechaFin,    setFechaFin]    = useState(periodo?.fecha_fin    || "");
  const [estado,      setEstado]      = useState(periodo?.estado       || "activo");
  const [cursos,      setCursos]      = useState(periodo?.cursos       ?? 0);

  const dateError =
    fechaInicio && fechaFin && fechaFin <= fechaInicio
      ? "La fecha de fin debe ser posterior a la de inicio"
      : "";

  const isValid = nombre && fechaInicio && fechaFin && !dateError;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid) return;
    onSave({
      id: periodo?.id,
      nombre,
      fecha_inicio: fechaInicio,
      fecha_fin:    fechaFin,
      estado,
      cursos: Number(cursos),
    });
  };

  const inputCls =
    "w-full h-9 border border-gray-300 rounded-lg px-3 text-sm text-gray-700 " +
    "focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400";
  const labelCls = "block text-xs font-medium text-gray-600 mb-1";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className={labelCls}>Nombre del Periodo</label>
        <input
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className={inputCls}
          placeholder="Formato: 2026-1"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelCls}>Fecha de Inicio</label>
          <input
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            className={inputCls}
            required
          />
        </div>
        <div>
          <label className={labelCls}>Fecha de Fin</label>
          <input
            type="date"
            value={fechaFin}
            onChange={(e) => setFechaFin(e.target.value)}
            className={inputCls}
            required
          />
        </div>
      </div>

      {dateError && (
        <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          <AlertCircle size={14} />
          {dateError}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelCls}>Estado</label>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value)}
            className={inputCls + " bg-white"}
          >
            {estadoOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>Cursos Asociados</label>
          <input
            type="number"
            min="1"
            value={cursos}
            onChange={(e) => setCursos(e.target.value)}
            className={inputCls}
          />
        </div>
      </div>

      <div className="flex gap-3 justify-end pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={!isValid}
          className="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
          style={{
            backgroundColor: isValid ? "#c0392b" : "#e5e7eb",
            color:           isValid ? "white"   : "#9ca3af",
            cursor:          isValid ? "pointer"  : "not-allowed",
          }}
        >
          {periodo?.id ? "Actualizar" : "Crear Periodo"}
        </button>
      </div>
    </form>
  );
}

export default function GestionPeriodos() {
  const [periodos,      setPeriodos]      = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [showModal,     setShowModal]     = useState(false);
  const [editingPeriodo, setEditingPeriodo] = useState(null);
  const [deleteModal,   setDeleteModal]   = useState({ open: false, periodo: null });
  const [toast,         setToast]         = useState(null);

  useEffect(() => {
    loadPeriodos();
  }, []);

  async function loadPeriodos() {
    try {
      const data = await periodosApi.listar();
      setPeriodos(data);
    } catch (err) {
      setToast({ msg: err.data?.detail || "Error al cargar períodos", type: "error" });
      setTimeout(() => setToast(null), 3000);
    } finally {
      setLoading(false);
    }
  }

  const activePeriodo = periodos.find((p) => p.estado === "activo");

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleCreate = () => { setEditingPeriodo(null); setShowModal(true); };
  const handleEdit   = (p) => { setEditingPeriodo(p);   setShowModal(true); };

  const handleSave = async (data) => {
    try {
      const payload = {
        nombre: data.nombre,
        fecha_inicio: data.fecha_inicio,
        fecha_fin: data.fecha_fin,
        estado: data.estado,
      };
      console.log('Enviando período:', payload);
      
      if (data.id) {
        await periodosApi.editar(data.id, payload);
        setPeriodos((prev) => prev.map((p) => (p.id === data.id ? { ...p, ...data } : p)));
        showToast("Periodo actualizado correctamente");
      } else {
        const nuevo = await periodosApi.crear(payload);
        console.log('Período creado:', nuevo);
        setPeriodos((prev) => [nuevo, ...prev]);
        showToast("Periodo creado correctamente");
      }
      setShowModal(false);
      setEditingPeriodo(null);
    } catch (err) {
      console.error('Error al guardar:', err);
      const msg = err.data?.detail || JSON.stringify(err.data) || "Error al guardar período";
      showToast(msg, "error");
    }
  };

  const handleDelete = async () => {
    try {
      await periodosApi.eliminar(deleteModal.periodo.id);
      setPeriodos((prev) => prev.filter((p) => p.id !== deleteModal.periodo.id));
      showToast("Periodo eliminado correctamente");
      setDeleteModal({ open: false, periodo: null });
    } catch (err) {
      showToast(err.data?.detail || "Error al eliminar período", "error");
    }
  };

  return (
    <div
      className="min-h-screen bg-gray-50 p-8"
      style={{ fontFamily: "'Inter','Segoe UI',system-ui,sans-serif" }}
    >
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">
        Workspace &rsaquo; Gestión de Periodos
      </p>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 leading-tight">
            Periodos Académicos
          </h1>
          <p className="text-sm text-gray-500 mt-1 max-w-lg leading-relaxed">
            Administre los ciclos lectivos, defina fechas de vigencia y supervise el estado
            operativo de cada periodo del Atelier.
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg shrink-0 hover:opacity-90 transition-opacity"
          style={{ backgroundColor: "#c0392b" }}
        >
          <Plus size={16} />
          Nuevo periodo
        </button>
      </div>

      {toast && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg mb-4 text-sm ${
            toast.type === "success"
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {toast.msg}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              {["Nombre", "Fecha Inicio", "Fecha Fin", "Estado", "Cursos Asociados", "Acciones"].map(
                (col) => (
                  <th
                    key={col}
                    className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
                  >
                    {col}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-sm text-gray-500">
                  Cargando períodos...
                </td>
              </tr>
            ) : periodos.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-sm text-gray-500">
                  No hay períodos registrados
                </td>
              </tr>
            ) : periodos.map((p) => {
              const cfg = estadoConfig[p.estado] || estadoConfig.inactivo;
              return (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4 text-sm font-semibold text-gray-800">
                    {p.nombre}
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-600">
                    {formatDate(p.fecha_inicio)}
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-600">
                    {formatDate(p.fecha_fin)}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
                      style={{ backgroundColor: cfg.bg, color: cfg.color }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: cfg.color }}
                      />
                      {cfg.label}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-blue-600 underline cursor-pointer">
                    {p.cursos} cursos
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEdit(p)}
                        className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
                      >
                        <Pencil size={14} className="text-gray-500" />
                      </button>
                      <button
                        onClick={() => setDeleteModal({ open: true, periodo: p })}
                        className="w-8 h-8 flex items-center justify-center rounded-lg border border-red-100 bg-red-50 hover:bg-red-100 transition-colors"
                      >
                        <Trash2 size={14} className="text-red-500" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-400 uppercase tracking-wide font-medium">
            Mostrando {periodos.length} periodo
            {periodos.length !== 1 ? "s" : ""} académico
            {periodos.length !== 1 ? "s" : ""} registrado
            {periodos.length !== 1 ? "s" : ""}
          </span>
          <div className="flex items-center gap-1">
            <button className="w-7 h-7 flex items-center justify-center rounded border border-gray-200 text-gray-400 hover:bg-gray-50">
              <ChevronLeft size={13} />
            </button>
            <button
              className="w-7 h-7 flex items-center justify-center rounded text-xs font-semibold text-white"
              style={{ backgroundColor: "#c0392b" }}
            >
              1
            </button>
            <button className="w-7 h-7 flex items-center justify-center rounded border border-gray-200 text-gray-400 hover:bg-gray-50">
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-5">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">
            Estado del Periodo Actual
          </h3>
          <p className="text-xs text-gray-500 leading-relaxed mb-4">
            El periodo{" "}
            <span className="font-medium text-gray-700">
              {activePeriodo?.nombre || "—"}
            </span>{" "}
            se encuentra en fase de inscripción activa. Verifique los cupos disponibles por
            curso.
          </p>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-3xl font-bold" style={{ color: "#c0392b" }}>
              82%
            </span>
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Capacidad Alcanzada
            </span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: "82%", backgroundColor: "#c0392b" }}
            />
          </div>
        </div>

        <div
          className="rounded-xl p-5 flex flex-col justify-between"
          style={{ backgroundColor: "#c0392b" }}
        >
          <div>
            <BarChart2 size={28} className="mb-3" style={{ color: "rgba(255,255,255,0.7)" }} />
            <h3 className="text-sm font-bold text-white mb-1">Historial Anual</h3>
            <p className="text-xs leading-relaxed" style={{ color: "rgba(255,220,220,0.9)" }}>
              Comparativa de matriculados vs periodos anteriores.
            </p>
          </div>
        </div>
      </div>

      <Modal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditingPeriodo(null); }}
        title={editingPeriodo ? "Editar Periodo" : "Nuevo Periodo"}
      >
        <PeriodoForm
          periodo={editingPeriodo}
          onSave={handleSave}
          onCancel={() => { setShowModal(false); setEditingPeriodo(null); }}
        />
      </Modal>

      <ConfirmModal
        isOpen={deleteModal.open}
        onClose={() => setDeleteModal({ open: false, periodo: null })}
        onConfirm={handleDelete}
        nombre={deleteModal.periodo?.nombre}
      />
    </div>
  );
}