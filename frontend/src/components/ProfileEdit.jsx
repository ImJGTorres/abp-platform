import { useState, useEffect } from "react";
import { usuariosApi } from "../services/api";
import { session } from "../services/api";

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
  return roles[tipo_rol] || tipo_rol.toUpperCase();
};

export default function ProfileEdit() {
  const user = session.getUser();
  
  const [loading, setLoading] = useState(true);
  const [initialData, setInitialData] = useState(null);
  const [form, setForm] = useState({
    nombre: "",
    apellido: "",
    telefono: "",
  });
  const [toast, setToast] = useState(false);
  const [phoneError, setPhoneError] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [fotoUrl, setFotoUrl] = useState("");
  const [showFotoInput, setShowFotoInput] = useState(false);
  const [fotoInputValue, setFotoInputValue] = useState("");
  const [savingFoto, setSavingFoto] = useState(false);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        const data = await usuariosApi.getPerfil();
        setInitialData({
          nombre: data.nombre || "",
          apellido: data.apellido || "",
          telefono: data.telefono || "",
        });
        setForm({
          nombre: data.nombre || "",
          apellido: data.apellido || "",
          telefono: data.telefono || "",
        });
        setFotoUrl(data.foto_perfil || "");
        setFotoInputValue(data.foto_perfil || "");
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
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: null }));
    if (field === "telefono") {
      setPhoneError(!isValidPhone(value));
    }
  };

  const handleSave = async () => {
    if (phoneError) return;
    
    const changedFields = {};
    if (form.nombre !== initialData.nombre) changedFields.nombre = form.nombre;
    if (form.apellido !== initialData.apellido) changedFields.apellido = form.apellido;
    if (form.telefono !== (initialData.telefono || "")) changedFields.telefono = form.telefono;

    if (Object.keys(changedFields).length === 0) {
      setToast(true);
      setTimeout(() => setToast(false), 3000);
      return;
    }

    try {
      await usuariosApi.actualizarPerfil(changedFields);
      setInitialData({ ...form });
      setToast(true);
      setTimeout(() => setToast(false), 3000);
      setFieldErrors({});
    } catch (err) {
      if (err.status === 400 && err.data) {
        const errors = {};
        Object.keys(err.data).forEach((key) => {
          errors[key] = Array.isArray(err.data[key]) ? err.data[key][0] : err.data[key];
        });
        setFieldErrors(errors);
      } else {
        setFieldErrors({ general: "Error al guardar los cambios" });
      }
    }
  };

  const handleCancel = () => {
    if (initialData) {
      setForm({
        nombre: initialData.nombre,
        apellido: initialData.apellido,
        telefono: initialData.telefono,
      });
    }
    setFieldErrors({});
    setPhoneError(false);
  };

  const handleSaveFoto = async () => {
    setSavingFoto(true);
    try {
      await usuariosApi.actualizarPerfil({ foto_perfil: fotoInputValue });
      setFotoUrl(fotoInputValue);
      setShowFotoInput(false);
    } catch {
      // mantener input abierto para que el usuario pueda reintentar
    } finally {
      setSavingFoto(false);
    }
  };

  const hasChanges = form.nombre !== initialData?.nombre ||
                     form.apellido !== initialData?.apellido ||
                     form.telefono !== (initialData?.telefono || "");

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#f5f6f8", minHeight: "100vh", padding: "32px 16px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }

        .toast-anim { animation: toastIn 0.35s cubic-bezier(.22,1,.36,1) both; }
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(-50%) translateY(-14px) scale(0.96); }
          to   { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
        }

        .field-input {
          width: 100%;
          border: 1.5px solid #e2e2e2;
          border-radius: 8px;
          padding: 11px 14px;
          font-size: 14px;
          font-family: inherit;
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
          border-color: #c0392b;
        }
        .field-input.error {
          border-color: #dc2626;
        }

        .btn-primary {
          background: #c0392b;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 11px 22px;
          font-size: 14px;
          font-weight: 600;
          font-family: inherit;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: background 0.16s, transform 0.1s;
        }
        .btn-primary:hover { background: #a93226; transform: translateY(-1px); }
        .btn-primary:active { transform: translateY(0); }
        .btn-primary:disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; transform: none; }

        .btn-secondary {
          background: transparent;
          color: #555;
          border: 1.5px solid #ddd;
          border-radius: 8px;
          padding: 11px 22px;
          font-size: 14px;
          font-weight: 500;
          font-family: inherit;
          cursor: pointer;
          transition: background 0.15s, border-color 0.15s;
        }
        .btn-secondary:hover { background: #f0f0f0; border-color: #bbb; }

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
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 5px;
          transition: opacity 0.15s;
          cursor: pointer;
          background: none;
          border: none;
          font-family: inherit;
        }
        .pw-link:hover { opacity: 0.72; }
      `}</style>

      {loading && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "200px" }}>
          <span style={{ color: "#6b7280", fontSize: 14 }}>Cargando...</span>
        </div>
      )}

      {!loading && loadError && (
        <div style={{
          maxWidth: 760, margin: "0 auto", padding: "16px 20px",
          background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
          color: "#dc2626", fontSize: 14, textAlign: "center",
        }}>
          No se pudo cargar el perfil. Recarga la página e intenta de nuevo.
        </div>
      )}

      {!loading && !loadError && (
        <>
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
              Perfil actualizado correctamente.
            </div>
          )}

          {fieldErrors.general && (
            <div style={{
              maxWidth: 760, margin: "0 auto 16px", padding: "12px 16px",
              background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
              color: "#dc2626", fontSize: 14,
            }}>
              {fieldErrors.general}
            </div>
          )}

          <div style={{
            maxWidth: 760,
            margin: "0 auto",
            background: "white",
            borderRadius: 16,
            boxShadow: "0 2px 8px rgba(0,0,0,0.07), 0 8px 32px rgba(0,0,0,0.05)",
            overflow: "hidden",
          }}>
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              paddingTop: 36,
              paddingBottom: 28,
              borderBottom: "1px solid #f0f0f0",
            }}>
              <div style={{ position: "relative", width: 90, height: 90, marginBottom: showFotoInput ? 8 : 14 }}>
                <div style={{
                  width: 90, height: 90, borderRadius: "50%",
                  border: "3px solid white",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
                  overflow: "hidden",
                  background: "#E8EDF2",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {fotoUrl
                    ? <img src={fotoUrl} alt="Foto de perfil" style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={() => setFotoUrl("")} />
                    : AVATAR_SVG
                  }
                </div>
                <div className="camera-btn" onClick={() => { setFotoInputValue(fotoUrl); setShowFotoInput(v => !v); }}>
                  <CameraIcon />
                </div>
              </div>

              {showFotoInput && (
                <div style={{ display: "flex", gap: 6, marginBottom: 14, padding: "0 24px", width: "100%", maxWidth: 420 }}>
                  <input
                    value={fotoInputValue}
                    onChange={e => setFotoInputValue(e.target.value)}
                    placeholder="https://ejemplo.com/foto.jpg"
                    style={{
                      flex: 1, border: "1.5px solid #e2e2e2", borderRadius: 8,
                      padding: "7px 10px", fontSize: 13, fontFamily: "inherit", color: "#1a1a1a",
                    }}
                  />
                  <button
                    onClick={handleSaveFoto}
                    disabled={savingFoto}
                    style={{
                      background: "#c0392b", color: "white", border: "none",
                      borderRadius: 8, padding: "7px 14px", fontSize: 13,
                      fontWeight: 600, cursor: savingFoto ? "not-allowed" : "pointer",
                      opacity: savingFoto ? 0.7 : 1, fontFamily: "inherit",
                    }}
                  >
                    {savingFoto ? "..." : "Guardar"}
                  </button>
                  <button
                    onClick={() => setShowFotoInput(false)}
                    style={{
                      background: "transparent", color: "#555", border: "1.5px solid #ddd",
                      borderRadius: 8, padding: "7px 10px", fontSize: 13,
                      cursor: "pointer", fontFamily: "inherit",
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              )}

              <h2 style={{ fontSize: 22, fontWeight: 700, color: "#111", letterSpacing: "-0.4px" }}>
                {form.nombre} {form.apellido}
              </h2>

              <span style={{
                marginTop: 8,
                background: "#fdf0ef",
                color: "#c0392b",
                fontSize: 10.5,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                padding: "4px 12px",
                borderRadius: 20,
              }}>
                {formatRole(user?.tipo_rol)}
              </span>

              <span style={{ fontSize: 13, color: "#999", marginTop: 8 }}>
                {user?.correo}
              </span>
            </div>

            <div style={{ padding: "28px 32px 32px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px 24px" }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Nombre <span style={{ color: "#c0392b" }}>*</span>
                  </label>
                  <input
                    className={`field-input ${fieldErrors.nombre ? 'error' : ''}`}
                    value={form.nombre}
                    onChange={(e) => handleChange("nombre", e.target.value)}
                  />
                  {fieldErrors.nombre && (
                    <p style={{ fontSize: 12, color: "#dc2626", marginTop: 5, display: "flex", alignItems: "center", gap: 5 }}>
                      <AlertIcon /> {fieldErrors.nombre}
                    </p>
                  )}
                </div>

                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Apellido <span style={{ color: "#c0392b" }}>*</span>
                  </label>
                  <input
                    className={`field-input ${fieldErrors.apellido ? 'error' : ''}`}
                    value={form.apellido}
                    onChange={(e) => handleChange("apellido", e.target.value)}
                  />
                  {fieldErrors.apellido && (
                    <p style={{ fontSize: 12, color: "#dc2626", marginTop: 5, display: "flex", alignItems: "center", gap: 5 }}>
                      <AlertIcon /> {fieldErrors.apellido}
                    </p>
                  )}
                </div>

                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "flex", alignItems: "center", gap: 6, marginBottom: 7 }}>
                    Correo electrónico
                    <span style={{ color: "#bbb", display: "flex" }}><LockIcon /></span>
                  </label>
                  <input
                    className="field-input locked"
                    value={user?.correo || ""}
                    readOnly
                  />
                  <p style={{ fontSize: 12, color: "#aaa", marginTop: 5 }}>
                    Solo el administrador puede cambiar el correo.
                  </p>
                </div>

                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#333", display: "block", marginBottom: 7 }}>
                    Teléfono
                  </label>
                  <input
                    className={`field-input ${phoneError || fieldErrors.telefono ? 'has-error' : ''}`}
                    value={form.telefono}
                    onChange={(e) => handleChange("telefono", e.target.value)}
                    placeholder="+57 300 000 0000"
                  />
                  {(phoneError || fieldErrors.telefono) && (
                    <p style={{ fontSize: 12, color: "#dc2626", marginTop: 5, display: "flex", alignItems: "center", gap: 5 }}>
                      <AlertIcon /> {fieldErrors.telefono || "Formato de teléfono inválido"}
                    </p>
                  )}
                </div>

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

              <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
                <button 
                  className="btn-primary" 
                  onClick={handleSave}
                  disabled={!hasChanges || phoneError}
                >
                  <SaveIcon /> Guardar cambios
                </button>
                <button className="btn-secondary" onClick={handleCancel}>
                  Cancelar
                </button>
              </div>
            </div>

            <div style={{
              borderTop: "1px solid #f0f0f0",
              padding: "20px 32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#222" }}>Seguridad</div>
                <div style={{ fontSize: 13, color: "#999", marginTop: 3 }}>
                  Gestiona tu contraseña y métodos de acceso.
                </div>
              </div>
              <button className="pw-link" disabled style={{ opacity: 0.4, cursor: "not-allowed" }}>
                Cambiar contraseña <ArrowIcon />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}