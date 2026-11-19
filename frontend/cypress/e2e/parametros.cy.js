// RUTA: frontend/cypress/e2e/parametros.cy.js
// HU-035 — Configuración de parámetros del sistema.
// Usa cypress.administrador@example.com (seed_cypress). Los parámetros que cambia
// (correo de soporte y % de alerta del semáforo) se guardan antes y se restauran al terminar.

const URL_CONFIGURACION = '/admin/configuracion'
const CLAVES_MODIFICADAS = ['correo_soporte', 'umbral_porcentaje_alerta']

const originales = {}

// Valores actuales de los parámetros, leídos de la API: { clave: valor }
function leerParametros() {
  return cy.api('administrador', 'GET', '/api/configuracion/').then(({ body }) => {
    const valores = {}
    Object.values(body).filter(Array.isArray).flat()
      .forEach(p => { valores[p.clave] = p.valor })
    return valores
  })
}

const inputDe = etiqueta => cy.contains('div', etiqueta).parent().parent().find('input')

// Guarda la sección y espera a que el backend acepte sus n parámetros (un PATCH 200 por cada uno).
function guardarSeccion(titulo, n) {
  cy.intercept('PATCH', '**/api/configuracion/*/').as('guardarParametro')
  cy.contains('span', titulo).parent().parent().contains('button', 'Guardar sección').click()
  // Con una sola petición cy.wait devuelve un objeto, no una lista
  cy.wait(Array(n).fill('@guardarParametro')).then(r => {
    [].concat(r).forEach(({ response }) => expect(response.statusCode).to.eq(200))
  })
}

function abrirConfiguracion() {
  cy.intercept('GET', '**/api/configuracion/').as('cargarParametros')
  cy.login('administrador')
  cy.visit(URL_CONFIGURACION)
  cy.contains('h1', 'Configuración de Parámetros').should('be.visible')
  // En desarrollo React (StrictMode) carga los parámetros dos veces; si se escribe antes de
  // que termine la segunda carga, esta pisa lo escrito. Se espera a que terminen todas.
  cy.get('@cargarParametros.all').should(cargas => {
    expect(cargas.length).to.be.greaterThan(0)
    cargas.forEach(c => expect(c.response, 'respuesta de la carga').to.exist)
  })
}

before(() => {
  cy.task('seedCypress', null, { timeout: 120000 })
  leerParametros().then(valores => {
    CLAVES_MODIFICADAS.forEach(clave => { originales[clave] = valores[clave] })
  })
})

after(() => {
  CLAVES_MODIFICADAS.forEach(clave => {
    if (originales[clave] !== undefined) {
      cy.api('administrador', 'PATCH', `/api/configuracion/${clave}/`, { valor: originales[clave] })
    }
  })
})

describe('HU-035 - Configuración de Parámetros', () => {

  it('CA-01: Administrador modifica un parámetro de texto y el sistema lo aplica', () => {
    const nuevoCorreo = `soporte.cypress${Date.now()}@example.com`
    abrirConfiguracion()

    inputDe('Correo de Soporte').clear().type(nuevoCorreo)
    guardarSeccion('Información Institucional', 1)

    // Persistencia: al volver a abrir la pantalla se lee el valor guardado
    abrirConfiguracion()
    inputDe('Correo de Soporte').should('have.value', nuevoCorreo)
  })

  it('CA-01: Modificar un umbral del semáforo (entero)', () => {
    // Un valor distinto del actual, dentro del rango 0-100
    const nuevo = Number(originales.umbral_porcentaje_alerta) === 30 ? '31' : '30'
    abrirConfiguracion()

    inputDe('% Actividades incumplidas para Amarillo').type(`{selectAll}${nuevo}`)
    inputDe('% Actividades incumplidas para Amarillo').should('have.value', nuevo)
    guardarSeccion('Umbrales del Semáforo Académico', 4)

    leerParametros().its('umbral_porcentaje_alerta').should('eq', nuevo)
  })

  it('CA-02: Validación en frontend - un porcentaje no puede superar 100', () => {
    abrirConfiguracion()

    inputDe('% Actividades incumplidas para Amarillo').type('{selectAll}150')

    inputDe('% Actividades incumplidas para Amarillo').should('have.value', '100')
  })

  it('CA-02: Validación en frontend - una nota no puede superar 5', () => {
    abrirConfiguracion()

    inputDe('Nota crítica (Riesgo Rojo').type('{selectAll}9')

    inputDe('Nota crítica (Riesgo Rojo').should('have.value', '5')
  })

  it('CA-02: Validación en backend - el valor es obligatorio', () => {
    cy.api('administrador', 'PATCH', '/api/configuracion/umbral_porcentaje_alerta/', {})
      .its('status').should('eq', 400)
  })

  it('CA-03: Un usuario que no es administrador no puede cambiar parámetros', () => {
    cy.api('docente', 'PATCH', '/api/configuracion/umbral_porcentaje_alerta/', { valor: '99' })
      .its('status').should('eq', 403)
  })

  it('Verificar que existen las secciones de parámetros', () => {
    abrirConfiguracion()

    cy.contains('Información Institucional').should('be.visible')
    cy.contains('Umbrales del Semáforo Académico').should('be.visible')
  })
})
