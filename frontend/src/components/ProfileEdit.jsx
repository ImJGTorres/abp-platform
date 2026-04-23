import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { usuariosApi, session, rutaPorRol, authApi, buildMediaUrl } from "../services/api";

// ─── SVG Assets ────────────────────────────────────────────────────────────────

const AVATAR_SVG = (
  <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" width="90" height="90">
    <circle cx="40" cy="40" r="40" fill="#E8EDF2" />
    <ellipse cx="40" cy="32" rx="14" ry="15" fill="#6B9BB8" />
    <path d="M14 72c0-14.36 11.64-26 26-26h0c14.36 0 26 11.64 26 26" fill="#4A7C96" />
    <ellipse cx="40" cy="30" rx="10" ry="11" fill="#F5C5A3" />
    <rect x="30" y="38" width="20" height="14" rx="4" fill="#5B8FA8" />
  </svg>
);

const LockIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const SaveIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
    <polyline points="17 21 17 13 7 13 7 21" />
    <polyline points="7 3 7 8 15 8" />
  </svg>
);

const AlertIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

const CameraIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
    <circle cx="12" cy="13" r="4" />
  </svg>
);

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const ArrowIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const EyeIcon = ({ open }) =>
  open ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );

// ─── Helpers ───────────────────────────────────────────────────────────────────

const isValidPhone = (phone) => {
  if (!phone) return true;
  const cleaned = phone.replace(/\s/g, "");
  return /^\+?[0-9]{7,15}$/.test(cleaned);
};

const formatRole = (tipo_rol) => {
  const roles = {
    administrador: "ADMINISTRADOR",
    director: "DIRECTOR",
    docente: "DOCENTE",
    lider_equipo: "LÍDER DE EQUIPO",
    estudiante: "ESTUDIANTE",
  };
  return roles[tipo_rol] || (tipo_rol ? tipo_rol.toUpperCase() : "");
};

// ─── Estilos globales ──────────────────────────────────────────────────────────

const GLOBAL_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* Toast */
  .toast-anim {
    animation: toastIn 0.35s cubic-bezier(.22,1,.36,1) both;
  }
  @keyframes toastIn {
    from { opacity: 0; transform: translateX(-50%) translateY(-14px) scale(0.96); }
    to   { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
  }

  /* Modal backdrop */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 900;
    padding: 16px;
    animation: fadeIn 0.2s ease both;
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  /* Modal box */
  .modal-box {
    background: #fff;
    border-radius: 16px;
    width: 100%;
    max-width: 440px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.18);
    animation: slideUp 0.3s cubic-bezier(.22,1,.36,1) both;
    overflow: hidden;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(24px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* Inputs */
  .field-input {
    width: 100%;
    border: 1.5px solid #e2e2e2;
    border-radius: 8px;
    padding: 11px 14px;
    font-size: 14px;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    color: #1a1a1a;
    background: #fff;
    transition: border-color 0.18s, box-shadow 0.18s;
  }
  .field-input:focus {
    outline: none;
    border-color: #c0392b;
    box-shadow: 0 0 0 3px rgba(192,57,43,0.1);
  }
  .field-input.locked {
    background: #f4f4f5;
    color: #aaa;
    cursor: not-allowed;
  }
  .field-input.has-error {
    border-color: #dc2626;
    box-shadow: 0 0 0 3px rgba(220,38,38,0.08);
  }

  /* Password input wrapper */
  .pw-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }
  .pw-input-wrapper .field-input {
    padding-right: 42px;
  }
  .pw-eye-btn {
    position: absolute;
    right: 12px;
    background: none;
    border: none;
    cursor: pointer;
    color: #aaa;
    display: flex;
    align-items: center;
    padding: 0;
    transition: color 0.15s;
  }
  .pw-eye-btn:hover { color: #555; }

  /* Buttons */
  .btn-primary {
    background: #c0392b;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 11px 22px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: background 0.16s, transform 0.1s;
  }
  .btn-primary:hover:not(:disabled) { background: #a93226; transform: translateY(-1px); }
  .btn-primary:active:not(:disabled) { transform: translateY(0); }
  .btn-primary:disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; }

  .btn-secondary {
    background: transparent;
    color: #555;
    border: 1.5px solid #ddd;
    border-radius: 8px;
    padding: 11px 22px;
    font-size: 14px;
    font-weight: 500;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .btn-secondary:hover { background: #f0f0f0; border-color: #bbb; }

  .btn-ghost {
    background: none;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 6px;
    color: #888;
    transition: background 0.15s, color 0.15s;
  }
  .btn-ghost:hover { background: #f0f0f0; color: #333; }

  .camera-btn {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 27px;
    height: 27px;
    background: #c0392b;
    border-radius: 50%;
    border: 2px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.15s, transform 0.15s;
  }
  .camera-btn:hover { background: #a93226; transform: scale(1.1); }

  .pw-link {
    color: #c0392b;
    font-size: 14px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    background: none;
    border: none;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    transition: opacity 0.15s;
  }
  .pw-link:hover { opacity: 0.72; }

  /* Error & hint text */
  .field-error {
    font-size: 12px;
    color: #dc2626;
    margin-top: 5px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .field-hint {
    font-size: 12px;
    color: #aaa;
    margin-top: 5px;
  }

  /* Password strength bar */
  .strength-bar {
    height: 3px;
    border-radius: 99px;
    margin-top: 6px;
    transition: width 0.3s, background 0.3s;
  }
`;

// ─── Password strength helper ──────────────────────────────────────────────────

const getPasswordStrength = (pw) => {
  if (!pw) return { level: 0, label: "", color: "#e2e2e2" };
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const map = [
    { level: 1, label: "Débil", color: "#dc2626" },
    { level: 2, label: "Regular", color: "#f59e0b" },
    { level: 3, label: "Buena", color: "#3b82f6" },
    { level: 4, label: "Fuerte", color: "#16a34a" },
  ];
  return map[score - 1] || { level: 0, label: "", color: "#e2e2e2" };
};

// ─── Modal cambiar contraseña ──────────────────────────────────────────────────

function PasswordModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ actual: "", nueva: "", confirmar: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState({ actual: false, nueva: false, confirmar: false });

  const strength = getPasswordStrength(form.nueva);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: null, general: null }));
  };

  const toggleShow = (field) =>
    setShowPw((prev) => ({ ...prev, [field]: !prev[field] }));

  const handleSubmit = async () => {
    const errs = {};
    if (!form.actual) errs.actual = "Ingresa tu contraseña actual";
    if (!form.nueva) errs.nueva = "Ingresa una nueva contraseña";
    else if (form.nueva.length < 8) errs.nueva = "Mínimo 8 caracteres";
    if (!form.confirmar) errs.confirmar = "Confirma tu nueva contraseña";
    else if (form.nueva !== form.confirmar) errs.confirmar = "Las contraseñas no coinciden";

    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    try {
      setLoading(true);
      await authApi.cambiarContrasena({
        password_actual: form.actual,
        nueva_contrasena: form.nueva,
        confirmar_contrasena: form.confirmar,
      });
      onSuccess();
    } catch (err) {
      if (err.status === 400 && err.data) {
        setErrors({
          actual: err.data.password_actual,
          nueva: err.data.nueva_contrasena,
          confirmar: err.data.confirmar_contrasena,
          general: err.data.non_field_errors?.[0] || err.data.detail,
        });
      } else {
        setErrors({ general: "Ocurrió un error. Intenta de nuevo." });
      }
    } finally {
      setLoading(false);
    }
  };

  // Cerrar con Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const fields = [
    { key: "actual", label: "Contraseña actual", placeholder: "Tu contraseña actual" },
    { key: "nueva", label: "Nueva contraseña", placeholder: "Mínimo 8 caracteres" },
    { key: "confirmar", label: "Confirmar nueva contraseña", placeholder: "Repite la nueva contraseña" },
  ];

  return (
    <div className="modal-backdrop" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-box">
        {/* Header */}
        <div style={{ padding: "24px 24px 0", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: "#111", letterSpacing: "-0.3px" }}>
              Cambiar contraseña
            </h3>
            <p style={{ fontSize: 13, color: "#888", marginTop: 4 }}>
              Elige una contraseña segura que no uses en otros sitios.
            </p>
          </div>
          <button className="btn-ghost" onClick={onClose} style={{ marginTop: 2 }}>
            <CloseIcon />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px 24px" }}>
          {errors.general && (
            <div style={{
              background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
              padding: "10px 14px", marginBottom: 16, fontSize: 13, color: "#dc2626",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <AlertIcon /> {errors.general}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {fields.map(({ key, label, placeholder }) => (
              <div key={key}>
                <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                  {label}
                </label>
                <div className="pw-input-wrapper">
                  <input
                    type={showPw[key] ? "text" : "password"}
                    className={`field-input${errors[key] ? " has-error" : ""}`}
                    value={form[key]}
                    onChange={(e) => handleChange(key, e.target.value)}
                    placeholder={placeholder}
                    autoComplete={key === "actual" ? "current-password" : "new-password"}
                  />
                  <button
                    className="pw-eye-btn"
                    onClick={() => toggleShow(key)}
                    type="button"
                    tabIndex={-1}
                  >
                    <EyeIcon open={showPw[key]} />
                  </button>
                </div>

                {/* Barra de fortaleza solo en campo "nueva" */}
                {key === "nueva" && form.nueva && (
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
                      {[1, 2, 3, 4].map((i) => (
                        <div
                          key={i}
                          className="strength-bar"
                          style={{
                            flex: 1,
                            background: i <= strength.level ? strength.color : "#e2e2e2",
                          }}
                        />
                      ))}
                      <span style={{ fontSize: 11, color: strength.color, fontWeight: 600, minWidth: 46 }}>
                        {strength.label}
                      </span>
                    </div>
                  </div>
                )}

                {errors[key] && (
                  <p className="field-error">
                    <AlertIcon /> {errors[key]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: "0 24px 24px",
          display: "flex",
          gap: 10,
          justifyContent: "flex-end",
        }}>
          <button className="btn-secondary" onClick={onClose} disabled={loading}>
            Cancelar
          </button>
          <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Guardando..." : <><SaveIcon /> Guardar contraseña</>}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Componente principal ──────────────────────────────────────────────────────

export default function ProfileEdit() {
  const user = session.getUser();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [initialData, setInitialData] = useState(null);

  const [form, setForm] = useState({ nombre: "", apellido: "", telefono: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [phoneError, setPhoneError] = useState(false);

  const [fotoUrl,      setFotoUrl]      = useState("");
  const [fotoArchivo,  setFotoArchivo]  = useState(null);   // File object seleccionado
  const [fotoPreview,  setFotoPreview]  = useState(null);   // URL de preview local
  const [uploadingFoto, setUploadingFoto] = useState(false);
  const fotoInputRef = useState(() => ({ current: null }))[0];

  const [toast, setToast] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  // Cargar perfil
  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        const data = await usuariosApi.getPerfil();
        const profile = {
          nombre: data.nombre || "",
          apellido: data.apellido || "",
          telefono: data.telefono || "",
        };
        setInitialData(profile);
        setForm(profile);
        setFotoUrl(data.foto_perfil || "");
      } catch (err) {
        console.error("Error al cargar perfil:", err);
        setLoadError(true);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleChange = (field, value) => {
    // Filtro en tiempo real: solo permite letras unicode, tildes, ñ y espacios para nombre y apellido
    if (field === "nombre" || field === "apellido") {
      // Elimina TODO carácter que NO sea letra (unicode) ni espacio
      value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, "");
    }
    
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: null }));
    if (field === "telefono") setPhoneError(!isValidPhone(value));
  };

  const handleSave = async () => {
    if (phoneError) return;

    const changedFields = {};
    if (form.nombre !== initialData.nombre) changedFields.nombre = form.nombre;
    if (form.apellido !== initialData.apellido) changedFields.apellido = form.apellido;
    if (form.telefono !== (initialData.telefono || "")) changedFields.telefono = form.telefono;

    if (Object.keys(changedFields).length === 0) {
      showToast();
      return;
    }

    try {
      await usuariosApi.actualizarPerfil(changedFields);
      setInitialData({ ...form });
      setFieldErrors({});
      showToast();
    } catch (err) {
      if (err.status === 400 && err.data) {
        const errors = {};
        Object.keys(err.data).forEach((key) => {
          errors[key] = Array.isArray(err.data[key]) ? err.data[key][0] : err.data[key];
        });
        setFieldErrors(errors);
      } else {
        setFieldErrors({ general: "Error al guardar los cambios. Intenta de nuevo." });
      }
    }
  };

  const handleCancel = () => {
    if (initialData) setForm({ ...initialData });
    setFieldErrors({});
    setPhoneError(false);
  };

  const handleSeleccionarFoto = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Liberar URL de preview anterior
    if (fotoPreview) URL.revokeObjectURL(fotoPreview);

    setFotoArchivo(file);
    setFotoPreview(URL.createObjectURL(file));
  };

  const handleSaveFoto = async () => {
    if (!fotoArchivo) return;
    setUploadingFoto(true);
    try {
      const data = await usuariosApi.subirFotoPerfil(fotoArchivo);
      const nuevaUrl = data.foto_perfil;
      setFotoUrl(nuevaUrl);
      setFotoArchivo(null);
      if (fotoPreview) { URL.revokeObjectURL(fotoPreview); setFotoPreview(null); }

      // Sincronizar en localStorage para header y sidebar
      const currentUser = session.getUser();
      if (currentUser) {
        session.save(session.getAccess(), session.getRefresh(), { ...currentUser, foto_perfil: nuevaUrl });
        window.dispatchEvent(new Event('user-updated'));
      }
    } catch {
      // mantener preview para reintento
    } finally {
      setUploadingFoto(false);
    }
  };

  const handleCancelarFoto = () => {
    if (fotoPreview) { URL.revokeObjectURL(fotoPreview); setFotoPreview(null); }
    setFotoArchivo(null);
    if (fotoInputRef.current) fotoInputRef.current.value = '';
  };

  const showToast = () => {
    setToast(true);
    setTimeout(() => setToast(false), 3000);
  };

  const hasChanges =
    form.nombre !== initialData?.nombre ||
    form.apellido !== initialData?.apellido ||
    form.telefono !== (initialData?.telefono || "");

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#f5f6f8", minHeight: "100vh", padding: "32px 16px" }}>
      <style>{GLOBAL_STYLES}</style>

      {/* Toast */}
      {toast && (
        <div className="toast-anim" style={{
          position: "fixed", top: 18, left: "50%",
          transform: "translateX(-50%)",
          background: "#27ae60", color: "white",
          borderRadius: 10, padding: "10px 20px",
          display: "flex", alignItems: "center", gap: 10,
          fontSize: 14, fontWeight: 500,
          boxShadow: "0 6px 28px rgba(39,174,96,0.28)",
          zIndex: 999, whiteSpace: "nowrap",
        }}>
          <span style={{
            background: "rgba(255,255,255,0.22)", borderRadius: "50%",
            width: 24, height: 24, display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <CheckIcon />
          </span>
          Cambios guardados correctamente.
        </div>
      )}

      {/* Modal contraseña */}
      {showPasswordModal && (
        <PasswordModal
          onClose={() => setShowPasswordModal(false)}
          onSuccess={() => {
            setShowPasswordModal(false);
            showToast();
          }}
        />
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "200px" }}>
          <span style={{ color: "#6b7280", fontSize: 14 }}>Cargando...</span>
        </div>
      )}

      {/* Error de carga */}
      {!loading && loadError && (
        <div style={{
          maxWidth: 760, margin: "0 auto", padding: "16px 20px",
          background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
          color: "#dc2626", fontSize: 14, textAlign: "center",
        }}>
          No se pudo cargar el perfil. Recarga la página e intenta de nuevo.
        </div>
      )}

      {/* Contenido principal */}
      {!loading && !loadError && (
        <>
          {/* Botón volver */}
          <div style={{ maxWidth: 760, margin: "0 auto 16px" }}>
            <button
              onClick={() => navigate(rutaPorRol(user?.tipo_rol))}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: "transparent", border: "none", cursor: "pointer",
                color: "#6b7280", fontSize: 13, fontFamily: "inherit", padding: "4px 0",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 12H5M12 5l-7 7 7 7" />
              </svg>
              Volver
            </button>
          </div>

          {/* Tarjeta principal */}
          <div style={{
            maxWidth: 760, margin: "0 auto",
            background: "white", borderRadius: 16,
            boxShadow: "0 2px 8px rgba(0,0,0,0.07), 0 8px 32px rgba(0,0,0,0.05)",
            overflow: "hidden",
          }}>

            {/* Cabecera con avatar */}
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              paddingTop: 36, paddingBottom: 28, borderBottom: "1px solid #f0f0f0",
            }}>
              {/* Input de archivo oculto */}
              <input
                ref={(el) => { fotoInputRef.current = el; }}
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                style={{ display: "none" }}
                onChange={handleSeleccionarFoto}
              />

              {/* Avatar */}
              <div style={{ position: "relative", width: 90, height: 90, marginBottom: (fotoArchivo) ? 8 : 14 }}>
                <div style={{
                  width: 90, height: 90, borderRadius: "50%",
                  border: "3px solid white",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
                  overflow: "hidden", background: "#E8EDF2",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {(fotoPreview || fotoUrl)
                    ? <img
                        src={fotoPreview || buildMediaUrl(fotoUrl)}
                        alt="Foto de perfil"
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        onError={() => { setFotoUrl(""); setFotoPreview(null); }}
                      />
                    : AVATAR_SVG
                  }
                </div>
                <div className="camera-btn" onClick={() => fotoInputRef.current?.click()}>
                  <CameraIcon />
                </div>
              </div>

              {/* Controles de foto: solo visibles al seleccionar un archivo */}
              {fotoArchivo && (
                <div style={{ display: "flex", gap: 6, marginBottom: 14, alignItems: "center" }}>
                  <span style={{ fontSize: 12, color: "#666", maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {fotoArchivo.name}
                  </span>
                  <button
                    onClick={handleSaveFoto}
                    disabled={uploadingFoto}
                    className="btn-primary"
                    style={{ padding: "7px 14px", fontSize: 13 }}
                  >
                    {uploadingFoto ? "Subiendo..." : "Guardar foto"}
                  </button>
                  <button
                    onClick={handleCancelarFoto}
                    className="btn-secondary"
                    style={{ padding: "7px 10px", fontSize: 13 }}
                  >
                    Cancelar
                  </button>
                </div>
              )}

              <h2 style={{ fontSize: 22, fontWeight: 700, color: "#111", letterSpacing: "-0.4px" }}>
                {form.nombre} {form.apellido}
              </h2>

              <span style={{
                marginTop: 8, background: "#fdf0ef", color: "#c0392b",
                fontSize: 10.5, fontWeight: 700, letterSpacing: "0.08em",
                textTransform: "uppercase", padding: "4px 12px", borderRadius: 20,
              }}>
                {formatRole(user?.tipo_rol)}
              </span>

              <span style={{ fontSize: 13, color: "#999", marginTop: 8 }}>
                {user?.correo}
              </span>
            </div>

            {/* Formulario */}
            <div style={{ padding: "28px 32px 32px" }}>

              {fieldErrors.general && (
                <div style={{
                  padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca",
                  borderRadius: 8, color: "#dc2626", fontSize: 14, marginBottom: 20,
                  display: "flex", alignItems: "center", gap: 6,
                }}>
                  <AlertIcon /> {fieldErrors.general}
                </div>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px 24px" }}>

                {/* Nombre */}
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Nombre <span style={{ color: "#c0392b" }}>*</span>
                  </label>
                  <input
                    className={`field-input${fieldErrors.nombre ? " has-error" : ""}`}
                    value={form.nombre}
                    onChange={(e) => handleChange("nombre", e.target.value)}
                  />
                  {fieldErrors.nombre && (
                    <p className="field-error"><AlertIcon /> {fieldErrors.nombre}</p>
                  )}
                </div>

                {/* Apellido */}
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Apellido <span style={{ color: "#c0392b" }}>*</span>
                  </label>
                  <input
                    className={`field-input${fieldErrors.apellido ? " has-error" : ""}`}
                    value={form.apellido}
                    onChange={(e) => handleChange("apellido", e.target.value)}
                  />
                  {fieldErrors.apellido && (
                    <p className="field-error"><AlertIcon /> {fieldErrors.apellido}</p>
                  )}
                </div>

                {/* Correo (bloqueado) */}
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "flex", alignItems: "center", gap: 6, marginBottom: 7 }}>
                    Correo electrónico
                    <span style={{ color: "#bbb", display: "flex" }}><LockIcon /></span>
                  </label>
                  <input className="field-input locked" value={user?.correo || ""} readOnly />
                  <p className="field-hint">Solo el administrador puede cambiar el correo.</p>
                </div>

                {/* Teléfono */}
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Teléfono
                  </label>
                  <input
                    className={`field-input${(phoneError || fieldErrors.telefono) ? " has-error" : ""}`}
                    value={form.telefono}
                    onChange={(e) => handleChange("telefono", e.target.value)}
                    placeholder="+57 300 000 0000"
                  />
                  {(phoneError || fieldErrors.telefono) && (
                    <p className="field-error">
                      <AlertIcon /> {fieldErrors.telefono || "Formato de teléfono inválido"}
                    </p>
                  )}
                </div>

                {/* Rol (bloqueado) */}
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Rol asignado
                  </label>
                  <input
                    className="field-input locked"
                    value={formatRole(user?.tipo_rol)}
                    readOnly
                    style={{ fontWeight: 600, fontSize: 13, letterSpacing: "0.03em" }}
                  />
                </div>

              </div>

              {/* Acciones */}
              <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
                <button
                  className="btn-primary"
                  onClick={handleSave}
                  disabled={!hasChanges || phoneError}
                >
                  <SaveIcon /> Guardar cambios
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    if (hasChanges) {
                      handleCancel();
                    } else {
                      navigate(rutaPorRol(user?.tipo_rol));
                    }
                  }}
                >
                  Cancelar
                </button>
              </div>
            </div>

            {/* Sección seguridad */}
            <div style={{
              borderTop: "1px solid #f0f0f0", padding: "20px 32px",
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#222" }}>Seguridad</div>
                <div style={{ fontSize: 13, color: "#999", marginTop: 3 }}>
                  Gestiona tu contraseña.
                </div>
              </div>
              <button className="pw-link" onClick={() => setShowPasswordModal(true)}>
                Cambiar contraseña <ArrowIcon />
              </button>
            </div>

          </div>
        </>
      )}
    </div>
  );
}