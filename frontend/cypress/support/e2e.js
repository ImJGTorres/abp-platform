// Comandos compartidos por las specs.
import { PASSWORD, correoDe } from './datos'

// Inicia sesión por la pantalla de login y guarda la sesión (cy.session) para no
// repetir el login en cada test de la misma spec.
Cypress.Commands.add('login', rol => {
  cy.session(['login', rol], () => {
    cy.visit('/login')
    cy.get('[name="correo"]').type(correoDe(rol))
    cy.get('[name="contrasena"]').type(PASSWORD, { log: false })
    cy.get('button[type="submit"]').click()
    cy.url().should('not.include', '/login')
  })
})

// Token de acceso de un usuario de prueba, para preparar o limpiar datos por la API.
// Se guarda por rol durante la spec: cada login contra la base remota tarda ~2 s.
const tokens = {}
Cypress.Commands.add('tokenDe', rol => {
  if (tokens[rol]) return cy.wrap(tokens[rol], { log: false })
  return cy.request('POST', '/api/auth/login/', { correo: correoDe(rol), contrasena: PASSWORD })
    .its('body.access')
    .then(token => { tokens[rol] = token })
})

// Petición a la API con el token del rol indicado. No falla por el código de estado,
// para que el test pueda comprobarlo.
Cypress.Commands.add('api', (rol, method, url, body) =>
  cy.tokenDe(rol).then(token =>
    cy.request({
      method, url, body,
      headers: { Authorization: `Bearer ${token}` },
      failOnStatusCode: false,
    })
  )
)
