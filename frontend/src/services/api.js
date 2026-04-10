const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const session = {
  getAccess: () => localStorage.getItem("access_token"),
  getRefresh: () => localStorage.getItem("refresh_token"),
  getUser: () => { const r = localStorage.getItem("user"); return r ? JSON.parse(r) : null; },
  save(access, refresh, user) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    localStorage.setItem("user", JSON.stringify(user));
  },
  clear() {
    ["access_token", "refresh_token", "user"].forEach(k => localStorage.removeItem(k));
  },
  isAuthenticated: () => !!localStorage.getItem("access_token"),
};

async function tryRefresh() {
  const refresh = session.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE_URL}/api/auth/refresh/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    localStorage.setItem("access_token", (await res.json()).access);
    return true;
  } catch { return false; }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = session.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    if (await tryRefresh()) {
      headers["Authorization"] = `Bearer ${session.getAccess()}`;
      return fetch(`${BASE_URL}${path}`, { ...options, headers });
    }
    session.clear(); window.location.href = "/login";
    throw new Error("Sesión expirada");
  }
  return res;
}

export const authApi = {
  async login(correo, contrasena) {
    const res = await fetch(`${BASE_URL}/api/auth/login/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correo, contrasena }),
    });
    const data = await res.json();
    if (!res.ok) throw { status: res.status, data };
    const p = (() => { try { return JSON.parse(atob(data.access.split(".")[1])); } catch { return null; } })();
    const user = {
      id: p?.id_usuario ?? data.user?.id, nombre: p?.nombre ?? data.user?.nombre,
      correo: p?.correo ?? correo, tipo_rol: p?.tipo_rol ?? data.user?.tipo_rol
    };
    session.save(data.access, data.refresh, user);
    return user;
  },
  async logout() {
    const refresh = session.getRefresh();
    if (refresh) { try { await request("/api/auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) }); } catch { } }
    session.clear();
  },
};

export const usuariosApi = {
  async crear({ nombre, apellido, correo, contrasena, tipo_rol }) {
    const res = await request("/api/usuarios/", {
      method: "POST",
      body: JSON.stringify({ nombre, apellido, correo, contrasena, tipo_rol }),
    });
    const data = await res.json();
    if (!res.ok) throw { status: res.status, data };
    return data;
  },
};

export function rutaPorRol(tipo_rol) {
  return { administrador: "/admin", docente: "/docente", director: "/director", estudiante: "/estudiante" }[tipo_rol] ?? "/";
}