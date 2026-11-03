// RUTA: frontend/cypress/e2e/hu043-correos.cy.js
// SCRUM-543 (HU-043) — Notificaciones automáticas por correo electrónico.
// Datos de prueba: backend/apps/alertas/management/commands/seed_hu043_demo.py
// (la suite lo corre sola en before() mediante cy.task('hu043Seed')).
// Cypress no puede leer una bandeja de correo: el correo se verifica en cola_correo y con el
// HTML que renderizaría el despachador (frontend/cypress/support/hu043_cola.py), sin enviar nada.
// La llegada real en staging (SendGrid) se evidencia aparte; aquí se prueba el encolado
// inmediato + la frecuencia del scheduler, que acotan el tiempo de entrega (RNF28: < 15 min).

const URL_LOGIN = 'http://localhost:5173/static/login'
const PASSWORD = 'Test1234'
const DOCENTE = 'demo.docente.hu043@example.com'
const ESTUDIANTE = 'demo.est1.hu043@example.com'
const LIMITE_RNF28_MIN = 15

let datos

function login(correo, contrasena) {
  // El menú lateral usa 'hidden lg:flex' (Tailwind, breakpoint 1024px).
  cy.viewport(1280, 800)
  cy.clearLocalStorage()
  cy.visit(URL_LOGIN)
  cy.get('[name="correo"]').type(correo)
  cy.get('[name="contrasena"]').type(contrasena)
  cy.contains('Iniciar sesión').click()
}

function tokenDe(correo) {
  return cy.request('POST', '/api/auth/login/', { correo, contrasena: PASSWORD })
    .its('body.access')
}

// El correo debe salir como máximo en (tiempo hasta encolar + intervalo del scheduler) < 15 min
function verificarTiempo(cola) {
  expect(cola.intervalo_scheduler_min).to.be.at.most(5)
  cola.correos.forEach(c => {
    expect(c.estado).to.eq('pendiente')
    const peorCasoMin = c.segundos_desde_encolado / 60 + cola.intervalo_scheduler_min
    expect(peorCasoMin, 'peor caso de entrega (min)').to.be.lessThan(LIMITE_RNF28_MIN)
  })
}

function verificarMembrete(html) {
  expect(html).to.include('Plataforma ABP')
  expect(html).to.include('#d32f2f')
  expect(html).to.include('Hola, Estudiante')
  expect(html).to.include('Este es un mensaje automático de la Plataforma ABP')
}

before(() => {
  cy.task('hu043Seed', null, { timeout: 120000 }).then(d => { datos = d })
})

// Escenario 1 — Anuncio publicado
it('CA-01 - Al publicar un anuncio, cada integrante recibe en cola un correo con membrete a tiempo', () => {
  const titulo = `Cambio de fecha ${Date.now()}`
  login(DOCENTE, PASSWORD)
  cy.url({ timeout: 15000 }).should('include', '/docente')
  cy.contains('a', 'Semáforos').click()
  cy.contains('button', 'Todos').click()
  cy.contains('[DEMO HU-043] Proyecto').closest('a').click()
  cy.url().should('include', `/docente/proyectos/${datos.proyecto_id}/monitoreo`)

  cy.contains('Publicar nuevo anuncio').scrollIntoView()
  cy.get('input[placeholder="Título del anuncio..."]').type(titulo)
  cy.get('textarea[placeholder="Mensaje del anuncio..."]').type('La entrega pasa al viernes.')
  cy.contains('button', 'Publicar anuncio').click()
  cy.contains('h3', titulo).should('be.visible')
  cy.screenshot('hu043-ca01-anuncio-publicado')

  cy.task('hu043Cola', `Nuevo anuncio: ${titulo}`, { timeout: 120000 }).then(cola => {
    expect(cola.correos).to.have.length(2)  // un correo por integrante activo, sin el autor
    verificarTiempo(cola)
    cola.correos.forEach(c => {
      expect(c.plantilla).to.eq('anuncio')
      expect(c.destino).to.match(/^demo\.est[12]\.hu043@example\.com$/)
      verificarMembrete(c.html)
      expect(c.html).to.include(titulo)
      expect(c.html).to.include('La entrega pasa al viernes.')
    })
  })
})

// Escenario 2 — Calificación publicada
it('CA-02 - Al publicar una calificación, cada integrante recibe en cola un correo con membrete y la nota', () => {
  tokenDe(DOCENTE).then(token => {
    cy.request({
      method: 'PATCH',
      url: `/api/evaluaciones/${datos.evaluacion_id}/publicar/`,
      headers: { Authorization: `Bearer ${token}` },
    }).its('status').should('eq', 200)
  })

  cy.task('hu043Cola', 'Calificación publicada: [DEMO HU-043] Informe final', { timeout: 120000 }).then(cola => {
    expect(cola.correos).to.have.length(2)
    verificarTiempo(cola)
    cola.correos.forEach(c => {
      expect(c.plantilla).to.eq('calificacion')
      verificarMembrete(c.html)
      expect(c.html).to.include('4.50')
      expect(c.html).to.include('Buen trabajo, sigan así.')
      expect(c.html).to.include(`/estudiante/proyectos/${datos.proyecto_id}/historial`)
    })
  })
})

// Escenario 3 — Campanita y correo no duplican el aviso
it('CA-03 - La campanita no repite el aviso que ya se envió por correo', () => {
  cy.task('hu043Cola', 'Calificación publicada: [DEMO HU-043] Informe final', { timeout: 120000 }).then(cola => {
    // Un solo correo por destinatario y evento
    const destinos = cola.correos.map(c => c.destino)
    expect(new Set(destinos).size).to.eq(destinos.length)
    // El evento no genera alerta ni notificación de campanita
    Object.values(cola.campanita).forEach(n => expect(n).to.eq(0))
  })

  login(ESTUDIANTE, PASSWORD)
  cy.url({ timeout: 15000 }).should('include', '/estudiante')
  cy.get('button[title="Notificaciones"]').click()
  cy.contains('Sin notificaciones').should('be.visible')
  cy.contains('Calificación publicada').should('not.exist')
  cy.contains('Cambio de fecha').should('not.exist')

  cy.screenshot('hu043-ca03-campanita-sin-duplicados')
})
