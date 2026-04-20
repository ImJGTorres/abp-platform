const URL_LOGIN = "http://localhost:5173/login";
const URL_ROLES = "http://localhost:5173/admin/roles";
const URL_DOCENTE = "http://localhost:5173/docente";

function loginComo(correo, contrasena) {
  cy.clearLocalStorage();
  cy.visit(URL_LOGIN);

  cy.get('[name="correo"]').type(correo);
  cy.get('[name="contrasena"]').type(contrasena);
  cy.get('button[type="submit"]').click();

  // 🔥 asegurar login real
  cy.url().should('not.include', '/login');

  cy.window().then((win) => {
    const token = win.localStorage.getItem("access_token");
    expect(token).to.exist;
  });
}

function cargarRoles() {
  cy.intercept('GET', '**/roles/**').as('getRoles');

  cy.visit(URL_ROLES);

  // 🔥 evitar redirección silenciosa
  cy.url().should('include', '/admin/roles');

  // 🔥 esperar backend
  cy.wait('@getRoles');

  // 🔥 asegurar render
  cy.get('table').should('be.visible');
}


// ══════════════════════════════════════════════════════════════
// CP-01: Crear rol
// ══════════════════════════════════════════════════════════════

it("CP-01 - Administrador puede crear un rol correctamente", () => {
  loginComo("administrador@ufps.edu.co", "Test1234");
  cargarRoles();

  cy.contains("+ Nuevo rol").click();

  cy.get('input[placeholder="Ej: Director académico"]')
    .type("Rol Cypress Test");

  cy.get('textarea[placeholder="Describe las responsabilidades de este rol..."]')
    .type("Rol creado por Cypress");

  cy.contains("button", "Crear rol").click();

  cy.contains("Rol Cypress Test").should("be.visible");
});


// ══════════════════════════════════════════════════════════════
// CP-02: Editar rol
// ══════════════════════════════════════════════════════════════

it("CP-02 - Administrador puede editar un rol correctamente", () => {
  loginComo("administrador@ufps.edu.co", "Test1234");

  // 🔥 intercepts ANTES del visit
  cy.intercept('GET', '**/roles/**').as('getRoles');
  cy.intercept('PATCH', '**/roles/**').as('updateRol');

  cy.visit(URL_ROLES);

  // 🔥 evitar redirección
  cy.url().should('include', '/admin/roles');

  // 🔥 esperar carga real
  cy.wait('@getRoles');
  cy.get('table').should('be.visible');

  // 🔥 asegurar que el rol existe antes de interactuar
  cy.contains('td', 'Estudiante Editado', { timeout: 10000 })
    .should('be.visible')
    .closest('tr')
    .within(() => {
      cy.contains('button', 'Editar').click();
    });

  // 🔥 editar input
  cy.get('input[placeholder="Ej: Director académico"]')
    .should('be.visible')
    .clear()
    .type("Estudiante Editado");

  cy.contains("button", "Guardar cambios").click();

  // 🔥 validar backend
  cy.wait('@updateRol')
    .its('response.statusCode')
    .should('be.oneOf', [200, 204]);

  // 🔥 validar que se actualizó en UI
  cy.contains("Estudiante Editado", { timeout: 10000 })
    .should("be.visible");
});


// ══════════════════════════════════════════════════════════════
// CP-03: Permisos por rol
// ══════════════════════════════════════════════════════════════

it("CP-03 - Los permisos se asignan correctamente por rol", () => {
  loginComo("administrador@ufps.edu.co", "Test1234");

  cy.intercept('GET', '**/roles/**').as('getRoles');
  cy.intercept('PATCH', '**/roles/**').as('updateRol');

  cy.visit(URL_ROLES);
  cy.url().should('include', '/admin/roles');
  cy.wait('@getRoles');

  cy.get('table').should('be.visible');

  // abrir rol
  cy.contains("td", "director").closest("tr").click();

  cy.contains("Configurar permisos").should("be.visible");

  // marcar permiso
  cy.get('input[type="checkbox"]').first().check();

  // guardar
  cy.contains("button", "Guardar cambios").click();

  // 🔥 validar backend
  cy.wait('@updateRol')
    .its('response.statusCode')
    .should('be.oneOf', [200, 204]);

  // 🔥 validar persistencia real
  cy.reload();
  cy.wait('@getRoles');

  cy.contains("td", "director").closest("tr").click();
  cy.get('input[type="checkbox"]').first().should("be.checked");
});


// ══════════════════════════════════════════════════════════════
// CP-04: No eliminar rol con usuarios
// ══════════════════════════════════════════════════════════════

it("CP-04 - No se puede eliminar un rol con usuarios activos", () => {
  loginComo("administrador@ufps.edu.co", "Test1234");
  cargarRoles();

  cy.contains("td", "administrador")
    .closest("tr")
    .contains("button", "Eliminar")
    .click();

  cy.contains(/usuario.*vinculado/i).should("be.visible");

  cy.contains("button", "Cancelar").click();
});


// ══════════════════════════════════════════════════════════════
// CP-05: Eliminar rol sin usuarios
// ══════════════════════════════════════════════════════════════

it("CP-05 - Se puede eliminar un rol sin usuarios asignados", () => {
  loginComo("administrador@ufps.edu.co", "Test1234");

  cy.intercept('GET', '**/roles/**').as('getRoles');
  cy.intercept('POST', '**/roles/**').as('createRol');
  cy.intercept('DELETE', '**/roles/**').as('deleteRol');

  cy.visit(URL_ROLES);
  cy.url().should('include', '/admin/roles');
  cy.wait('@getRoles');

  cy.get('table').should('be.visible');

  // crear rol
  cy.contains("+ Nuevo rol").click();

  cy.get('input[placeholder="Ej: Director académico"]')
    .type("Rol Para Eliminar");

  cy.get('textarea[placeholder="Describe las responsabilidades de este rol..."]')
    .type("Solo para prueba");

  cy.contains("button", "Crear rol").click();

  // 🔥 validar creación backend
  cy.wait('@createRol')
    .its('response.statusCode')
    .should('be.oneOf', [200, 201]);

  cy.contains("Rol Para Eliminar").should("be.visible");

  // eliminar rol
  cy.contains("td", "Rol Para Eliminar")
    .closest("tr")
    .contains("button", "Eliminar")
    .click();

  cy.get(".fixed").contains("button", "Eliminar").click();

  // 🔥 validar eliminación backend
  cy.wait('@deleteRol')
    .its('response.statusCode')
    .should('be.oneOf', [200, 204]);

  // 🔥 validar UI
  cy.contains("Rol Para Eliminar").should("not.exist");
});


// ══════════════════════════════════════════════════════════════
// CP-06: Docente no accede a admin
// ══════════════════════════════════════════════════════════════

it("CP-06 - Docente no puede acceder a /admin/roles", () => {
  loginComo("docente@ufps.edu.co", "Test1234");

  cy.visit(URL_ROLES);

  cy.url().should("include", "/login");
});


// ══════════════════════════════════════════════════════════════
// CP-07: Estudiante no accede a docente
// ══════════════════════════════════════════════════════════════

it("CP-07 - Estudiante no puede acceder a /docente", () => {
  loginComo("estudiante@ufps.edu.co", "Test1234");

  cy.visit(URL_DOCENTE);

  cy.url().should("include", "/login");
});


// ══════════════════════════════════════════════════════════════
// CP-08: Backend responde 403
// ══════════════════════════════════════════════════════════════

it("CP-08 - Backend retorna 403 a docente", () => {
  loginComo("docente@ufps.edu.co", "Test1234");

  cy.window().then((win) => {
    const token = win.localStorage.getItem("access_token");

    cy.request({
      method: "GET",
      url: "http://127.0.0.1:8000/api/roles/",
      headers: { Authorization: `Bearer ${token}` },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.eq(403);
    });
  });
});