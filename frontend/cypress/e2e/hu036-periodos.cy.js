// frontend/cypress/e2e/hu036-periodos.cy.js
//
// HU-036 — Gestionar períodos académicos
// Subtarea: SCRUM-165 — Pruebas E2E con Cypress
//
// No toca períodos reales: trabaja con '1990-1' y '1990-2' (fechas de 1990, para que nadie
// los confunda con el período actual), que crea, edita y borra. El período '1991-1' con un
// curso lo crea seed_cypress para comprobar que no se puede borrar un período con cursos.
// Los períodos de prueba se crean INACTIVOS: crear uno ACTIVO desactivaría el período real.

const URL_PERIODOS = '/admin/periodos'
const PERIODO_PRUEBA = '1990-1'
const PERIODO_EDITADO = '1990-2'
const PERIODO_CON_CURSOS = '1991-1'

function borrarPeriodosDePrueba() {
  cy.api('administrador', 'GET', '/api/configuracion/periodos/').then(({ body }) => {
    const lista = Array.isArray(body) ? body : body.results
    lista.filter(p => [PERIODO_PRUEBA, PERIODO_EDITADO].includes(p.nombre))
      .forEach(p => cy.api('administrador', 'DELETE', `/api/configuracion/periodos/${p.id}/`))
  })
}

function crearPeriodoApi(nombre) {
  return cy.api('administrador', 'POST', '/api/configuracion/periodos/', {
    nombre, fecha_inicio: '1990-01-15', fecha_fin: '1990-06-15', estado: 'inactivo',
  }).its('status').should('eq', 201)
}

const fila = nombre => cy.contains('tbody tr', nombre)

before(() => {
  cy.task('seedCypress', null, { timeout: 120000 })
})

beforeEach(() => {
  borrarPeriodosDePrueba()
})

after(() => {
  borrarPeriodosDePrueba()
})

function abrirPeriodos() {
  cy.login('administrador')
  cy.visit(URL_PERIODOS)
  cy.contains('h1', 'Periodos Académicos').should('be.visible')
  cy.contains('Cargando períodos...').should('not.exist')
}

describe('HU-036 - Gestión de Períodos Académicos', () => {

  // CA-01: Administrador crea un nuevo periodo académico.
  // Se llena el formulario como lo haría un usuario. Hoy falla por un error de la app:
  // 'Cursos Asociados' empieza en 0 con min="1" y el navegador bloquea el envío.
  it('CA-01: Crear nuevo periodo académico', () => {
    abrirPeriodos()

    cy.contains('button', 'Nuevo periodo').click()
    cy.contains('h2', 'Nuevo Periodo').should('be.visible')

    cy.get('input[placeholder="Formato: 2026-1"]').type(PERIODO_PRUEBA)
    cy.get('input[type="date"]').first().type('1990-01-15')
    cy.get('input[type="date"]').eq(1).type('1990-06-15')
    cy.get('form select').first().select('inactivo')

    cy.intercept('POST', '**/api/configuracion/periodos/').as('crearPeriodo')
    cy.contains('button', 'Crear Periodo').click()
    cy.wait('@crearPeriodo').its('response.statusCode').should('eq', 201)
    fila(PERIODO_PRUEBA).should('contain', 'INACTIVO')
  })

  // CA-02: Administrador edita un periodo existente
  it('CA-02: Editar periodo existente', () => {
    crearPeriodoApi(PERIODO_PRUEBA)
    abrirPeriodos()

    fila(PERIODO_PRUEBA).find('button').first().click()
    cy.contains('h2', 'Editar Periodo').should('be.visible')

    cy.get('input[placeholder="Formato: 2026-1"]').clear().type(PERIODO_EDITADO)
    cy.intercept('PATCH', '**/api/configuracion/periodos/*/').as('editarPeriodo')
    cy.contains('button', 'Actualizar').should('not.be.disabled').click()

    cy.wait('@editarPeriodo').its('response.statusCode').should('eq', 200)
    fila(PERIODO_EDITADO).should('be.visible')
  })

  // CA-03: Administrador elimina un periodo
  it('CA-03: Eliminar periodo sin cursos', () => {
    crearPeriodoApi(PERIODO_PRUEBA)
    abrirPeriodos()

    fila(PERIODO_PRUEBA).find('button').last().click()
    cy.contains('h3', 'Eliminar Periodo').should('be.visible')
    cy.intercept('DELETE', '**/api/configuracion/periodos/*/').as('deletePeriodo')
    cy.contains('.fixed button', 'Eliminar').click()

    cy.wait('@deletePeriodo').its('response.statusCode').should('eq', 204)
    cy.contains('tbody tr', PERIODO_PRUEBA).should('not.exist')
  })

  // CA-03b: No se puede eliminar un periodo con cursos (el backend responde 409)
  it('CA-03b: No se puede eliminar un periodo con cursos', () => {
    abrirPeriodos()
    cy.intercept('DELETE', '**/api/configuracion/periodos/*/').as('deletePeriodo')

    fila(PERIODO_CON_CURSOS).find('button').last().click()
    cy.contains('.fixed button', 'Eliminar').click()

    cy.wait('@deletePeriodo').its('response.statusCode').should('eq', 409)
    fila(PERIODO_CON_CURSOS).should('be.visible')
  })

  // CA-04: Validación de fechas en formulario
  it('CA-04: Validación - fecha fin menor a fecha inicio', () => {
    abrirPeriodos()

    cy.contains('button', 'Nuevo periodo').click()
    cy.get('input[placeholder="Formato: 2026-1"]').type(PERIODO_PRUEBA)
    cy.get('input[type="date"]').first().type('1990-12-01')
    cy.get('input[type="date"]').eq(1).type('1990-06-01')

    cy.contains('La fecha de fin debe ser posterior a la de inicio').should('be.visible')
    cy.contains('button', 'Crear Periodo').should('be.disabled')
  })

  // CA-04b: Validación del formato del nombre
  it('CA-04b: Validación - formato del nombre YYYY-N', () => {
    abrirPeriodos()

    cy.contains('button', 'Nuevo periodo').click()
    cy.get('input[placeholder="Formato: 2026-1"]').type('Periodo uno')
    cy.get('input[type="date"]').first().type('1990-01-15')
    cy.get('input[type="date"]').eq(1).type('1990-06-15')

    cy.contains('El formato debe ser YYYY-N').should('be.visible')
    cy.contains('button', 'Crear Periodo').should('be.disabled')
  })

  // Tests adicionales de verificación de UI
  it('Verificar estructura de la tabla de periodos', () => {
    abrirPeriodos()

    ;['Nombre', 'Fecha Inicio', 'Fecha Fin', 'Estado', 'Acciones'].forEach(col => {
      cy.contains('th', col).should('be.visible')
    })
    cy.get('table tbody tr').should('have.length.greaterThan', 0)
  })

  it('Verificar estados de periodos en la UI', () => {
    abrirPeriodos()

    // Hay un período activo (el real) y el de prueba está inactivo
    cy.contains('tbody tr span', /^ACTIVO$/).should('exist')
    fila(PERIODO_CON_CURSOS).should('contain', 'INACTIVO')
  })

  it('Verificar cancelación en modal de creación', () => {
    abrirPeriodos()

    cy.contains('button', 'Nuevo periodo').click()
    cy.get('input[placeholder="Formato: 2026-1"]').type(PERIODO_PRUEBA)
    cy.contains('button', 'Cancelar').click()

    cy.contains('h2', 'Nuevo Periodo').should('not.exist')
    cy.contains('tbody tr', PERIODO_PRUEBA).should('not.exist')
  })

  it('Verificar cancelación en modal de eliminación', () => {
    abrirPeriodos()

    fila(PERIODO_CON_CURSOS).find('button').last().click()
    cy.contains('h3', 'Eliminar Periodo').should('be.visible')
    cy.contains('.fixed button', 'Cancelar').click()

    cy.contains('h3', 'Eliminar Periodo').should('not.exist')
    fila(PERIODO_CON_CURSOS).should('be.visible')
  })
})
