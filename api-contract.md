# Contrato de API — ABP Platform
**Archivo:** `api-contract.md` en la raíz del repositorio
**Regla:** Ningún endpoint cambia su estructura sin actualizar este documento y avisar al equipo.

---

## Convenciones generales

- **Base URL:** `http://localhost:8000/api`
- Todos los endpoints retornan y reciben `Content-Type: application/json`
- Rutas protegidas requieren header: `Authorization: Bearer <access_token>`
- Formato de fechas: `ISO 8601` — `"2026-04-06T10:30:00Z"`
- Errores siguen siempre la misma estructura:
```json
{
  "error": "Descripción del error",
  "campo": ["mensaje de validación"]
}
```

---

## Índice de endpoints

| Módulo | Prefijo |
|---|---|
| Autenticación | `/api/auth/` |
| Usuarios | `/api/usuarios/` |
| Roles y Permisos | `/api/roles/` · `/api/permisos/` |
| Bitácora | `/api/bitacora/` |
| Configuración | `/api/configuracion/` |
| Periodos académicos | `/api/configuracion/periodos/` |
| Cursos | `/api/cursos/` |
| Proyectos | `/api/proyectos/` |
| Objetivos | `/api/objetivos/` |
| RAPs | `/api/raps/` |
| Hitos | `/api/hitos/` |
| Fases | `/api/fases/` |
| Actividades | `/api/actividades/` |
| Equipos | `/api/proyectos/<id>/equipos/` · `/api/equipos/` · `/api/miembros/` |
| Entregables | `/api/actividades/<id>/entregables/` · `/api/entregables/` |
| Archivos adjuntos | `/api/archivos/` |
| Notificaciones | `/api/notificaciones/` |
| Evaluación / Rúbricas | `/api/rubricas/` · `/api/evaluaciones/` |
| Retroalimentación | `/api/proyectos/<id>/retroalimentaciones/` |
| Autoevaluación | `/api/proyectos/<id>/autoevaluaciones/` |
| Coevaluación | `/api/proyectos/<id>/coevaluaciones/` |
| Alertas | `/api/alertas/` |
| Reportes | `/api/reportes/` |
| Exportaciones | `/api/exportar/` |

---

## Autenticación

### `POST /api/auth/login/`
**Permiso:** Público
**Body:**
```json
{
  "correo": "usuario@ufps.edu.co",
  "contrasena": "contraseña123"
}
```
**Respuesta `200`:**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "usuario": {
    "id": 1,
    "nombre": "Gabriel",
    "apellido": "Torres",
    "correo": "gabriel.torres@ufps.edu.co",
    "tipo_rol": "docente",
    "foto_perfil": "/media/fotos/gabriel.jpg"
  }
}
```
**Errores:**
- `401` — `{"error": "Correo o contraseña incorrectos."}`
- `403` — `{"error": "Tu cuenta está desactivada."}`

---

### `POST /api/auth/refresh/`
**Permiso:** Público (requiere refresh token válido)
**Body:** `{ "refresh": "<token>" }`
**Respuesta `200`:** `{ "access": "<nuevo_token>" }`
**Error `401`:** refresh expirado o inválido

---

### `POST /api/auth/logout/`
**Permiso:** Autenticado
**Body:** `{ "refresh": "<token>" }`
**Respuesta `200`:** `{ "mensaje": "Sesión cerrada correctamente." }`

---

### `POST /api/auth/olvidar-contrasena/`
**Permiso:** Público
**Body:** `{ "correo": "usuario@ufps.edu.co" }`
**Respuesta `200`:** `{ "mensaje": "Si el correo existe, recibirás un enlace de recuperación." }`

---

### `POST /api/auth/recuperar-contrasena/`
**Permiso:** Público
**Body:**
```json
{
  "token": "<token_de_recuperacion>",
  "nueva_contrasena": "nueva123"
}
```
**Respuesta `200`:** `{ "mensaje": "Contraseña actualizada correctamente." }`
**Error `400`:** token inválido o expirado

---

### `POST /api/auth/cambiar-contrasena/`
**Permiso:** Autenticado
**Body:**
```json
{
  "contrasena_actual": "actual123",
  "nueva_contrasena": "nueva456"
}
```
**Respuesta `200`:** `{ "mensaje": "Contraseña cambiada correctamente." }`
**Error `400`:** contraseña actual incorrecta

---

## Usuarios

### `POST /api/usuarios/`
**Permiso:** Solo administrador
**Body:**
```json
{
  "nombre": "Angie Nikol",
  "apellido": "Ortiz Amaya",
  "correo": "angie.ortiz@ufps.edu.co",
  "contrasena": "contraseña123",
  "tipo_rol": "estudiante",
  "codigo_estudiante": "1150467"
}
```
**`tipo_rol` válidos:** `administrador | docente | estudiante | director | lider_equipo`

**Respuesta `201`:**
```json
{
  "id": 5,
  "nombre": "Angie Nikol",
  "apellido": "Ortiz Amaya",
  "correo": "angie.ortiz@ufps.edu.co",
  "tipo_rol": "estudiante",
  "estado": "activo",
  "codigo_estudiante": "1150467",
  "fecha_creacion": "2026-04-06T10:30:00Z"
}
```
**Errores:**
- `400` — correo duplicado: `{"correo": ["Ya existe un usuario con este correo."]}`
- `403` — no es administrador

---

### `GET /api/usuarios/perfil/`
**Permiso:** Autenticado (retorna el perfil del usuario en sesión)
**Respuesta `200`:** Objeto usuario completo con `foto_perfil`

---

### `PATCH /api/usuarios/<pk>/`
**Permiso:** Propio usuario o administrador
**Body (parcial):**
```json
{
  "nombre": "Nuevo nombre",
  "apellido": "Nuevo apellido"
}
```
**Respuesta `200`:** Objeto usuario actualizado
**Error `403`:** intentar editar otro usuario sin ser administrador

---

### `POST /api/usuarios/foto-perfil/`
**Permiso:** Autenticado
**Body:** `multipart/form-data` con campo `foto` (imagen)
**Respuesta `200`:** `{ "foto_perfil": "/media/fotos/<nombre>.jpg" }`

---

### `POST /api/usuarios/carga-masiva/`
**Permiso:** Solo administrador
**Body:** `multipart/form-data` con campo `archivo` (Excel `.xlsx`)
**Formato esperado del Excel:**

| nombre | apellido | correo | codigo_estudiante |
|---|---|---|---|
| Carlos | García | carlos@ufps.edu.co | 1150001 |

**Respuesta `201`:**
```json
{
  "creados": 28,
  "omitidos": 2,
  "errores": [
    { "fila": 5, "motivo": "Correo ya registrado." }
  ]
}
```

---

## Roles y Permisos

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
    "fecha_creacion": "2026-04-01T00:00:00Z",
    "permisos": [{ "id": 3, "codigo": "cursos.crear", "modulo": "cursos" }]
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
  "descripcion": "Coordinador con acceso a reportes",
  "permisos": [1, 2, 5]
}
```
**Respuesta `201`:** Objeto rol creado
**Error `400`:** nombre duplicado

---

### `GET /api/roles/<pk>/`
**Respuesta `200`:** Objeto rol con permisos

### `PUT /api/roles/<pk>/` · `PATCH /api/roles/<pk>/`
**Body:** Igual que POST
**Respuesta `200`:** Objeto rol actualizado

### `DELETE /api/roles/<pk>/`
**Respuesta `204`:** Sin body
**Error `409`:** `{ "error": "No se puede eliminar. Tiene N usuarios activos asignados." }`

---

### `GET /api/permisos/`
**Permiso:** Solo administrador
**Respuesta `200`:**
```json
{
  "usuarios": ["usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"],
  "cursos":   ["cursos.ver", "cursos.crear", "cursos.editar", "cursos.eliminar"],
  "equipos":  ["equipos.ver", "equipos.crear", "equipos.editar"],
  "entregables": ["entregables.ver", "entregables.crear", "entregables.validar"],
  "evaluacion": ["evaluacion.ver", "evaluacion.crear", "evaluacion.editar"],
  "reportes": ["reportes.ver", "reportes.exportar"]
}
```

### `GET /api/roles/permisos/` · `POST /api/roles/permisos/`
**Permiso:** Solo administrador
**CRUD completo:** también `GET/PUT/PATCH/DELETE /api/roles/permisos/<pk>/`

### `GET /api/roles/rol-permiso/` · `POST /api/roles/rol-permiso/`
**CRUD completo:** también `GET/PUT/PATCH/DELETE /api/roles/rol-permiso/<pk>/`

---

## Bitácora

### `GET /api/bitacora/`
**Permiso:** Solo administrador
**Query params:**
- `usuario=<id>` · `modulo=usuarios` · `accion=CREATE`
- `fecha_desde=2026-04-01` · `fecha_hasta=2026-04-30`
- `page=2` (50 registros por página)

**Acciones válidas:** `CREATE | UPDATE | DELETE | LOGIN | LOGOUT | ACCESS_DENIED`

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
      "fecha_hora": "2026-04-06T10:30:00Z"
    }
  ]
}
```
**No existen endpoints POST, PUT, PATCH ni DELETE para este recurso.**

---

## Configuración del sistema

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
    "max_estudiantes_por_equipo": "6"
  },
  "archivos": {
    "formatos_archivo_permitidos": "pdf,docx,jpg,png,zip"
  },
  "sesiones": {
    "duracion_sesion_minutos": "60"
  }
}
```

---

### `PATCH /api/configuracion/<clave>/`
**Permiso:** Solo administrador
**Body:** `{ "valor": "8" }`
**Respuesta `200`:**
```json
{
  "clave": "max_estudiantes_por_equipo",
  "valor_anterior": "6",
  "valor_nuevo": "8",
  "actualizado_por": "admin@ufps.edu.co",
  "fecha_actualizacion": "2026-04-06T10:30:00Z"
}
```
**Error `400`:** valor inválido para el tipo de dato del parámetro

---

## Periodos académicos

### `GET /api/configuracion/periodos/`
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
    "fecha_creacion": "2026-01-01T00:00:00Z"
  }
]
```

### `POST /api/configuracion/periodos/`
**Permiso:** Solo administrador
**Body:**
```json
{
  "nombre": "2026-2",
  "fecha_inicio": "2026-07-20",
  "fecha_fin": "2026-12-10",
  "estado": "activo"
}
```
**Respuesta `201`:** Objeto periodo creado
**Errores:**
- `400` — `fecha_fin ≤ fecha_inicio`
- `400` — nombre duplicado

### `GET /api/configuracion/periodos/<pk>/`
### `PUT /api/configuracion/periodos/<pk>/` · `PATCH /api/configuracion/periodos/<pk>/`
**Body:** Igual que POST (campos opcionales en PATCH)

### `DELETE /api/configuracion/periodos/<pk>/`
**Respuesta `204`:** Sin body
**Error `409`:** `{ "error": "No se puede eliminar. Tiene N cursos asociados." }`

---

## Cursos

### `GET /api/cursos/`
**Permiso:** Administrador, docentes y estudiantes
**Query params:** `periodo_id` · `docente_id` · `estado` · `page`
**Respuesta `200`:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "nombre": "Análisis y Diseño de Sistemas",
      "codigo": "AYD-01",
      "descripcion": "Curso de arquitectura de software",
      "id_periodo_academico": 1,
      "id_docente": 5,
      "docente_nombre": "Juan Pérez",
      "cantidad_max_estudiantes": 30,
      "estado": "activo",
      "fecha_creacion": "2026-04-06T10:30:00Z"
    }
  ]
}
```

### `POST /api/cursos/`
**Permiso:** Administrador o docente
**Body:**
```json
{
  "nombre": "Análisis y Diseño de Sistemas",
  "codigo": "AYD-01",
  "descripcion": "Curso de arquitectura de software",
  "id_periodo_academico": 1,
  "id_docente": 5,
  "cantidad_max_estudiantes": 30
}
```
**Respuesta `201`:** Objeto curso creado
**Error `400`:** código duplicado en mismo periodo

---

### `GET /api/cursos/<pk>/` · `PUT /api/cursos/<pk>/` · `PATCH /api/cursos/<pk>/` · `DELETE /api/cursos/<pk>/`
**Permiso:** Docente del curso o administrador
**Error `409` en DELETE:** tiene estudiantes o proyectos asociados

---

### `GET /api/cursos/docentes/`
**Permiso:** Administrador
**Respuesta `200`:** Lista de usuarios con rol docente `[{ "id", "nombre", "apellido", "correo" }]`

---

### `POST /api/cursos/carga-masiva/`
**Permiso:** Administrador
**Body:** `multipart/form-data` con archivo Excel de cursos
**Respuesta `201`:** Resumen de creados / omitidos / errores

---

### `GET /api/cursos/<curso_id>/estudiantes/`
**Permiso:** Docente del curso o administrador
**Respuesta `200`:** Lista de estudiantes inscritos

### `POST /api/cursos/<curso_id>/estudiantes/`
**Permiso:** Docente del curso o administrador
**Body:** `{ "estudiante_id": 10 }`
**Respuesta `201`:** Objeto inscripción creado

### `POST /api/cursos/<curso_id>/estudiantes/importar/`
**Permiso:** Docente del curso o administrador
**Body:** `multipart/form-data` con Excel (columnas: `correo` o `codigo_estudiante`)
**Respuesta `201`:** `{ "inscritos": 25, "omitidos": 2, "errores": [] }`

---

### `GET /api/cursos/<curso_id>/proyectos/`
**Permiso:** Docente, estudiantes inscritos o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "nombre": "Sistema de Gestión de Biblioteca",
    "descripcion": "...",
    "id_curso": 1,
    "fecha_inicio": "2026-04-15",
    "fecha_fin_estimada": "2026-06-15",
    "estado": "planificado",
    "fecha_creacion": "2026-04-06T10:30:00Z"
  }
]
```

### `POST /api/cursos/<curso_id>/proyectos/`
**Permiso:** Docente del curso o administrador
**Body:**
```json
{
  "nombre": "Sistema de Gestión de Biblioteca",
  "descripcion": "Proyecto ABP de gestión de biblioteca",
  "fecha_inicio": "2026-04-15",
  "fecha_fin_estimada": "2026-06-15"
}
```
**Respuesta `201`:** Objeto proyecto con `estado: "planificado"`
**Error `400`:** `fecha_fin_estimada ≤ fecha_inicio`

---

## Proyectos

### `GET /api/proyectos/<pk>/`
**Permiso:** Docente del curso, estudiantes inscritos o administrador
**Respuesta `200`:** Objeto proyecto completo

### `PUT /api/proyectos/<pk>/` · `PATCH /api/proyectos/<pk>/`
**Permiso:** Docente del proyecto o administrador
**Body:** Campos del proyecto (todos opcionales en PATCH)
**`estado` válidos:** `planificado | en_ejecucion | finalizado`
**Respuesta `200`:** Objeto proyecto actualizado

---

### `GET /api/proyectos/<pk>/progreso/`
**Permiso:** Autenticado con acceso al proyecto
**Respuesta `200`:**
```json
{
  "id_proyecto": 1,
  "nombre_proyecto": "Sistema de Gestión de Biblioteca",
  "estado_proyecto": "en_ejecucion",
  "total_fases": 4,
  "fases_completadas": 1,
  "fases_en_progreso": 1,
  "porcentaje_progreso": 35,
  "total_actividades": 20,
  "actividades_completadas": 7
}
```

---

### `GET /api/proyectos/<proyecto_id>/dashboard/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:** Dashboard ejecutivo con métricas de fases, actividades y equipos

---

### `GET /api/proyectos/<proyecto_id>/equipos-resumen/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:** Lista de equipos con su resumen de progreso y miembros

---

### `GET /api/proyectos/<proyecto_id>/entregables-pendientes/`
**Permiso:** Docente del proyecto
**Respuesta `200`:** Lista de entregables en estado `enviado` pendientes de revisión

---

## Objetivos del proyecto

### `GET /api/proyectos/<proyecto_id>/objetivos/`
**Permiso:** Docente, estudiantes del curso o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_proyecto": 1,
    "descripcion": "Desarrollar un sistema de gestión completo",
    "tipo": "general",
    "orden": 1,
    "fecha_creacion": "2026-04-06T10:30:00Z"
  }
]
```

### `POST /api/proyectos/<proyecto_id>/objetivos/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "descripcion": "Implementar módulo de autenticación",
  "tipo": "especifico",
  "orden": 1
}
```
**`tipo` válidos:** `general | especifico`
**Respuesta `201`:** Objeto objetivo creado

---

### `GET /api/objetivos/<pk>/`
### `PUT /api/objetivos/<pk>/` · `PATCH /api/objetivos/<pk>/`
**Body:** `{ "descripcion": "...", "tipo": "especifico", "orden": 2 }`
**Respuesta `200`:** Objetivo actualizado (el orden se reajusta automáticamente)

### `DELETE /api/objetivos/<pk>/`
**Respuesta `204`:** Sin body. Los órdenes restantes se reajustan automáticamente.

---

## RAPs (Resultados de Aprendizaje)

### `GET /api/proyectos/<id_proyecto>/raps/`
**Permiso:** Docente, estudiantes o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "proyecto": 1,
    "nombre": "RAP 1",
    "descripcion": "Análisis de requisitos de software",
    "competencia_asociada": "Análisis de sistemas",
    "porcentaje_evaluacion": 25
  }
]
```

### `POST /api/proyectos/<id_proyecto>/raps/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "nombre": "RAP 1",
  "descripcion": "Análisis de requisitos de software",
  "competencia_asociada": "Análisis de sistemas",
  "porcentaje_evaluacion": 25
}
```
**Respuesta `201`:** Objeto RAP creado

---

### `GET /api/raps/<id>/`
### `PUT /api/raps/<id>/` · `PATCH /api/raps/<id>/`
**Body:** Campos del RAP (todos opcionales en PATCH)
**Respuesta `200`:** Objeto RAP actualizado

### `DELETE /api/raps/<id>/`
**Respuesta `204`:** Sin body

---

## Hitos del proyecto

### `GET /api/proyectos/<proyecto_id>/hitos/`
**Permiso:** Docente, estudiantes o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_proyecto": 1,
    "nombre": "Entrega de análisis",
    "descripcion": "Primera entrega del análisis de requisitos",
    "fecha_inicio": "2026-04-20",
    "fecha_fin": "2026-05-01",
    "tipo": "entrega",
    "estado": "pendiente",
    "fecha_creacion": "2026-04-06T10:30:00Z"
  }
]
```

### `POST /api/proyectos/<proyecto_id>/hitos/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "nombre": "Entrega de análisis",
  "descripcion": "Primera entrega",
  "fecha_inicio": "2026-04-20",
  "fecha_fin": "2026-05-01",
  "tipo": "entrega"
}
```
**`tipo` válidos:** `hito | entrega | revision`
**`estado` válidos:** `pendiente | en_progreso | completado | cancelado`
**Respuesta `201`:** Objeto hito creado

---

### `GET /api/hitos/<pk>/`
### `PUT /api/hitos/<pk>/` · `PATCH /api/hitos/<pk>/`
### `DELETE /api/hitos/<pk>/`

---

## Fases del proyecto

### `GET /api/proyectos/<proyecto_id>/fases/`
**Permiso:** Docente, estudiantes o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_proyecto": 1,
    "nombre": "Análisis",
    "descripcion": "Fase de levantamiento de requisitos",
    "orden": 1,
    "fecha_inicio": "2026-04-15",
    "fecha_fin": "2026-04-30",
    "estado": "en_progreso",
    "porcentaje_completado": 60
  }
]
```

### `POST /api/proyectos/<proyecto_id>/fases/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "nombre": "Análisis",
  "descripcion": "Fase de levantamiento de requisitos",
  "orden": 1,
  "fecha_inicio": "2026-04-15",
  "fecha_fin": "2026-04-30"
}
```
**Respuesta `201`:** Objeto fase creado
**`estado` válidos:** `pendiente | en_progreso | completada`

---

### `GET /api/fases/<pk>/`
### `PUT /api/fases/<pk>/` · `PATCH /api/fases/<pk>/`
**Body:** Campos de la fase
**Respuesta `200`:** Objeto fase actualizado

### `DELETE /api/fases/<pk>/`
**Respuesta `204`:** Sin body
**Error `409`:** `{ "error": "No se puede eliminar la fase. Tiene N actividades asociadas." }`

---

## Actividades

### `GET /api/fases/<fase_id>/actividades/`
**Permiso:** Docente, estudiantes del proyecto o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_fase": 1,
    "nombre": "Entrevistas con stakeholders",
    "descripcion": "...",
    "fecha_limite": "2026-04-22",
    "prioridad": "alta",
    "estado": "en_progreso",
    "id_responsable": 10,
    "id_equipo_asignado": 2,
    "responsables": [10, 12],
    "fecha_creacion": "2026-04-15T08:00:00Z"
  }
]
```

### `POST /api/fases/<fase_id>/actividades/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "nombre": "Entrevistas con stakeholders",
  "descripcion": "Levantar requisitos funcionales",
  "fecha_limite": "2026-04-22",
  "prioridad": "alta",
  "id_equipo_asignado": 2
}
```
**`prioridad` válidos:** `alta | media | baja`
**`estado` válidos:** `pendiente | en_progreso | completada | bloqueada`
**Respuesta `201`:** Objeto actividad creado

---

### `GET /api/actividades/<pk>/`
### `PUT /api/actividades/<pk>/` · `PATCH /api/actividades/<pk>/`
**Respuesta `200`:** Objeto actividad actualizado

### `DELETE /api/actividades/<pk>/`
**Respuesta `204`:** Sin body
**Error `409`:** si tiene dependencias

---

### `PATCH /api/actividades/<pk>/asignar-responsable/`
**Permiso:** Líder de equipo o docente
**Body:** `{ "responsable_id": 10 }`
**Respuesta `200`:** Objeto actividad actualizado

---

### `PATCH /api/actividades/<pk>/asignar/`
**Permiso:** Líder de equipo o docente
**Body:** `{ "responsables": [10, 12, 15] }`
**Respuesta `200`:** Objeto actividad con lista de responsables actualizada

---

### `GET /api/actividades/<actividad_id>/avances/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_actividad": 1,
    "id_usuario": 10,
    "descripcion": "Se completaron las entrevistas con 5 stakeholders",
    "porcentaje_completado": 50,
    "tipo": "texto",
    "url_referencia": null,
    "fecha_registro": "2026-04-20T14:00:00Z"
  }
]
```

### `POST /api/actividades/<actividad_id>/avances/`
**Permiso:** Miembros del equipo
**Body:**
```json
{
  "descripcion": "Se completaron las entrevistas con 5 stakeholders",
  "porcentaje_completado": 50,
  "tipo": "texto",
  "url_referencia": null
}
```
**`tipo` válidos:** `texto | enlace`
**Respuesta `201`:** Objeto avance creado

---

## Equipos

### `GET /api/proyectos/<proyecto_id>/equipos/`
**Permiso:** Docente, estudiantes del proyecto o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "proyecto": 1,
    "nombre": "Equipo Alpha",
    "descripcion": "Equipo de desarrollo backend",
    "cupo_maximo": 6,
    "estado": "activo",
    "cantidad_miembros_activos": 4,
    "fecha_creacion": "2026-04-06T10:30:00Z"
  }
]
```

### `POST /api/proyectos/<proyecto_id>/equipos/`
**Permiso:** Docente del proyecto o administrador
**Body:**
```json
{
  "nombre": "Equipo Alpha",
  "descripcion": "Equipo de desarrollo backend",
  "cupo_maximo": 6
}
```
**Respuesta `201`:** Objeto equipo creado
**Error `400`:** `cupo_maximo` supera `max_estudiantes_por_equipo` del sistema

---

### `PUT /api/equipos/<equipo_id>/` · `PATCH /api/equipos/<equipo_id>/`
**Permiso:** Docente del proyecto o administrador
**Body:** `{ "nombre": "...", "descripcion": "...", "cupo_maximo": 5 }`
**Respuesta `200`:** Objeto equipo actualizado

---

### `DELETE /api/equipos/<equipo_id>/disolver/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:** `{ "mensaje": "Equipo disuelto. N miembros retirados." }`

---

### `GET /api/equipos/<equipo_id>/estudiantes/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:**
```json
{
  "miembros_activos": [
    {
      "id": 10,
      "nombre": "Carlos García",
      "correo": "carlos@ufps.edu.co",
      "rol_interno": "lider",
      "estado": "activo"
    }
  ],
  "disponibles": [
    { "id": 11, "nombre": "Laura Martínez", "correo": "laura@ufps.edu.co" }
  ]
}
```

---

### `POST /api/equipos/<equipo_id>/asignar/`
**Permiso:** Docente del proyecto o administrador
**Body:** `{ "estudiantes": [10, 11, 12] }`
**Respuesta `200`:** `{ "asignados": 3, "omitidos": 0 }`
**Errores:**
- `400` — estudiante ya en otro equipo del mismo proyecto
- `409` — equipo lleno

---

### `DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `204`:** Sin body (soft-delete, registro queda como `retirado`)

---

### `PATCH /api/equipos/<equipo_id>/miembros/<usuario_id>/rol/`
**Permiso:** Docente del proyecto o administrador
**Body:** `{ "rol_interno": "lider" }`
**`rol_interno` válidos:** `lider | desarrollador | disenador | tester | analista`
**Respuesta `200`:** Miembro actualizado

---

### `PATCH /api/miembros/<miembro_id>/`
**Permiso:** Docente del proyecto o administrador
**Body:** `{ "rol_interno": "tester", "descripcion_responsabilidades": "..." }`
**Respuesta `200`:** Miembro actualizado

---

### `POST /api/equipos/<equipo_id>/miembros/mover/`
**Permiso:** Docente del proyecto o administrador
**Body:** `{ "usuario_id": 10, "equipo_destino_id": 2 }`
**Respuesta `200`:**
```json
{
  "mensaje": "Usuario movido del equipo 1 al equipo 2.",
  "usuario_id": 10,
  "equipo_origen_id": 1,
  "equipo_destino_id": 2
}
```
**Error `409`:** equipo destino lleno

---

### `GET /api/equipos/<equipo_id>/actividades/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:** Lista de actividades asignadas al equipo

---

### `GET /api/equipos/<equipo_id>/progreso/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:**
```json
{
  "equipo_id": 1,
  "nombre": "Equipo Alpha",
  "total_actividades": 10,
  "completadas": 4,
  "en_progreso": 3,
  "pendientes": 3,
  "porcentaje_progreso": 40
}
```

---

### `GET /api/mis-equipos/`
**Permiso:** Estudiante autenticado
**Respuesta `200`:** Lista de equipos del estudiante con sus actividades asignadas

---

## Entregables

### `GET /api/actividades/<id_actividad>/entregables/`
**Permiso:** Miembros del equipo asignado, docente o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_actividad": 5,
    "id_equipo": 2,
    "titulo": "Documento de Análisis v1",
    "descripcion": "Documento de requisitos funcionales",
    "tipo": "documento",
    "estado": "enviado",
    "numero_version": 1,
    "fecha_envio": "2026-04-22T09:00:00Z",
    "fecha_creacion": "2026-04-21T18:00:00Z"
  }
]
```

### `POST /api/actividades/<id_actividad>/entregables/`
**Permiso:** Miembros del equipo asignado
**Body:**
```json
{
  "id_equipo": 2,
  "titulo": "Documento de Análisis v1",
  "descripcion": "Documento de requisitos funcionales",
  "tipo": "documento"
}
```
**`tipo` válidos:** `documento | prototipo | codigo | presentacion | otro`
**Respuesta `201`:** Objeto entregable en estado `borrador`

---

### `POST /api/entregables/<pk>/enviar/`
**Permiso:** Miembros del equipo
**Body:** `{}` (vacío)
**Respuesta `200`:** `{ "estado": "enviado", "fecha_envio": "2026-04-22T09:00:00Z" }`
**Error `400`:** entregable sin archivos adjuntos

---

### `POST /api/entregables/<pk>/nueva-version/`
**Permiso:** Miembros del equipo
**Body:** `{ "motivo_revision": "Correcciones solicitadas por el docente" }`
**Respuesta `201`:** Nuevo entregable en estado `borrador` con `numero_version` incrementado

---

### `GET /api/entregables/<pk>/versiones/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:** Lista de versiones del entregable con fecha y usuario

---

### `POST /api/entregables/<entregable_id>/aprobar/`
**Permiso:** Docente del proyecto
**Body:** `{ "retroalimentacion": "Excelente trabajo, bien estructurado." }`
**Respuesta `200`:** `{ "estado": "aprobado", "fecha_validacion": "..." }`

---

### `POST /api/entregables/<entregable_id>/rechazar/`
**Permiso:** Docente del proyecto
**Body:** `{ "retroalimentacion": "Falta la sección de casos de uso." }`
**Respuesta `200`:** `{ "estado": "rechazado", "retroalimentacion": "..." }`

---

### `POST /api/entregables/<pk>/validar/`
**Permiso:** Docente del proyecto
**Body:** `{ "estado": "aprobado", "retroalimentacion": "..." }`
**Respuesta `200`:** Objeto entregable actualizado

---

## Archivos adjuntos

### `GET /api/entregables/<id_entregable>/archivos/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "nombre_original": "analisis_requisitos.pdf",
    "tipo_mime": "application/pdf",
    "tamaño_bytes": 204800,
    "version": 1,
    "fecha_subida": "2026-04-21T18:30:00Z"
  }
]
```

### `POST /api/entregables/<id_entregable>/archivos/`
**Permiso:** Miembros del equipo
**Body:** `multipart/form-data` con campo `archivo` (tamaño máximo 10 MB)
**Formatos:** según parámetro `formatos_archivo_permitidos`
**Respuesta `201`:** Objeto archivo creado

---

### `DELETE /api/archivos/<archivo_id>/`
**Permiso:** Usuario que subió el archivo, docente o administrador
**Respuesta `204`:** Sin body

---

## Notificaciones

### `GET /api/notificaciones/`
**Permiso:** Autenticado (retorna solo las del usuario en sesión)
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "tipo": "aprobado",
    "titulo_entregable": "Documento de Análisis v1",
    "retroalimentacion": "Excelente trabajo.",
    "id_entregable": 1,
    "leida": false,
    "fecha_creacion": "2026-04-22T10:00:00Z"
  }
]
```

### `PATCH /api/notificaciones/<pk>/leer/`
**Permiso:** Usuario dueño de la notificación
**Body:** `{}` (vacío)
**Respuesta `200`:** `{ "leida": true }`

### `PATCH /api/notificaciones/leer-todas/`
**Permiso:** Autenticado
**Respuesta `200`:** `{ "actualizadas": 5 }`

---

## Rúbricas

### `GET /api/rubricas/`
**Permiso:** Docente o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "nombre": "Rúbrica de Entregable Final",
    "descripcion": "Evaluación de la documentación del proyecto",
    "tipo": "entregable",
    "peso_total": 100,
    "id_proyecto": 1,
    "criterios": [
      {
        "id": 1,
        "nombre": "Claridad y estructura",
        "peso_porcentual": 30,
        "id_rap": 1,
        "niveles": [
          { "nivel": 1, "etiqueta": "insuficiente", "descripcion": "...", "puntos": 0 },
          { "nivel": 2, "etiqueta": "basico",        "descripcion": "...", "puntos": 1.5 },
          { "nivel": 3, "etiqueta": "satisfactorio", "descripcion": "...", "puntos": 2.5 },
          { "nivel": 4, "etiqueta": "excelente",     "descripcion": "...", "puntos": 3 }
        ]
      }
    ],
    "fecha_creacion": "2026-04-10T08:00:00Z"
  }
]
```

### `POST /api/rubricas/`
**Permiso:** Docente o administrador
**Body:**
```json
{
  "nombre": "Rúbrica de Entregable Final",
  "descripcion": "Evaluación de la documentación",
  "tipo": "entregable",
  "id_proyecto": 1,
  "criterios": [
    {
      "nombre": "Claridad y estructura",
      "peso_porcentual": 30,
      "id_rap": 1,
      "niveles": [
        { "nivel": 1, "etiqueta": "insuficiente", "descripcion": "...", "puntos": 0 },
        { "nivel": 4, "etiqueta": "excelente",    "descripcion": "...", "puntos": 3 }
      ]
    }
  ]
}
```
**`tipo` válidos:** `entregable | proceso | presentacion`
**Respuesta `201`:** Objeto rúbrica con criterios y niveles

---

### `GET /api/rubricas/<pk>/`
### `PUT /api/rubricas/<pk>/` · `PATCH /api/rubricas/<pk>/`
### `DELETE /api/rubricas/<pk>/`

---

### `GET /api/proyectos/<proyecto_id>/rubricas/`
**Permiso:** Docente, estudiantes o administrador
**Respuesta `200`:** Lista de rúbricas del proyecto

### `POST /api/proyectos/<proyecto_id>/rubricas/`
**Equivalente a POST /api/rubricas/ con `id_proyecto` fijado por la URL**

---

## Evaluaciones de entregables

### `GET /api/entregables/<id_entregable>/evaluaciones/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_entregable": 1,
    "id_rubrica": 1,
    "id_docente": 5,
    "puntuacion_total": 85.5,
    "comentario_general": "Buen trabajo en general.",
    "estado": "publicada",
    "fecha_evaluacion": "2026-04-25T10:00:00Z",
    "calificaciones": [
      {
        "id_criterio": 1,
        "id_nivel_seleccionado": 3,
        "puntos_obtenidos": 25.5,
        "comentario_criterio": "Buena estructura pero falta detalle."
      }
    ]
  }
]
```

### `POST /api/entregables/<id_entregable>/evaluaciones/`
**Permiso:** Docente del proyecto
**Body:**
```json
{
  "id_rubrica": 1,
  "comentario_general": "Buen trabajo en general.",
  "calificaciones": [
    {
      "id_criterio": 1,
      "id_nivel_seleccionado": 3,
      "comentario_criterio": "Buena estructura pero falta detalle."
    }
  ]
}
```
**Respuesta `201`:** Evaluación en estado `borrador`

---

### `PATCH /api/evaluaciones/<pk>/publicar/`
**Permiso:** Docente creador de la evaluación
**Body:** `{}` (vacío)
**Respuesta `200`:** `{ "estado": "publicada" }`

---

## Retroalimentación

### `POST /api/proyectos/<id_proyecto>/retroalimentaciones/`
**Permiso:** Docente del proyecto
**Body:**
```json
{
  "tipo": "grupal",
  "contenido": "El equipo ha demostrado buen manejo del tiempo.",
  "id_equipo": 2
}
```
**`tipo` válidos:** `grupal | individual | actividad`
- `grupal` → requiere `id_equipo`
- `individual` → requiere `id_estudiante`
- `actividad` → requiere `id_actividad`

**Respuesta `201`:** Objeto retroalimentación creado

---

### `GET /api/equipos/<id_equipo>/retroalimentaciones/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:** Lista de retroalimentaciones del equipo

### `GET /api/usuarios/<id_usuario>/retroalimentaciones/`
**Permiso:** Propio usuario, docente o administrador
**Respuesta `200`:** Lista de retroalimentaciones individuales del usuario

---

## Autoevaluación

### `GET /api/proyectos/<proyecto_id>/autoevaluaciones/mia/`
**Permiso:** Estudiante autenticado (retorna su autoevaluación del proyecto)
**Respuesta `200`:** Objeto autoevaluación o `404` si no existe aún

---

### `GET /api/proyectos/<id_proyecto>/autoevaluaciones/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "id_proyecto": 1,
    "id_estudiante": 10,
    "id_rubrica": 2,
    "puntuacion_total": 78.0,
    "reflexion_texto": "Considero que mejoré en el análisis de requisitos.",
    "estado": "enviada",
    "periodo_evaluacion": "2026-1",
    "fecha_registro": "2026-05-10T14:00:00Z",
    "detalles": [
      {
        "id_criterio": 1,
        "id_nivel_seleccionado": 3,
        "puntos_obtenidos": 25.0,
        "comentario": "Me siento satisfecho con este criterio."
      }
    ]
  }
]
```

### `POST /api/proyectos/<id_proyecto>/autoevaluaciones/`
**Permiso:** Estudiante inscrito en el proyecto
**Body:**
```json
{
  "id_rubrica": 2,
  "periodo_evaluacion": "2026-1",
  "reflexion_texto": "Considero que mejoré en el análisis.",
  "detalles": [
    {
      "id_criterio": 1,
      "id_nivel_seleccionado": 3,
      "comentario": "Me siento satisfecho."
    }
  ]
}
```
**Respuesta `201`:** Autoevaluación en estado `borrador`
**Error `400`:** ya existe una autoevaluación para ese periodo

---

## Coevaluación

### `GET /api/proyectos/<proyecto_id>/coevaluaciones/promedio/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:**
```json
[
  {
    "id_evaluado": 10,
    "nombre_evaluado": "Carlos García",
    "promedio_puntuacion": 82.5,
    "cantidad_evaluaciones": 3
  }
]
```

### `GET /api/proyectos/<id_proyecto>/coevaluaciones/`
**Permiso:** Docente del proyecto o administrador
**Respuesta `200`:** Lista de coevaluaciones del proyecto

### `POST /api/proyectos/<id_proyecto>/coevaluaciones/`
**Permiso:** Estudiante inscrito en el proyecto
**Body:**
```json
{
  "id_evaluado": 11,
  "id_rubrica": 2,
  "periodo_evaluacion": "2026-1",
  "comentario": "Buen compañero, aportó activamente.",
  "detalles": [
    {
      "id_criterio": 1,
      "id_nivel_seleccionado": 4,
      "comentario": "Siempre entregó a tiempo."
    }
  ]
}
```
**Respuesta `201`:** Coevaluación en estado `borrador`
**Errores:**
- `400` — no puede evaluarse a sí mismo
- `400` — ya evaluó a ese compañero en el mismo periodo

---

## Alertas

### `GET /api/alertas/`
**Permiso:** Autenticado (retorna solo las alertas del usuario en sesión)
**Query params:** `estado=no_leida | leida | descartada`
**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "tipo": "actividad_vencida",
    "mensaje": "La actividad 'Entrevistas con stakeholders' está vencida.",
    "estado": "no_leida",
    "id_proyecto": 1,
    "referencia_id": 5,
    "fecha_generacion": "2026-04-23T08:00:00Z",
    "fecha_lectura": null
  }
]
```
**`tipo` válidos:** `actividad_vencida | entregable_pendiente | entregable_enviado | evaluacion_pendiente | bajo_rendimiento`

### `PATCH /api/alertas/<alerta_id>/leer/`
**Permiso:** Dueño de la alerta
**Body:** `{}` (vacío)
**Respuesta `200`:** `{ "estado": "leida", "fecha_lectura": "2026-04-23T09:00:00Z" }`

---

## Reportes

### `GET /api/reportes/indicadores/`
**Permiso:** Director o administrador
**Respuesta `200`:**
```json
{
  "total_proyectos": 12,
  "proyectos_activos": 8,
  "total_equipos": 24,
  "total_entregables": 96,
  "entregables_aprobados": 70,
  "tasa_aprobacion": 72.9,
  "promedio_progreso_proyectos": 58.3
}
```

### `GET /api/reportes/indicadores/tendencia/`
**Permiso:** Director o administrador
**Respuesta `200`:** Serie temporal de indicadores por periodo

---

### `GET /api/reportes/proyecto/<proyecto_id>/`
**Permiso:** Docente del proyecto, director o administrador
**Respuesta `200`:** Reporte completo del proyecto (fases, actividades, equipos, entregables, evaluaciones)

### `GET /api/reportes/curso/<curso_id>/`
**Permiso:** Docente del curso, director o administrador
**Respuesta `200`:** Reporte consolidado del curso con todos sus proyectos

### `GET /api/reportes/estudiante/<estudiante_id>/proyecto/<proyecto_id>/`
**Permiso:** Propio estudiante, docente del proyecto, director o administrador
**Respuesta `200`:** Reporte de desempeño individual del estudiante en el proyecto

### `GET /api/reportes/equipo/<equipo_id>/estudiantes/`
**Permiso:** Miembros del equipo, docente o administrador
**Respuesta `200`:** Reporte comparativo de desempeño de los miembros del equipo

---

### `GET /api/reportes/bajo-rendimiento/`
**Permiso:** Docente o administrador
**Query params:** `curso_id` · `proyecto_id` · `umbral=60`
**Respuesta `200`:**
```json
[
  {
    "estudiante_id": 10,
    "nombre": "Carlos García",
    "correo": "carlos@ufps.edu.co",
    "proyecto_id": 1,
    "promedio_progreso": 35.0,
    "actividades_vencidas": 3,
    "entregables_rechazados": 1
  }
]
```

### `GET /api/reportes/estudiantes/<estudiante_id>/rendimiento/`
**Permiso:** Propio estudiante, docente o administrador
**Respuesta `200`:** Perfil completo de rendimiento del estudiante (actividades, entregables, evaluaciones, avances)

---

## Exportaciones

### `POST /api/exportar/reporte/`
**Permiso:** Director, docente o administrador
**Body:**
```json
{
  "tipo_reporte": "proyecto",
  "formato": "excel",
  "parametros": {
    "proyecto_id": 1
  }
}
```
**`tipo_reporte` válidos:** `proyecto | estudiante | equipo | indicadores | tendencia`
**`formato` válidos:** `pdf | excel`
**Respuesta `202`:**
```json
{
  "exportacion_id": 7,
  "estado": "generando",
  "mensaje": "La exportación se está procesando."
}
```

---

### `GET /api/exportar/<exportacion_id>/estado/`
**Permiso:** Usuario que solicitó la exportación
**Respuesta `200`:**
```json
{
  "id": 7,
  "estado": "listo",
  "tipo_reporte": "proyecto",
  "formato": "excel",
  "fecha_disponible": "2026-05-20T10:01:00Z"
}
```
**`estado` válidos:** `generando | listo | error`

---

### `GET /api/exportar/<exportacion_id>/descargar/`
**Permiso:** Usuario que solicitó la exportación
**Respuesta `200`:** Archivo binario con header `Content-Disposition: attachment; filename="reporte_proyecto_1.xlsx"`
**Error `404`:** exportación no lista o no existe
