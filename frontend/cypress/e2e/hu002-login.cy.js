// RUTA: frontend/cypress/e2e/hu002-login.cy.js
// HU-002 — Inicio de sesión y redirección según el rol.
// Usa los usuarios cypress.<rol>@example.com (seed_cypress).

import { PASSWORD, correoDe } from '../support/datos'

function loginPorPantalla(correo, contrasena) {
  cy.get('#correo').type(correo)
  cy.get('#contrasena').type(contrasena, { log: false })
  cy.get('button[type="submit"]').click()
}

before(() => {
  cy.task('seedCypress', null, { timeout: 120000 })
})

beforeEach(() => {
  cy.clearLocalStorage()
  cy.visit('/login')
})

// ══════════════════════════════════════════════════════════════
// CP-08: Login exitoso redirige según rol
// ══════════════════════════════════════════════════════════════

const REDIRECCIONES = [
  ['CP-08a', 'Administrador', 'administrador', '/admin'],
  ['CP-08b', 'Docente', 'docente', '/docente'],
  ['CP-08c', 'Estudiante', 'estudiante', '/estudiante'],
  ['CP-08d', 'Director', 'director', '/director'],
  ['CP-08e', 'Líder de equipo', 'lider_equipo', '/lider'],
]

REDIRECCIONES.forEach(([cp, nombre, rol, ruta]) => {
  it(`${cp} - ${nombre} redirige a ${ruta}`, () => {
    loginPorPantalla(correoDe(rol), PASSWORD)

    cy.url().should('include', ruta)
  })
})

// ══════════════════════════════════════════════════════════════
// CP-09: Credenciales inválidas
// ══════════════════════════════════════════════════════════════

it('CP-09 - Credenciales incorrectas muestran error en pantalla', () => {
  loginPorPantalla(correoDe('administrador'), 'ContrasenaMal!')

  cy.url().should('include', '/login')
  cy.contains(/credenciales|contraseña incorrecta|inválid/i).should('be.visible')
})

// ══════════════════════════════════════════════════════════════
// CP-10: Token inválido
// ══════════════════════════════════════════════════════════════

it('CP-10 - Token inválido redirige a /login', () => {
  cy.window().then(win => {
    win.localStorage.setItem('access_token', 'token.expirado.invalido')
  })

  cy.visit('/admin')

  cy.url().should('include', '/login')
})
