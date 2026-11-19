/**
 * Utilidades para el manejo centralizado de errores de la API.
 *
 * Criterio de nomenclatura:
 *   - Variables, funciones y comentarios del dominio de negocio: español.
 *   - Términos técnicos estándar de la industria (API, cache, token, handler): inglés.
 */

import toast from 'react-hot-toast'

const MENSAJE_SIN_PERMISO = 'No tienes permiso para realizar esta acción.'

/**
 * Mensaje legible de un error de la API: detail (DRF), error, o el texto por defecto.
 *
 * @param {object} error - Error capturado en catch ({ status, data }).
 * @param {string} porDefecto - Texto si el backend no envió un mensaje.
 * @returns {string}
 */
export function mensajeDeError(error, porDefecto) {
  const data = error?.data
  if (typeof data === 'string' && data) return data
  return data?.detail || data?.error || porDefecto
}

/**
 * Si la API respondió 403, muestra un toast con el mensaje del backend y retorna true.
 * El permiso real lo decide el backend; esto solo informa al usuario por qué no se hizo.
 *
 * @param {object} error - Error capturado en catch ({ status, data }).
 * @returns {boolean} true si era un 403 (ya avisado), false en otro caso.
 */
export function avisarSiProhibido(error) {
  if (error?.status !== 403) return false
  // id fijo: si varias peticiones fallan a la vez, se muestra un solo toast
  toast.error(mensajeDeError(error, MENSAJE_SIN_PERMISO), { id: 'api-403' })
  return true
}

/**
 * Extrae y normaliza errores de una respuesta de la API.
 *
 * Prioridad de extracción:
 *   1. Errores por campo en error.data (asignados vía setErrores).
 *   2. non_field_errors en error.data (retornado como string).
 *   3. Mensaje genérico si no hay estructura reconocida.
 *
 * @param {object} error - Error capturado en catch. Se espera que tenga propiedad .data
 *   con la respuesta del servidor (estructura DRF estándar).
 * @param {Function} setErrores - Setter de estado React para errores por campo.
 * @returns {string|null} Mensaje de error genérico para mostrar, o null si los
 *   errores ya fueron asignados por campo vía setErrores.
 */
export function handleApiError(error, setErrores) {
  const data = error?.data

  if (!data) {
    return 'Error de conexión. Verifica tu red e intenta de nuevo.'
  }

  if (data.non_field_errors) {
    return Array.isArray(data.non_field_errors)
      ? data.non_field_errors[0]
      : data.non_field_errors
  }

  const camposError = {}
  for (const [campo, mensajes] of Object.entries(data)) {
    camposError[campo] = Array.isArray(mensajes) ? mensajes[0] : mensajes
  }

  if (Object.keys(camposError).length > 0) {
    setErrores(prev => ({ ...prev, ...camposError }))
    return null
  }

  return 'Error inesperado. Intenta de nuevo.'
}
