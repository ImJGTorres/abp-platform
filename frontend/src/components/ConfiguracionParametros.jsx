import { useState } from "react";

// ─── Datos iniciales ────────────────────────────────────────────────────────
const initialParams = {
  institucional: {
    nombre_institucion: "Universidad Francisco de Paula Santander",
    correo_soporte: "soporte@ufps.edu.co",
    logo_url: "https://ufps.edu.co/assets/logo.png",
  },
  academicos: {
    max_estudiantes_equipo: 5,
    semanas_sprint: 2,
    nota_minima_aprobacion: 60,
  },
  seguridad: {
    bitacora_activa: true,
    proyectos_publicos: false,
    modo_mantenimiento: false,
  },
};

// ─── Subcomponentes ──────────────────────────────────────────────────────────

function Toast({ message, onClose }) {
  if (!message) return null;
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "10px 16px",
      backgroundColor: "#f0fdf4",
      border: "1px solid #86efac",
      borderRadius: 6,
      marginBottom: 24,
      fontSize: 13,
      color: "#15803d",
    }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="8" fill="#22c55e" />
        <path d="M5 8l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span style={{ flex: 1 }}>{message}</span>
      <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#15803d", fontSize: 16, lineHeight: 1 }}>×</button>
    </div>
  );
}

function ParamRow({ label, paramKey, value, type, onChange }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "200px 1fr",
      alignItems: "center",
      gap: 16,
      padding: "12px 20px",
      borderBottom: "1px solid #fecdd3",
    }}>
      <div>
        <div style={{ fontSize: 13, color: "#374151", fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 10, color: "#c0392b", fontFamily: "monospace", marginTop: 2 }}>{paramKey}</div>
      </div>

      <div>
        {type === "BOOLEANO" ? (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              onClick={() => onChange(!value)}
              style={{
                width: 44,
                height: 24,
                borderRadius: 99,
                border: "none",
                backgroundColor: value ? "#c0392b" : "#d1d5db",
                cursor: "pointer",
                position: "relative",
                transition: "background-color 0.2s",
                flexShrink: 0,
              }}
            >
              <span style={{
                position: "absolute",
                top: 3,
                left: value ? 22 : 3,
                width: 18,
                height: 18,
                borderRadius: "50%",
                backgroundColor: "white",
                transition: "left 0.2s",
                boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              }} />
            </button>
            <span style={{ fontSize: 13, color: "#6b7280" }}>
              {value ? "Habilitado" : "Deshabilitado"}
            </span>
          </div>
        ) : type === "ENTERO" ? (
          <input
            type="number"
            value={value}
            onChange={(e) => onChange(parseInt(e.target.value) || 0)}
            style={{
              width: 100,
              height: 32,
              border: "1px solid #d1d5db",
              borderRadius: 6,
              padding: "0 10px",
              fontSize: 13,
              color: "#374151",
              backgroundColor: "white",
              outline: "none",
            }}
            onFocus={(e) => { e.target.style.borderColor = "#c0392b"; e.target.style.boxShadow = "0 0 0 2px #fee2e2"; }}
            onBlur={(e) => { e.target.style.borderColor = "#d1d5db"; e.target.style.boxShadow = "none"; }}
          />
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            style={{
              width: "100%",
              height: 32,
              border: "1px solid #d1d5db",
              borderRadius: 6,
              padding: "0 10px",
              fontSize: 13,
              color: "#374151",
              backgroundColor: "white",
              outline: "none",
            }}
            onFocus={(e) => { e.target.style.borderColor = "#c0392b"; e.target.style.boxShadow = "0 0 0 2px #fee2e2"; }}
            onBlur={(e) => { e.target.style.borderColor = "#d1d5db"; e.target.style.boxShadow = "none"; }}
          />
        )}
      </div>
    </div>
  );
}

function SectionCard({ icon, iconBg, title, children, onSave }) {
  return (
    <div style={{
      border: "1px solid #fecdd3",
      borderRadius: 8,
      overflow: "hidden",
      backgroundColor: "white",
      marginBottom: 20,
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "12px 20px",
        backgroundColor: "#fff5f5",
        borderBottom: "1px solid #fecdd3",
      }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          backgroundColor: iconBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 13,
          fontWeight: 700,
          color: "white",
          flexShrink: 0,
        }}>
          {icon}
        </div>
        <span style={{ fontSize: 14, fontWeight: 600, color: "#1f2937" }}>{title}</span>
      </div>

      {/* Rows */}
      <div>{children}</div>

      {/* Footer */}
      <div style={{
        display: "flex",
        justifyContent: "flex-end",
        padding: "12px 20px",
        backgroundColor: "#fff5f5",
        borderTop: "1px solid #fecdd3",
      }}>
        <button
          onClick={onSave}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "8px 18px",
            backgroundColor: "#c0392b",
            color: "white",
            border: "none",
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
            transition: "background-color 0.15s",
          }}
          onMouseEnter={(e) => e.target.style.backgroundColor = "#991b1b"}
          onMouseLeave={(e) => e.target.style.backgroundColor = "#c0392b"}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 7.5L5.5 11L12 4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Guardar sección
        </button>
      </div>
    </div>
  );
}

// ─── Componente principal ────────────────────────────────────────────────────
export default function ConfiguracionParametros() {
  const [params, setParams] = useState(initialParams);
  const [toast, setToast] = useState("");

  function updateParam(section, key, value) {
    setParams((prev) => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }));
  }

  function handleSave(section) {
    // Aquí iría la llamada PATCH /api/configuracion/:clave/
    console.log(`Guardando sección ${section}:`, params[section]);
    setToast("Cambios guardados satisfactoriamente");
    setTimeout(() => setToast(""), 4000);
  }

  return (
    <div style={{
      padding: "32px 40px",
      maxWidth: 860,
      fontFamily: "'Segoe UI', system-ui, sans-serif",
    }}>
      {/* Título de página */}
      <h1 style={{ fontSize: 24, fontWeight: 700, color: "#111827", margin: "0 0 4px" }}>
        Configuración de Parámetros
      </h1>
      <p style={{ fontSize: 13, color: "#6b7280", margin: "0 0 24px" }}>
        Defina y ajuste las reglas de negocio, información institucional y controles de seguridad del sistema.
      </p>

      {/* Toast */}
      <Toast message={toast} onClose={() => setToast("")} />

      {/* Sección 1: Información Institucional */}
      <SectionCard
        icon="I"
        iconBg="#c0392b"
        title="Información Institucional"
        onSave={() => handleSave("institucional")}
      >
        <ParamRow
          label="Nombre de la institución"
          paramKey="nombre_institucion"
          value={params.institucional.nombre_institucion}
          type="TEXTO"
          onChange={(v) => updateParam("institucional", "nombre_institucion", v)}
        />
        <ParamRow
          label="Correo de Soporte"
          paramKey="correo_soporte"
          value={params.institucional.correo_soporte}
          type="TEXTO"
          onChange={(v) => updateParam("institucional", "correo_soporte", v)}
        />
        <ParamRow
          label="Logo URL"
          paramKey="logo_url"
          value={params.institucional.logo_url}
          type="TEXTO"
          onChange={(v) => updateParam("institucional", "logo_url", v)}
        />
      </SectionCard>

      {/* Sección 2: Parámetros Académicos */}
      <SectionCard
        icon="A"
        iconBg="#c0392b"
        title="Parámetros Académicos"
        onSave={() => handleSave("academicos")}
      >
        <ParamRow
          label="Máximo de estudiantes por equipo"
          paramKey="max_estudiantes_equipo"
          value={params.academicos.max_estudiantes_equipo}
          type="ENTERO"
          onChange={(v) => updateParam("academicos", "max_estudiantes_equipo", v)}
        />
        <ParamRow
          label="Semanas por sprint"
          paramKey="semanas_sprint"
          value={params.academicos.semanas_sprint}
          type="ENTERO"
          onChange={(v) => updateParam("academicos", "semanas_sprint", v)}
        />
        <ParamRow
          label="Nota mínima de aprobación"
          paramKey="nota_minima_aprobacion"
          value={params.academicos.nota_minima_aprobacion}
          type="ENTERO"
          onChange={(v) => updateParam("academicos", "nota_minima_aprobacion", v)}
        />
      </SectionCard>

      {/* Sección 3: Seguridad y Sistema */}
      <SectionCard
        icon="S"
        iconBg="#c0392b"
        title="Seguridad y Sistema"
        onSave={() => handleSave("seguridad")}
      >
        <ParamRow
          label="Bitácora activa"
          paramKey="bitacora_activa"
          value={params.seguridad.bitacora_activa}
          type="BOOLEANO"
          onChange={(v) => updateParam("seguridad", "bitacora_activa", v)}
        />
        <ParamRow
          label="Proyectos públicos"
          paramKey="proyectos_publicos"
          value={params.seguridad.proyectos_publicos}
          type="BOOLEANO"
          onChange={(v) => updateParam("seguridad", "proyectos_publicos", v)}
        />
        <div style={{ borderBottom: "none" }}>
          <ParamRow
            label="Modo de mantenimiento"
            paramKey="modo_mantenimiento"
            value={params.seguridad.modo_mantenimiento}
            type="BOOLEANO"
            onChange={(v) => updateParam("seguridad", "modo_mantenimiento", v)}
          />
        </div>
      </SectionCard>
    </div>
  );
}
