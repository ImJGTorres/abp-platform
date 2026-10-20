// RUTA: frontend/cypress/e2e/hu042-panel-docente.cy.js
// SCRUM-557 (HU-042) — Panel de semáforos de proyectos para el docente.
// Datos de prueba: backend/apps/reportes/management/commands/seed_hu042_demo.py
// (correr antes de esta suite: python manage.py seed_hu042_demo)
// Reutiliza los 3 proyectos reales del docente demo de HU-040 (2 rojo, 1 verde).

const URL_LOGIN = 'http://localhost:5173/static/login'

function login(correo, contrasena) {
  // El menú lateral usa 'hidden lg:flex' (Tailwind, breakpoint 1024px); con el
  // viewport por defecto de Cypress queda oculto y no se puede navegar por clic.
  cy.viewport(1280, 800)
  cy.clearLocalStorage()
  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type(contrasena)
  cy.contains('Iniciar sesión').click()
}

beforeEach(() => {
  login('demo.docente.hu040@ufps.edu.co', 'Test1234')
  // El login puede tardar más que el timeout por defecto por la latencia de Supabase.
  cy.url({ timeout: 15000 }).should('include', '/docente')
  cy.contains('a', 'Semáforos').click()
  cy.url().should('include', '/docente/semaforos')
  cy.contains('h1', 'Panel de semáforos').should('be.visible')
})

// Escenario 1 — Vista panorámica de proyectos del docente
it('CA-01 - El docente ve una tarjeta por proyecto con su color y % de avance', () => {
  cy.contains('button', 'Todos').click()

  cy.get('[role="progressbar"][aria-label="Avance del proyecto"]').should('have.length', 3)
  cy.contains('Óptimo').scrollIntoView().should('be.visible')
  // cy.contains() solo devuelve un elemento; para contar repeticiones se filtra por texto.
  cy.get('a:contains("Riesgo crítico")').should('have.length', 2)

  cy.screenshot('hu042-ca01-panel-tarjetas-por-proyecto')
})

// Escenario 2 — Filtro por proyectos en riesgo
it('CA-02 - El filtro Rojo lista únicamente los proyectos con retrasos críticos', () => {
  cy.contains('button', 'Todos').click()
  cy.get('[role="progressbar"][aria-label="Avance del proyecto"]').should('have.length', 3)

  cy.contains('button', 'Rojo').click()

  cy.get('[role="progressbar"][aria-label="Avance del proyecto"]').should('have.length', 2)
  cy.get('a:contains("Riesgo crítico")').should('have.length', 2)
  cy.contains('Óptimo').should('not.exist')

  cy.screenshot('hu042-ca02-filtro-rojo')
})

// Escenario 3 — Acceso directo al proyecto
it('CA-03 - El clic en una tarjeta navega directamente al detalle del proyecto', () => {
  cy.contains('button', 'Todos').click()

  cy.contains('Ver detalle').first().click()

  cy.url().should('include', '/docente/proyectos/').and('include', '/monitoreo')
  cy.contains('h1', 'Monitoreo').should('be.visible')

  cy.screenshot('hu042-ca03-navega-al-detalle')
})
