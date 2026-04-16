// RUTA: frontend/cypress/e2e/hu001_registro_usuario.cy.js

const URL_REGISTRO = 'http://localhost:5173/admin/registro'
const URL_LOGIN    = 'http://localhost:5173/login'

beforeEach(() => {
  cy.clearLocalStorage()
  // Hacer login real con un admin que exista en tu BD local
  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type('administrador@ufps.edu.co')
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('button[type="submit"]').click()
  // Esperar a que redirija al panel de admin antes de continuar
  cy.url().should('include', '/admin')
  cy.visit(URL_REGISTRO)
})

it('CP-01 - Registro exitoso muestra confirmación', () => {
  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type('ana.prueba@ufps.edu.co')
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')
  cy.get('button[type="submit"]').click()
  cy.contains('Usuario creado correctamente.').should('be.visible')
})

it('CP-02 - Correo duplicado muestra error sin limpiar formulario', () => {
  cy.get('[name="nombre"]').type('Ana')
  cy.get('[name="apellido"]').type('Lopez')
  cy.get('[name="correo"]').type('ana.prueba@ufps.edu.co') // ya debe existir en BD
  cy.get('[name="contrasena"]').type('Test1234')
  cy.get('[name="confirmarContrasena"]').type('Test1234')
  cy.get('[name="tipo_rol"]').select('estudiante')
  cy.get('button[type="submit"]').click()
  cy.get('[role="alert"]').should('be.visible')
  cy.get('[name="correo"]').should('have.value', 'ana.prueba@ufps.edu.co')
})

it('CP-03 - Sin token de admin redirige a login', () => {
  cy.clearLocalStorage()
  cy.visit('http://localhost:5173/admin/registro')
  cy.url().should('include', '/login')
})