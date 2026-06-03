/**
 * Hook y validadores reutilizables para formularios React.
 *
 * Uso básico:
 *   const { validar } = useFormValidation(form, {
 *     nombre:    [required()],
 *     porcentaje: [required(), between(1, 100)],
 *   })
 *
 *   const { esValido, errores } = validar()
 */

/**
 * Valida que el campo no esté vacío.
 *
 * @param {string} [mensaje] - Mensaje personalizado de error.
 * @returns {Function} Función validadora que recibe el valor del campo.
 */
export const required = (mensaje) => (valor) => {
  if (!valor || !String(valor).trim()) {
    return mensaje || 'Campo obligatorio.'
  }
  return null
}

/**
 * Valida que el valor sea mayor o igual al mínimo.
 *
 * @param {number} n - Valor mínimo permitido (inclusivo).
 * @param {string} [mensaje] - Mensaje personalizado de error.
 * @returns {Function} Función validadora.
 */
export const minValue = (n, mensaje) => (valor) => {
  if (parseFloat(valor) < n) {
    return mensaje || `El valor mínimo es ${n}.`
  }
  return null
}

/**
 * Valida que el valor sea menor o igual al máximo.
 *
 * @param {number} n - Valor máximo permitido (inclusivo).
 * @param {string} [mensaje] - Mensaje personalizado de error.
 * @returns {Function} Función validadora.
 */
export const maxValue = (n, mensaje) => (valor) => {
  if (parseFloat(valor) > n) {
    return mensaje || `El valor máximo es ${n}.`
  }
  return null
}

/**
 * Valida que el valor esté dentro de un rango (inclusivo en ambos extremos).
 *
 * @param {number} min - Límite inferior.
 * @param {number} max - Límite superior.
 * @param {string} [mensaje] - Mensaje personalizado de error.
 * @returns {Function} Función validadora.
 */
export const between = (min, max, mensaje) => (valor) => {
  const n = parseFloat(valor)
  if (isNaN(n) || n < min || n > max) {
    return mensaje || `El valor debe estar entre ${min} y ${max}.`
  }
  return null
}

/**
 * Hook para validar un formulario contra un conjunto de reglas.
 *
 * @param {object} form - Estado actual del formulario ({ campo: valor }).
 * @param {object} reglas - Mapa de reglas: { campo: [fn_validadora, ...] }.
 *   Cada función validadora recibe el valor del campo y retorna un string de
 *   error o null si el valor es válido.
 * @returns {{ validar: Function }} Objeto con la función validar.
 */
export function useFormValidation(form, reglas) {
  /**
   * Ejecuta todas las reglas sobre el estado actual del formulario.
   *
   * @returns {{ esValido: boolean, errores: object }} Resultado de la validación.
   */
  function validar() {
    const errores = {}
    for (const [campo, validadores] of Object.entries(reglas)) {
      for (const validador of validadores) {
        const mensaje = validador(form[campo])
        if (mensaje) {
          errores[campo] = mensaje
          break
        }
      }
    }
    return { esValido: Object.keys(errores).length === 0, errores }
  }

  return { validar }
}
