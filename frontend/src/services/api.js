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

// Refresh de token
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
export { request }

// Auth y usuarios
//   POST /api/auth/login/   → LoginView  (SimpleJWT personalizado) — obtiene access y refresh tokens
//   POST /api/auth/logout/  → LogoutView (SimpleJWT personalizado) — hace blacklist del refresh token

export const authApi = {
  async login(correo, contrasena) {
    // Usa fetch directo (no request()) para evitar que el interceptor de 401
    // intente hacer refresh y recargue la página cuando las credenciales son incorrectas.
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

    const user = {
      id: payload?.user_id,   // refresh['user_id'] = usuario.id
      nombre: payload?.nombre,    // refresh['nombre']
      correo: payload?.correo,    // refresh['correo']
      tipo_rol: payload?.tipo_rol,  // refresh['tipo_rol']
    }

    session.save(data.access, data.refresh, user)

    // Obtener foto_perfil desde el perfil (no viene en el JWT)
    try {
      const perfilRes = await fetch(`${BASE_URL}/api/usuarios/perfil/`, {
        headers: { Authorization: `Bearer ${data.access}` },
      })
      if (perfilRes.ok) {
        const perfil = await perfilRes.json()
        const userConFoto = { ...user, foto_perfil: perfil.foto_perfil ?? null }
        session.save(data.access, data.refresh, userConFoto)
        return userConFoto
      }
    } catch {
      // Si falla el fetch del perfil no bloqueamos el login
    }

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

  // POST /api/auth/olvidar-contrasena/
  async olvidarContrasena(correo) {
    const response = await request('/api/auth/olvidar-contrasena/', {
      method: 'POST',
      body: JSON.stringify({ correo }),
    })
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },

  // POST /api/auth/recuperar-contrasena/
  async recuperarContrasena({ token, nueva_contrasena, confirmar_contrasena }) {
    const response = await request('/api/auth/recuperar-contrasena/', {
      method: 'POST',
      body: JSON.stringify({ token, nueva_contrasena, confirmar_contrasena }),
    })
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },
  // POST /api/auth/cambiar-contrasena/ (usuario autenticado)
  async cambiarContrasena(data) {
    const response = await request('/api/auth/cambiar-contrasena/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    const resData = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data: resData }
    return resData
  }

}

// Usuarios
//   POST   /api/usuarios/             → UsuarioCreateView  — crea un usuario
//   GET    /api/usuarios/perfil/      → UsuarioPerfilView  — obtiene el perfil del usuario autenticado
//   PATCH  /api/usuarios/perfil/      → UsuarioPerfilView  — actualización parcial del perfil

export const usuariosApi = {
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

  async cargaMasiva(archivo) {
    const formData = new FormData()
    formData.append('archivo', archivo)

    const token = session.getAccess()
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    let response
    try {
      response = await fetch(`${BASE_URL}/api/usuarios/carga-masiva/`, {
        method: 'POST',
        headers,
        body: formData,
      })
    } catch {
      throw { type: 'network', message: 'Sin conexión con el servidor' }
    }

    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
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
// Endpoints (apps/configuracion/urls.py incluido en /api/configuracion/):
//   GET  /api/configuracion/         → ConfiguracionListView  — lista todos los parámetros
//   PATCH /api/configuracion/:clave/ → ConfiguracionDetailView — actualización parcial de un parámetro

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

// Periodos Académicos API
export const periodosApi = {
  async listar() {
    const response = await request('/api/configuracion/periodos/')
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },
  async crear(data) {
    const response = await request('/api/configuracion/periodos/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    const result = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data: result }
    return result
  },
  async editar(id, campos) {
    const response = await request(`/api/configuracion/periodos/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(campos),
    })
    const result = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data: result }
    return result
  },
  async eliminar(id) {
    const response = await request(`/api/configuracion/periodos/${id}/`, { method: 'DELETE' })
    if (!response.ok) {
      const data = await parseJSON(response)
      throw { status: response.status, data }
    }
  },
}

// Roles
//
// Endpoints (apps/roles/urls.py incluido en /api/roles/):
//   GET    /api/roles/             → RolListCreateView  — lista todos los roles
//   POST   /api/roles/             → RolListCreateView  — crea un rol
//   GET    /api/roles/:id/         → RolDetailView      — detalle con permisos anidados
//   PATCH  /api/roles/:id/         → RolDetailView      — actualización parcial
//   DELETE /api/roles/:id/         → RolDetailView      — elimina un rol
//   GET    /api/roles/permisos/    → PermisoListCreateView — lista todos los permisos

export const rolesApi = {
  /**
   * GET /api/roles/
   * Response 200: [{ id, nombre, descripcion, estado, total_usuarios }]
   */
  async listar() {
    const response = await request('/api/roles/')
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },

  /**
   * GET /api/roles/:id/
   * Response 200: { id, nombre, descripcion, estado, fecha_creacion, permisos: [{id, codigo, modulo, descripcion}] }
   */
  async obtener(id) {
    const response = await request(`/api/roles/${id}/`)
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },

  /**
   * POST /api/roles/
   * Request:  { nombre, descripcion }
   * Response 201: { id, nombre, descripcion, estado, fecha_creacion, permisos: [] }
   */
  async crear({ nombre, descripcion }) {
    const response = await request('/api/roles/', {
      method: 'POST',
      body: JSON.stringify({ nombre, descripcion }),
    })
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },

  /**
   * PATCH /api/roles/:id/
   * Request:  { nombre?, descripcion?, estado?, permiso_ids?: [id, id, ...] }
   *   — permiso_ids reemplaza TODOS los permisos del rol (RolSerializer.update)
   * Response 200: { id, nombre, descripcion, estado, fecha_creacion, permisos: [...] }
   */
  async editar(id, campos) {
    const response = await request(`/api/roles/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(campos),
    })
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },

  /**
   * DELETE /api/roles/:id/
   * Response 204: sin cuerpo
   */
  async eliminar(id) {
    const response = await request(`/api/roles/${id}/`, { method: 'DELETE' })
    if (!response.ok) {
      const data = await parseJSON(response)
      throw { status: response.status, data }
    }
  },

  /**
   * GET /api/roles/permisos/
   * Response 200: [{ id, codigo, modulo, descripcion }]
   */
  async listarPermisos() {
    const response = await request('/api/roles/permisos/')
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
    return data
  },
}

// Bitácora de Auditoría
// GET /api/bitacora/ → BitacoraListView (solo administradores)
// Filtros: modulo, accion, fecha_desde, fecha_hasta, page

export const bitacoraApi = {
  async listar({ modulo = '', accion = '', fecha_desde = '', fecha_hasta = '', page = 1 } = {}) {
    const params = new URLSearchParams()
    if (modulo) params.set('modulo', modulo)
    if (accion) params.set('accion', accion)
    if (fecha_desde) params.set('fecha_desde', fecha_desde)
    if (fecha_hasta) params.set('fecha_hasta', fecha_hasta)
    if (page > 1) params.set('page', String(page))
    const qs = params.toString()
    const response = await request(`/api/bitacora/${qs ? `?${qs}` : ''}`)
    const data = await parseJSON(response)
    if (!response.ok) throw { status: response.status, data }
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