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

// ─── Parsear respuesta — protege contra HTML en errores 500 ──────────────────

async function parseJSON(response) {
  const text = await response.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { detail: `Error del servidor (${response.status})` }
  }
}

// ─── Refresh de token ─────────────────────────────────────────────────────────
// POST /api/auth/refresh/ — TokenRefreshView (SimpleJWT nativo)
// Con ROTATE_REFRESH_TOKENS: True y BLACKLIST_AFTER_ROTATION: True en settings,
// cada refresh devuelve un nuevo refresh token y el anterior queda en blacklist.

async function tryRefresh() {
  const refresh = session.getRefresh()
  if (!refresh) return false

  try {
    const res = await fetch(`${BASE_URL}/api/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })

    if (!res.ok) {
      session.clear()
      return false
    }

    const data = await parseJSON(res)
    // Con ROTATE_REFRESH_TOKENS, el backend devuelve también un nuevo refresh
    localStorage.setItem('access_token', data.access)
    if (data.refresh) {
      localStorage.setItem('refresh_token', data.refresh)
    }
    return true

  } catch {
    session.clear()
    return false
  }
}

//  Cliente HTTP base

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const token = session.getAccess()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw { type: 'network', message: 'Sin conexión con el servidor' }
  }

  // Token expirado → intentar refresh automático una vez
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
      // tryRefresh() ya llamó session.clear()
      window.location.href = '/login'
      throw { type: 'auth', message: 'Sesión expirada' }
    }
  }

  return response
}

// ─── Auth y usuarios

export const authApi = {
  /**
   * POST /api/auth/login/  → LoginView
   *
   * Request:
   *   correo     string — requerido
   *   contrasena string — requerido
   *
   * Response 200:
   *   { access, refresh }
   *
   * Claims en el JWT (definidos en LoginView):
   *   user_id   → usuario.id
   *   nombre    → usuario.nombre
   *   correo    → usuario.correo
   *   tipo_rol  → usuario.tipo_rol
   *
   * Errores:
   *   400 → { detail: 'correo y contrasena son requeridos.' }
   *   401 → { detail: 'Credenciales inválidas.' }
   *   401 → { detail: 'Usuario inactivo.' }  ← inactivo también es 401, no 403
   */
  async login(correo, contrasena) {
    const response = await request('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ correo, contrasena }),
    })

    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }

    const payload = (() => {
      try {
        const base64 = data.access
          .split('.')[1]
          .replace(/-/g, '+')
          .replace(/_/g, '/')
        return JSON.parse(atob(base64))
      } catch {
        return null
      }
    })()

    // Mapeo exacto de los claims definidos en LoginView
    const user = {
      id: payload?.user_id,   // refresh['user_id'] = usuario.id
      nombre: payload?.nombre,    // refresh['nombre']
      correo: payload?.correo,    // refresh['correo']
      tipo_rol: payload?.tipo_rol,  // refresh['tipo_rol']
    }

    session.save(data.access, data.refresh, user)
    return user
  },

  async logout() {
    const refresh = session.getRefresh()

    if (refresh) {
      try {
        await request('/api/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh }),
        })
      } catch {
        // Aunque falle el logout (ej. sin conexión), igual limpiamos sesión localmente
      }
    }

    session.clear()
  },
}

// ─── Usuarios ─────────────────────────────────────────────────────────────────

export const usuariosApi = {
  /**
   * POST /api/usuarios/  → UsuarioCreateView
   *
   * Permiso requerido: EsAdministrador
   *   → verifica request.user.tipo_rol == 'administrador'
   *   → resuelto por UsuarioJWTAuthentication (modelo propio)
   *
   * Request (UsuarioSerializer):
   *   nombre     string, min 2 chars  — requerido
   *   apellido   string, min 2 chars  — requerido
   *   correo     email, único         — requerido
   *   contrasena string, min 8 chars  — requerido (write_only, se hashea en servidor)
   *   tipo_rol   enum TipoRol         — requerido
   *
   * Omitidos: estado (default='activo'), telefono, foto_perfil (opcionales)
   *
   * Response 201: usuario creado (sin contrasena)
   * Response 400: { campo: ["mensaje"] }   ← errores DRF por campo
   * Response 403: { detail: "..." }        ← no es administrador
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

  async getPerfil() {
    const response = await request('/api/usuarios/perfil/')

    const data = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data }
    }

    return data
  },

  async actualizarPerfil(data) {
    const response = await request('/api/usuarios/perfil/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    })

    const result = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data: result }
    }

    return result
  },
}

// Configuración API

export const configuracionApi = {
  async getParametros() {
    const response = await request('/api/configuracion/')

    const data = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data }
    }

    return data
  },

  async actualizarParametro(clave, valor) {
    const response = await request(`/api/configuracion/${clave}/`, {
      method: 'PATCH',
      body: JSON.stringify({ valor }),
    })

    const data = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data }
    }

    return data
  },
}

// Helpers
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