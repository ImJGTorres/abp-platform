import { useState, useEffect } from "react";
import { usuariosApi } from "../services/api";

const ROLES = [
  { value: "administrador", label: "Administrador"   },
  { value: "director",      label: "Director"        },
  { value: "docente",       label: "Docente"         },
  { value: "lider_equipo",  label: "Líder de equipo" },
  { value: "estudiante",    label: "Estudiante"      },
];

const estadoConfig = {
  activo:   { label: "Activo",   className: "bg-green-50 text-green-700 border border-green-200" },
  inactivo: { label: "Inactivo", className: "bg-gray-100 text-gray-500 border border-gray-200"  },
};

export default function GestionUsuarios() {
  const [usuarios, setUsuarios]   = useState([]);
  const [loading,  setLoading]    = useState(true);
  const [toast,    setToast]      = useState(null);
  const [confirm,  setConfirm]    = useState(null); // { id, nombre, nuevoRol }

  useEffect(() => { cargarUsuarios(); }, []);

  async function cargarUsuarios() {
    setLoading(true);
    try {
      const data = await usuariosApi.listar();
      setUsuarios(Array.isArray(data) ? data : (data.results ?? []));
    } catch {
      mostrarToast("Error al cargar usuarios", "error");
    } finally {
      setLoading(false);
    }
  }

  function mostrarToast(msg, tipo = "success") {
    setToast({ msg, tipo });
    setTimeout(() => setToast(null), 3500);
  }

  function pedirConfirmacion(usuario, nuevoRol) {
    setConfirm({ id: usuario.id, nombre: `${usuario.nombre} ${usuario.apellido}`, nuevoRol });
  }

  async function confirmarCambioRol() {
    const { id, nombre, nuevoRol } = confirm;
    setConfirm(null);
    try {
      await usuariosApi.cambiarRolUsuario(id, nuevoRol);
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, tipo_rol: nuevoRol } : u))
      );
      mostrarToast(`Rol de ${nombre} actualizado a "${ROLES.find(r => r.value === nuevoRol)?.label}"`);
    } catch (err) {
      mostrarToast(err?.data?.detail ?? "Error al cambiar el rol", "error");
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800">Lista de usuarios</h2>
        <button
          onClick={cargarUsuarios}
          className="text-xs text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50"
        >
          Recargar
        </button>
      </div>

      {toast && (
        <div
          className={`mx-5 mt-3 px-4 py-3 rounded-lg text-sm ${
            toast.tipo === "success"
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {toast.msg}
        </div>
      )}

      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50">
            {["Nombre", "Correo", "Rol", "Estado"].map((col) => (
              <th
                key={col}
                className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {loading ? (
            <tr>
              <td colSpan={4} className="px-5 py-8 text-center text-sm text-gray-400">
                Cargando usuarios…
              </td>
            </tr>
          ) : usuarios.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-5 py-8 text-center text-sm text-gray-400">
                No hay usuarios registrados
              </td>
            </tr>
          ) : (
            usuarios.map((u) => {
              const est = estadoConfig[u.estado] ?? estadoConfig.inactivo;
              return (
                <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 text-sm font-medium text-gray-800">
                    {u.nombre} {u.apellido}
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600">{u.correo}</td>
                  <td className="px-5 py-3">
                    <select
                      value={u.tipo_rol}
                      onChange={(e) => pedirConfirmacion(u, e.target.value)}
                      className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400"
                    >
                      {ROLES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${est.className}`}>
                      {est.label}
                    </span>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {confirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
        >
          <div className="bg-white rounded-xl w-full max-w-sm shadow-2xl p-6">
            <h3 className="text-base font-semibold text-gray-800 mb-3">Cambiar rol</h3>
            <p className="text-sm text-gray-500 mb-6">
              ¿Cambiar el rol de <strong>{confirm.nombre}</strong> a{" "}
              <strong>{ROLES.find((r) => r.value === confirm.nuevoRol)?.label}</strong>?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={confirmarCambioRol}
                className="px-4 py-2 text-sm font-medium text-white rounded-lg"
                style={{ backgroundColor: "#c0392b" }}
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
