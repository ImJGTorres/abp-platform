/**
 * Utilidades para el manejo centralizado de errores de la API.
 *
 * Criterio de nomenclatura:
 *   - Variables, funciones y comentarios del dominio de negocio: español.
 *   - Términos técnicos estándar de la industria (API, cache, token, handler): inglés.
 */

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
