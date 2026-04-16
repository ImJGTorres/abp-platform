const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
// Sesión / Tokens

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
    ;['access_token', 'refresh_token', 'user'].forEach(k =>
      localStorage.removeItem(k)
    )
  },
  isAuthenticated: () => !!localStorage.getItem('access_token'),
}


// Parsear respuesta JSON, manejando casos de error y respuestas vacías

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

// Cliente HTTP base

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const token = session.getAccess()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let response

  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers,
    })
  } catch {
    throw { type: 'network', message: 'Sin conexión con el servidor' }
  }

  //Intentar refresh automático
  if (response.status === 401) {
    const refreshed = await tryRefresh()

    if (refreshed) {
      headers['Authorization'] = `Bearer ${session.getAccess()}`

      try {
        response = await fetch(`${BASE_URL}${path}`, {
          ...options,
          headers,
        })
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

// Auth API
export const authApi = {
  async login(correo, contrasena) {
    let response

    try {
      response = await request('/api/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ correo, contrasena }),
      })
    } catch {
      throw { type: 'network', message: 'Sin conexión con el servidor' }
    }

    const data = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data }
    }

    // Decodificar JWT
    const decodeJWT = (token) => {
      try {
        const base64 = token
          .split('.')[1]
          .replace(/-/g, '+')
          .replace(/_/g, '/')

        return JSON.parse(atob(base64))
      } catch {
        return null
      }
    }

    const payload = decodeJWT(data.access)

    const user = {
      id: payload?.user_id,
      nombre: payload?.nombre,
      correo: payload?.correo,
      tipo_rol: payload?.tipo_rol,
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
        // silencioso
      }
    }

    session.clear()
  },
}

// Usuarios API

export const usuariosApi = {
  async crear({ nombre, apellido, correo, contrasena, tipo_rol }) {
    const response = await request('/api/usuarios/', {
      method: 'POST',
      body: JSON.stringify({
        nombre,
        apellido,
        correo,
        contrasena,
        tipo_rol,
      }),
    })

    const data = await parseJSON(response)

    if (!response.ok) {
      throw { status: response.status, data }
    }

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