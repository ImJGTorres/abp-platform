// RUTA: frontend/cypress/e2e/hu001-registro.cy.js
// HU-001 — Registro de usuarios por el administrador.
// Usa cypress.administrador@example.com (seed_cypress). Los usuarios que crea se llaman
// cypress.registro.<n>@example.com y se borran al terminar la spec.

const URL_REGISTRO = '/admin/registro'

const correoNuevo = sufijo => `cypress.registro.${sufijo}${Date.now()}@example.com`

function llenarFormulario(correo) {
  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')
  // La página también tiene la carga masiva con su propio submit: se usa el del registro
  cy.get('[name="tipo_rol"]').closest('form').find('button[type="submit"]').click()
}

before(() => {
  cy.task('seedCypress', null, { timeout: 120000 })
})

after(() => {
  cy.task('limpiarRegistrosCypress', null, { timeout: 120000 })
})

beforeEach(() => {
  cy.login('administrador')
  cy.visit(URL_REGISTRO)
})

it('CP-01 - Registro exitoso muestra confirmación', () => {
  llenarFormulario(correoNuevo('ok'))

  cy.contains('Usuario creado correctamente.').scrollIntoView().should('be.visible')
})

it('CP-02 - Correo duplicado muestra error sin limpiar formulario', () => {
  const correo = correoNuevo('dup')

  llenarFormulario(correo)
  cy.contains('Usuario creado correctamente.').scrollIntoView().should('be.visible')

  // Intentar registrar el mismo correo
  cy.visit(URL_REGISTRO)
  llenarFormulario(correo)

  // Error general (encima del formulario) o del campo correo, dentro de la tarjeta de registro
  cy.get('[name="tipo_rol"]').closest('form').parent()
    .find('[role="alert"]').first().scrollIntoView().should('be.visible')
  cy.get('[name="correo"]').should('have.value', correo)
})

it('CP-03 - Sin sesión de administrador redirige a login', () => {
  cy.clearLocalStorage()

  cy.visit(URL_REGISTRO)

  cy.url().should('include', '/login')
})
