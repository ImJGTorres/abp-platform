describe('HU-002 - Login', () => {
  it('muestra la pantalla de login', () => {
    cy.visit('http://localhost:5173/login')
    cy.url().should('include', '/login')
  })
})
