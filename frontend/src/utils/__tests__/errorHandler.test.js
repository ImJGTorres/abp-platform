import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import { avisarSiProhibido, mensajeDeError } from '../errorHandler'

vi.mock('react-hot-toast', () => ({ default: { error: vi.fn() } }))

describe('mensajeDeError', () => {
  it('usa el detail del backend', () => {
    expect(mensajeDeError({ data: { detail: 'Sin acceso al curso.' } }, 'x')).toBe('Sin acceso al curso.')
  })

  it('usa el campo error si no hay detail', () => {
    expect(mensajeDeError({ data: { error: 'Cupo lleno.' } }, 'x')).toBe('Cupo lleno.')
  })

  it('usa el texto por defecto si el backend no envió mensaje', () => {
    expect(mensajeDeError({ data: {} }, 'Por defecto')).toBe('Por defecto')
    expect(mensajeDeError(undefined, 'Por defecto')).toBe('Por defecto')
  })
})

describe('avisarSiProhibido', () => {
  beforeEach(() => toast.error.mockClear())

  it('ante un 403 muestra un toast con el mensaje del backend y retorna true', () => {
    const err = { status: 403, data: { detail: 'No eres el docente de este curso.' } }

    expect(avisarSiProhibido(err)).toBe(true)
    expect(toast.error).toHaveBeenCalledWith('No eres el docente de este curso.', { id: 'api-403' })
  })

  it('ante un 403 sin mensaje usa un texto genérico de permiso', () => {
    expect(avisarSiProhibido({ status: 403, data: {} })).toBe(true)
    expect(toast.error).toHaveBeenCalledWith('No tienes permiso para realizar esta acción.', { id: 'api-403' })
  })

  it('con otros errores no muestra toast y retorna false', () => {
    expect(avisarSiProhibido({ status: 400, data: { detail: 'Datos inválidos.' } })).toBe(false)
    expect(avisarSiProhibido(new Error('red'))).toBe(false)
    expect(toast.error).not.toHaveBeenCalled()
  })
})
