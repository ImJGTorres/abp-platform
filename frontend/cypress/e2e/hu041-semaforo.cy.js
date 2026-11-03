// RUTA: frontend/cypress/e2e/hu041-semaforo.cy.js
// SCRUM-550 (HU-041) — Semáforo de rendimiento personal del estudiante.
// Datos de prueba: backend/apps/reportes/management/commands/seed_hu041_demo.py
// (correr antes de esta suite: python manage.py seed_hu041_demo)
// jesusgabrieltd@ufps.edu.co ya queda en 'rojo' con los datos reales existentes (HU-040).

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

// Escenario 1 — Semáforo en Verde (desempeño óptimo)
it('CA-01 - Estudiante al día ve el semáforo en Verde con resumen óptimo', () => {
  login('estudiante.verde.hu041@ufps.edu.co', 'Test1234')
  cy.url().should('include', '/estudiante')

  cy.contains('h2', 'Semáforo de rendimiento').should('be.visible')
  cy.contains('Óptimo').should('be.visible')
  cy.contains('Vas muy bien: mantienes tu rendimiento en nivel óptimo.').should('be.visible')
  cy.contains('Nota promedio').should('be.visible')
  cy.contains('5.0').should('be.visible')

  // En verde no hay entregables críticos que mostrar
  cy.contains('h2', 'Entregables críticos').should('not.exist')

  cy.screenshot('hu041-ca01-semaforo-verde')
})

// Escenario 2 — Semáforo en Amarillo/Rojo con críticos y recomendaciones
it('CA-02 - Estudiante con atrasos ve Amarillo/Rojo con críticos y recomendaciones reales', () => {
  login('jesusgabrieltd@ufps.edu.co', 'Test1234')
  cy.url().should('include', '/estudiante')

  cy.contains('h2', 'Semáforo de rendimiento').should('be.visible')
  cy.contains('Riesgo crítico').should('be.visible')
  cy.contains('Tu rendimiento está en nivel crítico y necesitas actuar de inmediato.').should('be.visible')

  cy.contains('h2', 'Entregables críticos').scrollIntoView().should('be.visible')
  cy.contains('actividad 2').scrollIntoView().should('be.visible')

  cy.contains('Recomendaciones').scrollIntoView().should('be.visible')
  cy.contains('actividades vencidas; empieza por').scrollIntoView().should('be.visible')

  cy.screenshot('hu041-ca02-semaforo-rojo-criticos')
})

// Pasos Jira — el color coincide con el que ve el director para el mismo estudiante
it('CA-03 - El color del semáforo coincide con el que ve el director para el mismo estudiante', () => {
  login('director.hu041@ufps.edu.co', 'Test1234')
  cy.url().should('include', '/director')

  cy.contains('a', 'Riesgo').click()
  cy.url().should('include', '/director/riesgo')

  cy.contains('button', 'Todos').click()

  // La tabla de riesgo puede tardar más que el timeout por defecto (latencia de Supabase).
  cy.contains('tr', 'Jesus Gabriel Torres', { timeout: 15000 }).scrollIntoView().within(() => {
    cy.contains('Riesgo crítico').should('be.visible')
  })
  cy.contains('tr', 'Valeria Estudiante Verde', { timeout: 15000 }).scrollIntoView().within(() => {
    cy.contains('Óptimo').should('be.visible')
  })

  cy.screenshot('hu041-ca03-coincide-con-director')
})
