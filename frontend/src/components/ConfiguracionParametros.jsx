import { useState, useEffect } from "react";
import { configuracionApi } from "../services/api";
import IdentidadInstitucional from "./IdentidadInstitucional";

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

function ParamRow({ label, paramKey, value, type, onChange, min = null, max = null }) {
  const handleChange = (val) => {
    if (min !== null && type === "ENTERO") {
      const num = parseInt(val) || 0;
      if (num < min) val = min;
      else if (max !== null && num > max) val = max;
      else val = num;
    } else if (type === "DECIMAL") {
      let num = parseFloat(val);
      if (isNaN(num)) num = 0;
      if (min !== null && num < min) num = min;
      if (max !== null && num > max) num = max;
      val = num;
    }
    onChange(val);
  };

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "260px 1fr",
      alignItems: "center",
      gap: 16,
      padding: "12px 20px",
      borderBottom: "1px solid #fecdd3",
    }}>
      <div>
        <div style={{ fontSize: 13, color: "#374151", fontWeight: 500 }}>{label}</div>
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
        ) : type === "ENTERO" || type === "DECIMAL" ? (
          <input
            type="number"
            step={type === "DECIMAL" ? "0.1" : "1"}
            min={min ?? undefined}
            max={max ?? undefined}
            value={value ?? ""}
            onChange={(e) => handleChange(e.target.value)}
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
            value={value ?? ""}
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
  const [params, setParams] = useState({
    institucional: {
      correo_soporte: "",
    },
    semaforo: {
      umbral_nota_bajo_rendimiento: 3.0,
      umbral_porcentaje_actividades_incumplidas: 50,
      umbral_nota_alerta: 3.5,
      umbral_porcentaje_alerta: 25,
    },
  });
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    cargarParametros();
  }, []);

  async function cargarParametros() {
    try {
      setLoading(true);
      setError("");
      const data = await configuracionApi.getParametros();

      const mapped = {
        institucional: { correo_soporte: "" },
        semaforo: {
          umbral_nota_bajo_rendimiento: 3.0,
          umbral_porcentaje_actividades_incumplidas: 50,
          umbral_nota_alerta: 3.5,
          umbral_porcentaje_alerta: 25,
        },
      };

      Object.values(data).forEach((lista) => {
        if (Array.isArray(lista)) {
          lista.forEach((p) => {
            if (p.clave === "correo_soporte") mapped.institucional.correo_soporte = p.valor_casteado;
            if (p.clave === "umbral_nota_bajo_rendimiento") mapped.semaforo.umbral_nota_bajo_rendimiento = Number(p.valor_casteado);
            if (p.clave === "umbral_porcentaje_actividades_incumplidas") mapped.semaforo.umbral_porcentaje_actividades_incumplidas = Number(p.valor_casteado);
            if (p.clave === "umbral_nota_alerta") mapped.semaforo.umbral_nota_alerta = Number(p.valor_casteado);
            if (p.clave === "umbral_porcentaje_alerta") mapped.semaforo.umbral_porcentaje_alerta = Number(p.valor_casteado);
          });
        }
      });

      setParams(mapped);
    } catch (err) {
      setError(err.message || "Error al cargar parámetros");
    } finally {
      setLoading(false);
    }
  }

  function updateParam(section, key, value) {
    setParams((prev) => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }));
  }

  function handleSave(section) {
    const sectionMap = {
      institucional: {
        correo_soporte: "correo_soporte",
      },
      semaforo: {
        umbral_nota_bajo_rendimiento: "umbral_nota_bajo_rendimiento",
        umbral_porcentaje_actividades_incumplidas: "umbral_porcentaje_actividades_incumplidas",
        umbral_nota_alerta: "umbral_nota_alerta",
        umbral_porcentaje_alerta: "umbral_porcentaje_alerta",
      },
    };

    const claves = sectionMap[section];
    const valores = params[section];

    Promise.all(
      Object.entries(valores).map(([key, value]) => {
        const claveBackend = claves[key];
        return configuracionApi.actualizarParametro(claveBackend, value);
      })
    )
      .then(() => {
        setToast("Cambios guardados satisfactoriamente");
        setTimeout(() => setToast(""), 4000);
      })
      .catch((err) => {
        setToast(err.message || "Error al guardar");
        setTimeout(() => setToast(""), 4000);
      });
  }

  if (loading) {
    return (
      <div style={{ padding: "32px 40px", textAlign: "center", color: "#6b7280" }}>
        Cargando...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "32px 40px", textAlign: "center", color: "#dc2626" }}>
        {error}
      </div>
    );
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
          label="Correo de Soporte"
          paramKey="correo_soporte"
          value={params.institucional.correo_soporte}
          type="TEXTO"
          onChange={(v) => updateParam("institucional", "correo_soporte", v)}
        />
      </SectionCard>

      {/* Sección 2: Umbrales del Semáforo Académico */}
      <SectionCard
        icon="S"
        iconBg="#d32f2f"
        title="Umbrales del Semáforo Académico (RF34)"
        onSave={() => handleSave("semaforo")}
      >
        <ParamRow
          label="Nota crítica (Riesgo Rojo - Escala 0 a 5)"
          paramKey="umbral_nota_bajo_rendimiento"
          value={params.semaforo.umbral_nota_bajo_rendimiento}
          type="DECIMAL"
          min={0}
          max={5}
          onChange={(v) => updateParam("semaforo", "umbral_nota_bajo_rendimiento", v)}
        />
        <ParamRow
          label="% Actividades incumplidas para Rojo (0 a 100%)"
          paramKey="umbral_porcentaje_actividades_incumplidas"
          value={params.semaforo.umbral_porcentaje_actividades_incumplidas}
          type="ENTERO"
          min={0}
          max={100}
          onChange={(v) => updateParam("semaforo", "umbral_porcentaje_actividades_incumplidas", v)}
        />
        <ParamRow
          label="Nota preventiva (Alerta Amarillo - Escala 0 a 5)"
          paramKey="umbral_nota_alerta"
          value={params.semaforo.umbral_nota_alerta}
          type="DECIMAL"
          min={0}
          max={5}
          onChange={(v) => updateParam("semaforo", "umbral_nota_alerta", v)}
        />
        <ParamRow
          label="% Actividades incumplidas para Amarillo (0 a 100%)"
          paramKey="umbral_porcentaje_alerta"
          value={params.semaforo.umbral_porcentaje_alerta}
          type="ENTERO"
          min={0}
          max={100}
          onChange={(v) => updateParam("semaforo", "umbral_porcentaje_alerta", v)}
        />
      </SectionCard>

      {/* Sección 3: Identidad institucional */}
      <IdentidadInstitucional />
    </div>
  );
}