// RUTA: frontend/cypress/e2e/hu040-calendario.cy.js
// SCRUM-536 (HU-040) — Calendario unificado, detalle de evento y recordatorio 48h.
// Datos de prueba: backend/apps/calendario/management/commands/seed_hu040_demo.py
// (correr antes de esta suite: python manage.py seed_hu040_demo)

// NOTA: vite.config.js tiene base:'/static/', así que el dev server local solo sirve
// bajo ese prefijo (http://localhost:5173/static/...). El router tiene una ruta catch-all
// ('*' -> /login) que intercepta cualquier cy.visit() a una ruta de la app bajo /static/,
// porque no coincide con el path real (p.ej. '/static/estudiante/calendario' no matchea
// '/estudiante/calendario'). Por eso solo se hace cy.visit() UNA VEZ, a /static/login; el
// resto de la navegación es por clic en la UI (navegación del lado del cliente, sin
// recarga, por lo que no pasa por esa limitación).
const URL_LOGIN = 'http://localhost:5173/static/login'

function loginYClicCalendario() {
  // El menú lateral usa 'hidden lg:flex' (Tailwind, breakpoint 1024px); con el
  // viewport por defecto de Cypress (1000x660) queda oculto y el link no es clickeable.
  cy.viewport(1280, 800)
  cy.clearLocalStorage()

  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type('jesusgabrieltd@ufps.edu.co')
  cy.get('[name="contrasena"]').type('Test1234')
  cy.contains('Iniciar sesión').click()
  cy.url().should('include', '/estudiante')

  cy.contains('a', 'Calendario').click()
  cy.url().should('include', '/estudiante/calendario')
}

// Escenario 1 — Vista unificada de calendario multi-curso
it('CA-01 - El calendario muestra fechas de 2 cursos con código de colores por urgencia', () => {
  loginYClicCalendario()

  cy.contains('h1', 'Calendario').should('be.visible')

  // Eventos de ambos cursos de demo visibles en la agenda del mes
  cy.contains('[DEMO HU-040] Entrega de prototipo').should('be.visible')
  cy.contains('[DEMO HU-040] Documentar API').should('be.visible')
  cy.contains('[DEMO HU-040] Modelo ER final').should('be.visible')

  // Código de colores por urgencia: vencido / próximo / normal presentes en la leyenda
  cy.contains('Vencido').should('be.visible')
  cy.contains('Próximo').should('be.visible')
  cy.contains('Normal').should('be.visible')

  cy.screenshot('hu040-ca01-calendario-multi-curso')
})

// Escenario 3 — Consulta de detalle de evento
it('CA-03 - El detalle de un evento muestra avance, equipo y enlace directo', () => {
  loginYClicCalendario()

  cy.contains('[DEMO HU-040] Documentar API').click()

  cy.contains('h3', '[DEMO HU-040] Documentar API').should('be.visible')
  cy.get('[role="progressbar"]').should('have.attr', 'aria-valuenow', '40')
  cy.contains('Equipo').should('be.visible')
  cy.contains('[DEMO HU-040] Equipo IS').should('be.visible')
  cy.contains('a', 'Ir a la actividad').should('have.attr', 'href').and('include', '/actividades/')

  cy.screenshot('hu040-ca03-detalle-evento')
})

// Escenario 2 — Recordatorio proactivo previo al vencimiento (campanita, sin buscarlo)
it('CA-02 - La notificación de recordatorio llega sin que el usuario la busque', () => {
  // El recordatorio (Alerta + correo real) se genera en segundo plano por
  // `python manage.py run_scheduler --once` (evidencia de correo: manual, bandeja UFPS).
  // Aquí se verifica que, con la alerta ya generada, aparece sola al entrar a cualquier
  // vista con la barra superior, sin que el usuario abra o busque nada.
  cy.viewport(1280, 800)
  cy.clearLocalStorage()
  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type('jesusgabrieltd@ufps.edu.co')
  cy.get('[name="contrasena"]').type('Test1234')
  cy.contains('Iniciar sesión').click()
  cy.url().should('include', '/estudiante')

  cy.get('button[title="Notificaciones"]').should('be.visible')
  cy.get('button[title="Notificaciones"] span').should('be.visible') // insignia de no leídas

  cy.screenshot('hu040-ca02-campanita-recordatorio')
})
