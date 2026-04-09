
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Sesión / tokens

export const session = {
  getAccess: () => localStorage.getItem('access_token'),
  getRefresh: () => localStorage.getItem('refresh_token'),
  getUser: () => {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  },
  save(access, refresh, user) {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('user', JSON.stringify(user))
  },
  clear() {
    ;['access_token', 'refresh_token', 'user'].forEach(k => localStorage.removeItem(k))
  },
  isAuthenticated: () => !!localStorage.getItem('access_token'),
}

//Parsear respuesta — protege contra HTML en errores 500

async function parseJSON(response) {
  const text = await response.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { detail: `Error del servidor (${response.status})` }
  }
}

//Refresh de token

async function tryRefresh() {
  const refresh = session.getRefresh()
  if (!refresh) return false
  try {
    const res = await fetch(`${BASE_URL}/api/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return false
    const data = await parseJSON(res)
    localStorage.setItem('access_token', data.access)
    return true
  } catch {
    return false
  }
}

//Cliente HTTP base

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = session.getAccess()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  } catch {
    // Backend caído o sin conexión
    throw { type: 'network', message: 'Sin conexión con el servidor' }
  }

  // Token expirado → intentar refresh automático
  if (response.status === 401) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${session.getAccess()}`
      try {
        response = await fetch(`${BASE_URL}${path}`, { ...options, headers })
      } catch {
        throw { type: 'network', message: 'Sin conexión con el servidor' }
      }
    } else {
      session.clear()
      window.location.href = '/login'
      throw { type: 'auth', message: 'Sesión expirada' }
    }
  }

  return response
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

// ── Mock temporal ────────────────────────────────────────────────────────────
// Activo mientras el backend de login no esté disponible.
// Cambia USE_MOCK a false cuando el endpoint POST /api/auth/login/ esté listo.
// Usuarios de prueba definidos abajo.

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const MOCK_USERS = [
  { correo: 'admin@ufps.edu.co', contrasena: '12345678', tipo_rol: 'administrador', nombre: 'Admin ABP', id: 1 },
  { correo: 'docente@ufps.edu.co', contrasena: '12345678', tipo_rol: 'docente', nombre: 'Docente Prueba', id: 2 },
  { correo: 'director@ufps.edu.co', contrasena: '12345678', tipo_rol: 'director', nombre: 'Director ABP', id: 3 },
  { correo: 'estudiante@ufps.edu.co', contrasena: '12345678', tipo_rol: 'estudiante', nombre: 'Est. Prueba', id: 4 },
  { correo: 'lider@ufps.edu.co', contrasena: '12345678', tipo_rol: 'lider_equipo', nombre: 'Líder Prueba', id: 5 },
]

function mockLogin(correo, contrasena) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const found = MOCK_USERS.find(u => u.correo === correo && u.contrasena === contrasena)
      if (found) {
        resolve({
          access: 'mock_access_' + Date.now(),
          refresh: 'mock_refresh_' + Date.now(),
          user: { id: found.id, nombre: found.nombre, correo: found.correo, tipo_rol: found.tipo_rol },
        })
      } else {
        reject({ status: 401, data: { detail: 'Credenciales inválidas.' } })
      }
    }, 700) // simula latencia de red
  })
}

export const authApi = {
  /**
   * POST /api/auth/login/
   * Espera:  { correo, contrasena }
   * Devuelve: usuario con { id, nombre, correo, tipo_rol }
   * Guarda access_token y refresh_token en localStorage.
   */
  async login(correo, contrasena) {
    // ── Mock activo ───────────────────────────────────────────────────────
    if (USE_MOCK) {
      const result = await mockLogin(correo, contrasena) // lanza { status: 401 } si falla
      session.save(result.access, result.refresh, result.user)
      return result.user
    }

    // ── Llamada real al backend ───────────────────────────────────────────
    let response
    try {
      response = await fetch(`${BASE_URL}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ correo, contrasena }),
      })
    } catch {
      throw { type: 'network', message: 'Sin conexión con el servidor' }
    }

    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }

    // Decodificar payload del JWT para obtener tipo_rol sin llamada extra (HU-002 ST-04)
    const payload = (() => {
      try { return JSON.parse(atob(data.access.split('.')[1])) }
      catch { return null }
    })()

    const user = {
      id: payload?.id_usuario ?? data.user?.id,
      nombre: payload?.nombre ?? data.user?.nombre,
      correo: payload?.correo ?? correo,
      tipo_rol: payload?.tipo_rol ?? data.user?.tipo_rol,
    }

    session.save(data.access, data.refresh, user)
    return user
  },

  /** POST /api/auth/logout/ — invalida el refresh token en el servidor */
  async logout() {
    const refresh = session.getRefresh()
    if (refresh && !USE_MOCK) {
      try {
        await request('/api/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh }),
        })
      } catch { /* silencioso: igual limpiamos sesión local */ }
    }
    session.clear()
  },
}

//Usuarios

export const usuariosApi = {
  /**
   * POST /api/usuarios/
   *
   * Campos aceptados por UsuarioSerializer (backend real):
   *   nombre      string, min 2 chars   — requerido
   *   apellido    string, min 2 chars   — requerido
   *   correo      email, único          — requerido
   *   contrasena  string, min 8 chars   — requerido (se hashea en servidor)
   *   tipo_rol    enum TipoRol          — requerido
   *
   * Omitidos intencionalmente: estado (default='activo'), telefono, foto_perfil
   *
   * Response 201: usuario creado (sin contrasena, write_only=True)
   * Response 400: { campo: ["mensaje"] }
   * Response 403: { detail: "..." } (cuando se active IsAdminUser)
   *
   * Lanza: { type: 'network' } | { status, data }
   */
  async crear({ nombre, apellido, correo, contrasena, tipo_rol }) {
    const response = await request('/api/usuarios/', {
      method: 'POST',
      body: JSON.stringify({ nombre, apellido, correo, contrasena, tipo_rol }),
    })

    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },
}

//Helpers

export function rutaPorRol(tipo_rol) {
  const rutas = {
    administrador: '/admin',
    docente: '/docente',
    director: '/director',
    lider_equipo: '/lider',
    estudiante: '/estudiante',
  }
  return rutas[tipo_rol] ?? '/login'
}