// frontend/cypress/e2e/hu036-periodos.cy.js
//
// HU-036 — Gestionar períodos académicos
// Subtarea: SCRUM-165 — Pruebas E2E con Cypress

const URL_PERIODOS = 'http://localhost:5173/admin/periodos'

describe('HU-036 - Gestión de Períodos Académicos', () => {
  
  function setAdminSession() {
    cy.window().then((win) => {
      win.localStorage.setItem('access_token', 'fake_access_token')
      win.localStorage.setItem('refresh_token', 'fake_refresh_token')
      win.localStorage.setItem('user', JSON.stringify({
        id: 1,
        nombre: 'Admin',
        correo: 'admin@test.com',
        tipo_rol: 'administrador'
      }))
    })
  }

  beforeEach(() => {
    setAdminSession()
    cy.visit(URL_PERIODOS)
  })

  // CA-01: Administrador crea un nuevo periodo académico
  it('CA-01: Crear nuevo periodo académico', () => {
    cy.contains('Periodos Académicos').should('be.visible')
    cy.contains('2026-1').should('be.visible')

    cy.contains('2026-1').parent().parent().within(() => {
      cy.contains('ACTIVO').should('be.visible')
    })

    cy.contains('button', 'Nuevo periodo').click()
    cy.contains('Nuevo Periodo').should('be.visible')

    cy.get('input[placeholder="Ej: 2026-1"]').type('2026-2')
    cy.get('input[type="date"]').first().type('2026-08-01')
    cy.get('input[type="date"]').eq(1).type('2026-12-15')

    cy.contains('button', 'Crear Periodo').click()
    cy.contains('Periodo creado correctamente').should('be.visible')
    cy.contains('2026-2').should('be.visible')
  })

  // CA-02: Administrador edita un periodo existente
  it('CA-02: Editar periodo existente', () => {
    cy.contains('2025-2').parent().parent().within(() => {
      cy.get('button').first().click()
    })

    cy.contains('Editar Periodo').should('be.visible')

    // Modificar el nombre (campo de texto)
    cy.get('input[placeholder="Ej: 2026-1"]').clear().type('2025-2 Editado')

    // Verificar que el botón Actualizar está habilitado
    cy.contains('button', 'Actualizar').should('not.be.disabled')
    cy.contains('button', 'Actualizar').click()

    cy.contains('Periodo actualizado correctamente').should('be.visible')
    cy.contains('2025-2 Editado').should('be.visible')
  })

  // CA-03: Administrador elimina un periodo
  it('CA-03: Eliminar periodo', () => {
    // Usar 2025-1 que tiene menos cursos (10 vs 12 de 2025-2)
    cy.contains('2025-1').parent().parent().within(() => {
      cy.get('button').last().click()
    })

    cy.contains('Eliminar Periodo').should('be.visible')
    cy.contains('button', 'Eliminar').click()

    // Verificar que aparece el mensaje de éxito
    cy.contains('Periodo eliminado correctamente').should('be.visible')
  })

  // CA-04: Validación de fechas en formulario
  it('CA-04: Validación - fecha fin menor a fecha inicio', () => {
    cy.contains('button', 'Nuevo periodo').click()
    cy.get('input[placeholder="Ej: 2026-1"]').type('2026-3')
    cy.get('input[type="date"]').first().type('2026-12-01')
    cy.get('input[type="date"]').eq(1).type('2026-06-01')

    cy.contains('La fecha de fin debe ser posterior a la de inicio').should('be.visible')
    cy.contains('button', 'Crear Periodo').should('be.disabled')
  })

  // Tests adicionales de verificación de UI
  it('Verificar estructura de la tabla de periodos', () => {
    cy.contains('Nombre').should('be.visible')
    cy.contains('Fecha Inicio').should('be.visible')
    cy.contains('Estado').should('be.visible')
    cy.get('table tbody tr').should('have.length.greaterThan', 0)
  })

  it('Verificar estados de periodos en la UI', () => {
    cy.contains('2026-1').parent().parent().within(() => {
      cy.contains('ACTIVO').should('be.visible')
    })
    cy.contains('2025-2').parent().parent().within(() => {
      cy.contains('INACTIVO').should('be.visible')
    })
  })

  it('Verificar cancelación en modal de creación', () => {
    cy.contains('button', 'Nuevo periodo').click()
    cy.get('input[placeholder="Ej: 2026-1"]').type('temp')
    cy.contains('button', 'Cancelar').click()
    cy.contains('Nuevo Periodo').should('not.exist')
    cy.contains('temp').should('not.exist')
  })

  it('Verificar cancelación en modal de eliminación', () => {
    cy.contains('2025-1').parent().parent().within(() => {
      cy.get('button').last().click()
    })
    cy.contains('Eliminar Periodo').should('be.visible')
    cy.contains('button', 'Cancelar').click()
    cy.contains('Eliminar Periodo').should('not.exist')
    cy.contains('2025-1').should('be.visible')
  })
})