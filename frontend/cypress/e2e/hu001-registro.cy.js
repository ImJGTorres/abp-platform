// RUTA: frontend/cypress/e2e/hu001_registro_usuario.cy.js

const URL_REGISTRO = 'http://localhost:5173/admin/registro'
const URL_LOGIN    = 'http://localhost:5173/login'

beforeEach(() => {
  cy.clearLocalStorage()

  // Login real
  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type('administrador@ufps.edu.co')
  cy.get('[name="contrasena"]').type('Test1234')
  cy.contains('Iniciar sesión').click()

cy.url().should('include', '/admin')
  // Ir a registro
  cy.visit(URL_REGISTRO)
})

it('CP-01 - Registro exitoso muestra confirmación', () => {
  const correo = `ana${Date.now()}@ufps.edu.co`

  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')

  cy.get('button[type="submit"]').click()

  cy.contains('Usuario creado correctamente.').should('be.visible')
})

it('CP-02 - Correo duplicado muestra error sin limpiar formulario', () => {
  const correo = `ana_dup${Date.now()}@ufps.edu.co`

  // Crear usuario primero
  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')
  cy.get('button[type="submit"]').click()

  cy.contains('Usuario creado correctamente.').should('be.visible')

  // Intentar duplicado
  cy.visit(URL_REGISTRO)

  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')
  cy.get('button[type="submit"]').click()

  cy.get('[role="alert"]').should('be.visible')
})

it('CP-03 - Sin token de admin redirige a login', () => {
  cy.clearLocalStorage()

  cy.visit(URL_REGISTRO)

  cy.url().should('include', '/login')
})