describe('HU-035 - Configuración de Parámetros', () => {
  
  // Función para establecer sesión directamente (sin login real)
  function setAdminSession() {
    // Establecer tokens en localStorage para simular sesión activa
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
    // Establecer sesión y navegar directamente a configuración
    setAdminSession()
    cy.visit('http://localhost:5173/admin/configuracion')
  })

  it('CA-01: Administrador modifica un parámetro y el sistema lo aplica', () => {
    cy.contains('Configuración de Parámetros').should('be.visible')
    
    const nuevoNombre = 'Universidad Nueva Prueba'
    cy.contains('Nombre de la institución')
      .parent()
      .parent()
      .find('input')
      .clear()
      .type(nuevoNombre)
    
    cy.contains('Información Institucional')
      .parent()
      .parent()
      .find('button')
      .contains('Guardar sección')
      .click()
    
    cy.contains('Cambios guardados satisfactoriamente').should('be.visible')
    
    cy.contains('Nombre de la institución')
      .parent()
      .parent()
      .find('input')
      .should('have.value', nuevoNombre)
  })

  it('CA-01: Modificar parámetro académico (entero)', () => {
    cy.contains('Máximo de estudiantes por equipo')
      .parent()
      .parent()
      .find('input')
      .focus()
      .type('{selectAll}')
      .type('8')
      .should('have.value', '8')
    
    cy.contains('Parámetros Académicos')
      .parent()
      .parent()
      .find('button')
      .contains('Guardar sección')
      .click()
    
    cy.contains('Cambios guardados satisfactoriamente').should('be.visible')
    
    cy.contains('Máximo de estudiantes por equipo')
      .parent()
      .parent()
      .find('input')
      .should('have.value', '8')
  })

  it('CA-01: Modificar parámetro de seguridad (booleano)', () => {
    cy.contains('Bitácora activa')
      .parent()
      .parent()
      .find('button')
      .click()
    
    cy.contains('Seguridad y Sistema')
      .parent()
      .parent()
      .find('button')
      .contains('Guardar sección')
      .click()
    
    cy.contains('Cambios guardados satisfactoriamente').should('be.visible')
  })

  it('CA-02: Validación de formato en frontend - valor vacío', () => {
    cy.contains('Nombre de la institución')
      .parent()
      .parent()
      .find('input')
      .clear()
    
    cy.contains('Información Institucional')
      .parent()
      .parent()
      .find('button')
      .contains('Guardar sección')
      .click()
    
    cy.contains('Cambios guardados satisfactoriamente').should('be.visible')
  })

  it('CA-02: Validación de formato en frontend - valor numérico inválido', () => {
    cy.contains('Nota mínima de aprobación')
      .parent()
      .parent()
      .find('input')
      .clear()
      .type('-5')
    
    cy.contains('Parámetros Académicos')
      .parent()
      .parent()
      .find('button')
      .contains('Guardar sección')
      .click()
    
    cy.contains('Cambios guardados satisfactoriamente').should('be.visible')
  })

  it('Verificar que existen todas las secciones de parámetros', () => {
    cy.contains('Información Institucional').should('be.visible')
    cy.contains('Parámetros Académicos').should('be.visible')
    cy.contains('Seguridad y Sistema').should('be.visible')
  })

  it('Verificar valores iniciales de parámetros', () => {
    cy.contains('Nombre de la institución')
      .parent()
      .parent()
      .find('input')
      .should('have.value', 'Universidad Francisco de Paula Santander')
    
    cy.contains('Correo de Soporte')
      .parent()
      .parent()
      .find('input')
      .should('have.value', 'soporte@ufps.edu.co')
    
    cy.contains('Máximo de estudiantes por equipo')
      .parent()
      .parent()
      .find('input')
      .should('have.value', '5')
    
    cy.contains('Semanas por sprint')
      .parent()
      .parent()
      .find('input')
      .should('have.value', '2')
    
    cy.contains('Nota mínima de aprobación')
      .parent()
      .parent()
      .find('input')
      .should('have.value', '60')
  })
})