// RUTA: frontend/cypress/e2e/hu002_login.cy.js

const URL_LOGIN = 'http://localhost:5173/login'

beforeEach(() => {
  cy.clearLocalStorage()
  cy.visit(URL_LOGIN)
})

// ══════════════════════════════════════════════════════════════
// CP-08: Login exitoso redirige según rol
// ══════════════════════════════════════════════════════════════

it('CP-08a - Administrador redirige a /admin', () => {
  cy.get('#correo').type('administrador@ufps.edu.co')
  cy.get('#contrasena').type('Test1234')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/admin')
})

it('CP-08b - Docente redirige a /docente', () => {
  cy.get('#correo').type('docente@ufps.edu.co')
  cy.get('#contrasena').type('Test1234')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/docente')
})

it('CP-08c - Estudiante redirige a /estudiante', () => {
  cy.get('#correo').type('estudiante@ufps.edu.co')
  cy.get('#contrasena').type('Test1234')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/estudiante')
})

it('CP-08d - Director redirige a /director', () => {
  cy.get('#correo').type('director@ufps.edu.co')
  cy.get('#contrasena').type('Test1234')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/director')
})

it('CP-08e - Líder de equipo redirige a /lider', () => {
  cy.get('#correo').type('lider_equipo@ufps.edu.co')
  cy.get('#contrasena').type('Test1234')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/lider') // ⚠️ ajusta si tu ruta es diferente
})

// ══════════════════════════════════════════════════════════════
// CP-09: Credenciales inválidas
// ══════════════════════════════════════════════════════════════

it('CP-09 - Credenciales incorrectas muestran error en pantalla', () => {
  cy.get('#correo').type('administrador@ufps.edu.co')
  cy.get('#contrasena').type('ContrasenaMal!')
  cy.get('button[type="submit"]').click()

  cy.url().should('include', '/login')

  cy.contains(/credenciales|contraseña incorrecta|inválido/i).should('be.visible')
})

// ══════════════════════════════════════════════════════════════
// CP-10: Token expirado
// ══════════════════════════════════════════════════════════════

it('CP-10 - Token expirado redirige a /login', () => {
  cy.window().then(win => {
    win.localStorage.setItem('access_token', 'token.expirado.invalido')
  })

  cy.visit('http://localhost:5173/admin')

  cy.url().should('include', '/login')
})