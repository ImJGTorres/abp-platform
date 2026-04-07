# Contrato de API — ABP Platform
**Archivo:** `api-contract.md` en la raíz del repositorio
**Responsables:** Persona 1 + Persona 2 (Sub-equipo A) · Persona 4 + Persona 5 (Sub-equipo B)
**Regla:** Ningún endpoint cambia su estructura sin actualizar este documento y avisar al equipo.

---

## Convenciones generales

- Base URL: `http://localhost:8000/api`
- Todos los endpoints retornan y reciben `Content-Type: application/json`
- Rutas protegidas requieren header: `Authorization: Bearer <access_token>`
- Formato de fechas: `ISO 8601` — `"2026-04-06T10:30:00-05:00"`
- Errores siguen siempre la misma estructura:
```json
{
  "error": "Descripción del error",
  "campo": ["mensaje de validación"]
}
```

---

## HU-001 — Registrar usuarios

### `POST /api/usuarios/`
**Permiso:** Solo administrador
**Body:**
```json
{
  "nombre": "Angie Nikol",
  "apellido": "Ortiz Amaya",
  "correo": "angie.ortiz@ufps.edu.co",
  "contrasena": "contraseña_segura_123",
  "tipo_rol": "estudiante"
}
```
**tipo_rol valores válidos:** `administrador | docente | estudiante | director | lider_equipo`

**Respuesta exitosa `201`:**
```json
{
  "id": 1,
  "nombre": "Angie Nikol",
  "apellido": "Ortiz Amaya",
  "correo": "angie.ortiz@ufps.edu.co",
  "tipo_rol": "estudiante",
  "estado": "activo",
  "fecha_creacion": "2026-04-06T10:30:00-05:00"
}
```
**Errores:**
- `400` — correo ya existe: `{"correo": ["Ya existe un usuario con este correo."]}`
- `400` — campo faltante: `{"nombre": ["Este campo es requerido."]}`
- `403` — no es administrador

---

### `GET /api/usuarios/:id/`
**Permiso:** Propio usuario o administrador
**Respuesta `200`:** Mismo objeto que el POST exitoso

---

### `PATCH /api/usuarios/:id/`
**Permiso:** Propio usuario (campos limitados) o administrador (todos los campos)
**Body (solo los campos a modificar):**
```json
{
  "nombre": "Nuevo nombre",
  "apellido": "Nuevo apellido",
  "telefono": "3001234567"
}
```
**Respuesta `200`:** Objeto usuario actualizado
**Errores:**
- `403` — intentar editar perfil de otro usuario sin ser admin
- `400` — correo duplicado si admin intenta cambiar correo

---

## HU-002 — Autenticación

### `POST /api/auth/login/`
**Permiso:** Público
**Body:**
```json
{
  "correo": "angie.ortiz@ufps.edu.co",
  "contrasena": "contraseña_segura_123"
}
```
**Respuesta exitosa `200`:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id": 1,
    "nombre": "Angie Nikol",
    "apellido": "Ortiz Amaya",
    "correo": "angie.ortiz@ufps.edu.co",
    "tipo_rol": "estudiante"
  }
}
```
**Errores:**
- `401` — credenciales incorrectas: `{"error": "Correo o contraseña incorrectos."}`
- `403` — usuario inactivo: `{"error": "Tu cuenta está desactivada."}`

---

### `POST /api/auth/refresh/`
**Permiso:** Público (requiere refresh token válido)
**Body:**
```json
{ "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```
**Respuesta `200`:**
```json
{ "access": "nuevo_access_token..." }
```
**Error `401`:** refresh token inválido o expirado

---

### `POST /api/auth/logout/`
**Permiso:** Autenticado
**Body:**
```json
{ "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```
**Respuesta `200`:**
```json
{ "mensaje": "Sesión cerrada correctamente." }
```

---

## HU-003 — Gestión de roles y permisos

### `GET /api/roles/`
**Permiso:** Solo administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "nombre": "docente",
    "descripcion": "Profesores que gestionan cursos y proyectos",
    "estado": "activo",
    "cantidad_usuarios": 12,
    "permisos": ["usuarios.ver", "cursos.crear", "cursos.editar", "equipos.ver"]
  }
]
```

---

### `POST /api/roles/`
**Permiso:** Solo administrador
**Body:**
```json
{
  "nombre": "coordinador",
  "descripcion": "Coordinador académico con acceso a reportes",
  "permisos": ["reportes.ver", "cursos.ver"]
}
```
**Respuesta `201`:** Objeto rol creado
**Error `400`:** nombre duplicado

---

### `PUT /api/roles/:id/`
**Body:** Igual que POST
**Respuesta `200`:** Objeto rol actualizado

---

### `DELETE /api/roles/:id/`
**Respuesta `204`:** Sin body
**Error `409`:**
```json
{ "error": "No se puede eliminar este rol. Tiene 5 usuarios activos asignados." }
```

---

### `GET /api/permisos/`
**Permiso:** Solo administrador
**Respuesta `200`:**
```json
{
  "usuarios": ["usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"],
  "cursos": ["cursos.ver", "cursos.crear", "cursos.editar", "cursos.eliminar"],
  "equipos": ["equipos.ver", "equipos.crear", "equipos.editar"],
  "entregables": ["entregables.ver", "entregables.crear", "entregables.validar"],
  "evaluacion": ["evaluacion.ver", "evaluacion.crear", "evaluacion.editar"],
  "reportes": ["reportes.ver", "reportes.exportar"]
}
```

---

## HU-035 — Configuración del sistema

### `GET /api/configuracion/`
**Permiso:** Solo administrador
**Respuesta `200`:**
```json
{
  "institucional": {
    "nombre_institucion": "Universidad Francisco de Paula Santander",
    "nombre_programa": "Ingeniería de Sistemas",
    "correo_soporte": "soporte.abp@ufps.edu.co"
  },
  "equipos": {
    "max_estudiantes_por_equipo": 6
  },
  "archivos": {
    "formatos_archivo_permitidos": "pdf,docx,jpg,png,zip"
  },
  "sesiones": {
    "duracion_sesion_minutos": 60
  }
}
```

---

### `PATCH /api/configuracion/:clave/`
**Permiso:** Solo administrador
**Body:**
```json
{ "valor": "8" }
```
**Respuesta `200`:**
```json
{
  "clave": "max_estudiantes_por_equipo",
  "valor_anterior": "6",
  "valor_nuevo": "8",
  "actualizado_por": "admin@ufps.edu.co",
  "fecha_actualizacion": "2026-04-06T10:30:00-05:00"
}
```
**Error `400`:** valor inválido para el tipo de dato esperado

---

## HU-036 — Periodos académicos

### `GET /api/periodos/`
**Permiso:** Administrador y docentes
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "nombre": "2026-1",
    "fecha_inicio": "2026-01-20",
    "fecha_fin": "2026-06-15",
    "estado": "activo",
    "cantidad_cursos": 8
  }
]
```

---

### `POST /api/periodos/`
**Permiso:** Solo administrador
**Body:**
```json
{
  "nombre": "2026-2",
  "fecha_inicio": "2026-07-20",
  "fecha_fin": "2026-12-10"
}
```
**Respuesta `201`:** Objeto periodo creado
**Errores:**
- `400` — fecha_fin ≤ fecha_inicio
- `400` — nombre duplicado

---

### `PUT /api/periodos/:id/`
**Body:** Igual que POST más campo `"estado": "activo|inactivo|cerrado"`
**Respuesta `200`:** Objeto periodo actualizado

---

### `DELETE /api/periodos/:id/`
**Respuesta `204`:** Sin body
**Error `409`:**
```json
{ "error": "No se puede eliminar este periodo. Tiene 8 cursos asociados." }
```

---

## HU-037 — Bitácora

### `GET /api/bitacora/`
**Permiso:** Solo administrador
**Query params opcionales:**
- `usuario=5` — filtrar por ID de usuario
- `modulo=usuarios` — filtrar por módulo
- `accion=CREATE` — filtrar por tipo de acción
- `fecha_desde=2026-04-01` — filtrar por rango de fechas
- `fecha_hasta=2026-04-30`
- `page=2` — paginación (50 registros por página)

**Acciones válidas:** `CREATE | UPDATE | DELETE | LOGIN | LOGOUT | ACCESS_DENIED`
**Módulos válidos:** `usuarios | roles | bitacora | cursos | equipos | entregables | evaluacion | autenticacion`

**Respuesta `200`:**
```json
{
  "count": 248,
  "next": "http://localhost:8000/api/bitacora/?page=2",
  "previous": null,
  "results": [
    {
      "id": 248,
      "usuario": "admin@ufps.edu.co",
      "accion": "CREATE",
      "modulo": "usuarios",
      "descripcion": "Creó el usuario angie.ortiz@ufps.edu.co con rol estudiante",
      "ip_origen": "192.168.1.10",
      "fecha_hora": "2026-04-06T10:30:00-05:00"
    }
  ]
}
```
**No existen endpoints PUT, PATCH ni DELETE para este recurso.**
