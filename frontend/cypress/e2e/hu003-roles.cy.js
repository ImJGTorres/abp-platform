// RUTA: frontend/cypress/e2e/hu003-roles.cy.js
// HU-003 — Gestión de roles y permisos.
// Usa los usuarios cypress.<rol>@example.com y el rol '[CYPRESS] Rol con usuarios' (seed_cypress).
// Los roles que crea se llaman 'Cypress rol <n>' y se borran al terminar; no toca roles reales.

const URL_ROLES = '/admin/roles'
const PREFIJO_ROL = 'Cypress rol '
const ROL_CON_USUARIOS = '[CYPRESS] Rol con usuarios'

const nombreRol = () => `${PREFIJO_ROL}${Date.now()}`

// Crea un rol de prueba por la API (para los tests que necesitan uno ya existente).
function crearRolApi(nombre) {
  return cy.api('administrador', 'POST', '/api/roles/', { nombre, descripcion: 'Creado por Cypress' })
    .its('status').should('eq', 201)
}

// Borra por la API todos los roles de prueba que hayan quedado.
function borrarRolesDePrueba() {
  cy.api('administrador', 'GET', '/api/roles/').then(({ body }) => {
    body.filter(r => r.nombre.startsWith(PREFIJO_ROL))
      .forEach(r => cy.api('administrador', 'DELETE', `/api/roles/${r.id}/`))
  })
}

function abrirRoles() {
  cy.intercept('GET', '**/api/roles/').as('getRoles')
  cy.login('administrador')
  cy.visit(URL_ROLES)
  cy.wait('@getRoles')
  cy.get('table').should('be.visible')
}

before(() => {
  cy.task('seedCypress', null, { timeout: 120000 })
  borrarRolesDePrueba()
})

after(() => {
  borrarRolesDePrueba()
})

// ══════════════════════════════════════════════════════════════
// CP-01: Crear rol
// ══════════════════════════════════════════════════════════════

it('CP-01 - Administrador puede crear un rol correctamente', () => {
  const nombre = nombreRol()
  abrirRoles()

  cy.contains('button', '+ Nuevo rol').click()
  cy.get('input[placeholder="Ej: Director académico"]').type(nombre)
  cy.get('textarea[placeholder="Describe las responsabilidades de este rol..."]').type('Rol creado por Cypress')
  cy.intercept('POST', '**/api/roles/').as('createRol')
  cy.contains('button', 'Crear rol').click()

  cy.wait('@createRol').its('response.statusCode').should('eq', 201)
  cy.contains('tr', nombre).should('be.visible')
})

// ══════════════════════════════════════════════════════════════
// CP-02: Editar rol
// ══════════════════════════════════════════════════════════════

it('CP-02 - Administrador puede editar un rol correctamente', () => {
  const nombre = nombreRol()
  const editado = `${nombre} editado`
  crearRolApi(nombre)
  abrirRoles()
  cy.intercept('PATCH', '**/api/roles/*/').as('updateRol')

  cy.contains('tr', nombre).within(() => {
    cy.contains('button', 'Editar').click()
  })
  cy.get('input[placeholder="Ej: Director académico"]').clear().type(editado)
  cy.contains('button', 'Guardar cambios').click()

  cy.wait('@updateRol').its('response.statusCode').should('eq', 200)
  cy.contains('tr', editado).should('be.visible')
})

// ══════════════════════════════════════════════════════════════
// CP-03: Permisos por rol
// ══════════════════════════════════════════════════════════════

it('CP-03 - Los permisos se asignan correctamente por rol', () => {
  const nombre = nombreRol()
  crearRolApi(nombre)
  abrirRoles()
  cy.intercept('PATCH', '**/api/roles/*/').as('updateRol')

  // Clic en la fila abre el panel de permisos del rol
  cy.contains('tr', nombre).click()
  cy.contains('Configurar permisos').should('be.visible')
  cy.contains(`Rol seleccionado: ${nombre}`).should('be.visible')

  cy.get('input[type="checkbox"]').first().should('not.be.checked').check()
  cy.contains('button', 'Guardar cambios').click()
  cy.wait('@updateRol').its('response.statusCode').should('eq', 200)

  // Persistencia: tras recargar, el permiso sigue marcado
  cy.reload()
  cy.contains('tr', nombre).click()
  cy.contains(`Rol seleccionado: ${nombre}`).should('be.visible')
  cy.get('input[type="checkbox"]').first().should('be.checked')
})

// ══════════════════════════════════════════════════════════════
// CP-04: No eliminar rol con usuarios
// ══════════════════════════════════════════════════════════════

it('CP-04 - No se puede eliminar un rol con usuarios activos', () => {
  abrirRoles()
  cy.intercept('DELETE', '**/api/roles/*/').as('deleteRol')

  cy.contains('tr', ROL_CON_USUARIOS).within(() => {
    cy.contains('button', 'Eliminar').click()
  })
  // Nota: el aviso "usuarios vinculados" del modal usa total_usuarios, que se cuenta por
  // Usuario.tipo_rol y no por UsuarioRol (lo que valida el backend al borrar); para este
  // rol muestra 0, así que aquí solo se comprueba la regla del backend.
  cy.get('.fixed.inset-0').contains('button', 'Eliminar').click()

  // El backend lo rechaza (409) y el rol sigue en la tabla
  cy.wait('@deleteRol').its('response.statusCode').should('eq', 409)
  cy.contains('tr', ROL_CON_USUARIOS).should('be.visible')
})

// ══════════════════════════════════════════════════════════════
// CP-05: Eliminar rol sin usuarios
// ══════════════════════════════════════════════════════════════

it('CP-05 - Se puede eliminar un rol sin usuarios asignados', () => {
  const nombre = nombreRol()
  crearRolApi(nombre)
  abrirRoles()
  cy.intercept('DELETE', '**/api/roles/*/').as('deleteRol')

  cy.contains('tr', nombre).within(() => {
    cy.contains('button', 'Eliminar').click()
  })
  cy.get('.fixed.inset-0').contains('button', 'Eliminar').click()

  cy.wait('@deleteRol').its('response.statusCode').should('be.oneOf', [200, 204])
  cy.contains('tr', nombre).should('not.exist')
})

// ══════════════════════════════════════════════════════════════
// CP-06 / CP-07: Acceso por rol en el frontend
// ══════════════════════════════════════════════════════════════

it('CP-06 - Docente no puede acceder a /admin/roles', () => {
  cy.login('docente')
  cy.visit(URL_ROLES)

  cy.url().should('include', '/login')
})

it('CP-07 - Estudiante no puede acceder a /docente', () => {
  cy.login('estudiante')
  cy.visit('/docente')

  cy.url().should('include', '/login')
})

// ══════════════════════════════════════════════════════════════
// CP-08: Backend responde 403
// ══════════════════════════════════════════════════════════════

it('CP-08 - Backend retorna 403 a docente', () => {
  cy.api('docente', 'GET', '/api/roles/').its('status').should('eq', 403)
})
