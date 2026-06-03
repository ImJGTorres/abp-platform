# Plataforma ABP — Gestión Integral del Aprendizaje Basado en Proyectos
**Universidad Francisco de Paula Santander · Ingeniería de Sistemas · 2026**

Sistema web para centralizar y estructurar los procesos del modelo de **Aprendizaje Basado en Proyectos (ABP)** en los cursos de Ingeniería de Sistemas. Cubre el ciclo completo: configuración institucional, gestión de cursos y proyectos, trabajo colaborativo por equipos, entrega y revisión de entregables, evaluaciones con rúbricas, autoevaluación, coevaluación y generación de reportes.

---

## Tabla de contenido

1. [Tecnologías](#tecnologías)
2. [Arquitectura general](#arquitectura-general)
3. [Módulos del backend](#módulos-del-backend)
4. [Funcionalidades por rol](#funcionalidades-por-rol)
5. [Estructura del repositorio](#estructura-del-repositorio)
6. [Cómo levantar el proyecto localmente](#cómo-levantar-el-proyecto-localmente)
7. [Variables de entorno](#variables-de-entorno)
8. [Convención de ramas y commits](#convención-de-ramas-y-commits)
9. [Equipo](#equipo)

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Django 4.2 + Django REST Framework 3.15 |
| Autenticación | JWT (SimpleJWT) con rotación de tokens y blacklist |
| Base de datos (local) | SQLite 3 |
| Base de datos (producción) | PostgreSQL 15 via Supabase |
| Email | SMTP / SendGrid (django-anymail) |
| Exportaciones | openpyxl (Excel) + ReportLab (PDF) |
| Servidor producción | Gunicorn |
| Testing | pytest + pytest-django + factory-boy |

---

## Arquitectura general

```
Cliente (React SPA)
        │  HTTP/JSON (JWT Bearer)
        ▼
  Django REST Framework
        │
  ┌─────┴──────────────────────────────────────────────┐
  │ apps.usuarios │ apps.roles │ apps.bitacora          │
  │ apps.configuracion │ apps.cursos │ apps.equipos      │
  │ apps.entregables │ apps.evaluacion │ apps.alertas    │
  │ apps.reportes │ apps.exportaciones                   │
  └─────────────────────────────────────────────────────┘
        │
   SQLite (dev) / PostgreSQL Supabase (prod)
```

Toda la comunicación entre frontend y backend ocurre por la API REST definida en `api-contract.md`. El acceso a los endpoints está protegido por JWT; los permisos adicionales se validan por rol (administrador, docente, director, líder de equipo, estudiante).

---

## Módulos del backend

### `apps.usuarios`
Modelo de usuario personalizado (`AbstractBaseUser`). Gestión de perfiles, cambio de contraseña, recuperación por correo (token de un solo uso), carga masiva de estudiantes desde Excel y foto de perfil.

### `apps.roles`
Modelo `Rol` y `Permiso` con relación many-to-many. Seed automático de roles base vía `python manage.py seed_roles_permisos`. Gestión CRUD de roles desde el panel de administrador.

### `apps.bitacora`
Registro automático de auditoría de acciones del sistema (`BitacoraSistema`) mediante signals de Django. Los administradores pueden consultar y filtrar el historial completo.

### `apps.configuracion`
- **`ParametroSistema`**: tabla clave-valor tipada (string, integer, boolean, date) con caché en memoria (15 min) para evitar consultas repetidas. Categorías: institucional, seguridad, archivos, sesiones, general.
- **`PeriodoAcademico`**: gestión de periodos con estados activo / inactivo / cerrado.

### `apps.cursos`
Núcleo de la plataforma. Modelos:
- `Curso` — estados borrador / activo / cerrado, cupo máximo, docente asignado, periodo académico.
- `CursoEstudiante` — inscripción de estudiantes a cursos.
- `Proyecto` — estados planificado / en_ejecución / finalizado, fechas de inicio y fin.
- `ObjetivoProyecto` — objetivos generales y específicos ordenados por posición.
- `ResultadoAprendizaje (RAP)` — resultados vinculados a proyectos con competencia y porcentaje de evaluación.
- `FaseProyecto` — fases ordenadas con porcentaje de completitud calculado.
- `Actividad` — tareas con prioridad, estado, responsables, dependencias entre actividades (grafo DAG).
- `AvanceActividad` — registro de avances con porcentaje y referencias URL.
- `HitoProyecto` — hitos / entregas / revisiones con fechas y estado.
- `ActividadDependencia` — relación de precedencia (grafo dirigido acíclico) entre actividades.
- Vistas SQL de progreso: `VistaProgresoFase` y `VistaProgresoProyecto` (read-only, `managed=False`).

### `apps.equipos`
- `Equipo` — equipos de trabajo por proyecto con cupo máximo validado contra `ParametroSistema`.
- `MiembroEquipo` — membresía con soft-delete (estado activo / retirado) y rol interno (líder, desarrollador, diseñador, tester, analista). Valida que un estudiante no pertenezca a dos equipos del mismo proyecto.

### `apps.entregables`
- `Entregable` — documento / prototipo / código / presentación vinculado a actividad y equipo. Estados: borrador → enviado → aprobado / rechazado. Soporte de versiones.
- `ArchivoAdjunto` — archivos físicos subidos por los estudiantes (límite 10 MB, subdirectorio `entregables/archivos/`).
- `EntregableVersion` — historial completo de revisiones con motivo.
- `Notificacion` — notificación interna al aprobar o rechazar un entregable.

### `apps.evaluacion`
- `Rubrica` — tipos: entregable / proceso / presentación. Peso total 100%.
- `CriterioRubrica` — criterios con peso porcentual y RAP asociado opcional.
- `NivelDesempeno` — 4 niveles (insuficiente → excelente) con puntos por criterio.
- `Evaluacion` — evaluación de entregable por docente con estado borrador / publicada.
- `CalificacionCriterio` — nivel seleccionado y puntos por criterio por evaluación.
- `Retroalimentacion` — comentarios del docente al equipo, individuo o actividad.
- `Autoevaluacion` + `DetalleAutoevaluacion` — autoevaluación del estudiante una vez por periodo.
- `Coevaluacion` + `DetalleCoevaluacion` — evaluación entre pares, una por evaluador-evaluado-periodo.

### `apps.alertas`
- `Alerta` — alertas automáticas por actividad vencida, entregable pendiente / enviado, evaluación pendiente, bajo rendimiento. Estados: no_leida / leida / descartada.

### `apps.reportes`
Reportes consolidados para el rol de director: indicadores por proyecto, comparativos de equipos, tendencia histórica.

### `apps.exportaciones`
- `Exportacion` — registro de solicitudes de exportación con estado generando / listo / error.
- Soporta formatos **Excel** (openpyxl) y **PDF** (ReportLab) para tipos: proyecto, estudiante, equipo, indicadores, tendencia.

---

## Funcionalidades por rol

### 🔑 Administrador
- Gestión completa de usuarios (registro individual y carga masiva por Excel)
- Gestión de roles y permisos
- Gestión de periodos académicos
- Gestión de cursos (crear, activar, cerrar)
- Configuración de parámetros del sistema
- Visualización de bitácora de auditoría
- Acceso al panel de director (reportes e indicadores)

### 👩‍🏫 Docente
- Gestión de sus cursos y proyectos asignados
- Definición de objetivos y resultados de aprendizaje (RAPs) del proyecto
- Creación de fases, actividades y cronograma (hitos)
- Gestión de equipos: crear, reorganizar y asignar estudiantes
- Definición de perfiles y roles de proyecto
- Constructor de rúbricas con criterios y niveles de desempeño
- Panel de revisión y validación de entregables
- Evaluación de entregables con rúbrica
- Retroalimentación individual y grupal
- Monitoreo de progreso del proyecto (tablero Kanban, vista por fases)
- Historial de evaluaciones del proyecto
- Identificación de estudiantes en riesgo con perfil de rendimiento

### 📊 Director
- Dashboard de indicadores generales de todos los proyectos
- Listado y generación de reportes por proyecto (exportación Excel / PDF)
- Vista consolidada de tendencias históricas

### 👥 Estudiante
- Dashboard personal con cursos y proyectos activos
- Vista de actividades del proyecto y avance por fases
- Registro de avances con porcentaje de completitud
- Entrega de entregables con archivos adjuntos y gestión de versiones
- Tablero Kanban compartido del proyecto
- Dashboard de progreso personal
- Autoevaluación con rúbrica por periodo
- Coevaluación entre pares
- Historial de evaluaciones recibidas
- Notificaciones de aprobación / rechazo de entregables

### 🧑‍💼 Líder de Equipo
Todas las funcionalidades del estudiante más:
- Dashboard del líder con métricas del equipo
- Distribución de trabajo y carga entre miembros
- Asignación de responsables a actividades

---

## Estructura del repositorio

```
abp-platform/
├── backend/
│   ├── apps/
│   │   ├── actividades/         # (legacy, absorbido por cursos)
│   │   ├── alertas/             # Alertas automáticas por eventos
│   │   ├── bitacora/            # Auditoría de acciones del sistema
│   │   ├── configuracion/       # Parámetros del sistema y periodos académicos
│   │   ├── cursos/              # Cursos, proyectos, fases, actividades, RAPs, hitos
│   │   ├── entregables/         # Entregables, archivos adjuntos, versiones, notificaciones
│   │   ├── equipos/             # Equipos y miembros con soft-delete
│   │   ├── evaluacion/          # Rúbricas, evaluaciones, auto/coevaluación, retroalimentación
│   │   ├── exportaciones/       # Exportaciones Excel y PDF
│   │   ├── reportes/            # Reportes para director
│   │   ├── roles/               # Roles y permisos
│   │   └── usuarios/            # Modelo de usuario, auth, recuperación de contraseña
│   ├── config/
│   │   ├── settings.py          # Configuración principal (SQLite/Supabase, JWT, caché, email)
│   │   ├── urls.py              # URLs raíz
│   │   └── wsgi.py
│   ├── media/                   # Archivos subidos (ignorado en git)
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminLayout.jsx
│   │   │   ├── Compartidos/     # TableroKanban, ExportarReporte
│   │   │   ├── director/        # DashboardDirector, ListaReportes, ReporteProyecto
│   │   │   ├── docente/         # GestionCursos, ProyectoLayout, ConstructorRubricas, etc.
│   │   │   ├── Estudiante/      # DashboardEstudiante, Autoevaluacion, Coevaluacion, etc.
│   │   │   └── LiderEquipo/     # DashboardLider, DistribucionTrabajo, AsignarResponsables
│   │   ├── hooks/               # useRegistroForm, useFormValidation, useRAPsGestion
│   │   ├── router/              # AppRouter con rutas por rol + PrivateRoute
│   │   ├── services/            # api.js, docenteApi.js, estudianteApi.js, liderEquipoApi.js, entregablesApi.js
│   │   └── utils/               # errorHandler.js
│   ├── package.json
│   └── vite.config.js
├── api-contract.md              # Contrato de endpoints (fuente de verdad)
├── .gitignore
└── README.md
```

---

## Cómo levantar el proyecto localmente

### Requisitos previos
- Python 3.11+
- Node.js 20+
- Git

> Para desarrollo local se usa **SQLite** (no necesita PostgreSQL instalado). Para producción se conecta a Supabase vía variables de entorno.

### Backend

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env           # Editar .env con los valores correspondientes

# Aplicar migraciones
python manage.py migrate

# Cargar datos iniciales (roles, permisos y parámetros del sistema)
python manage.py seed_roles_permisos

# Crear superusuario administrador (opcional)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

El backend queda disponible en **http://localhost:8000**

### Frontend

```bash
cd frontend

npm install

cp .env.example .env           # Verificar VITE_API_URL=http://localhost:8000

npm run dev
```

El frontend queda disponible en **http://localhost:5173**

### Ejecutar pruebas (backend)

```bash
cd backend
pytest
```

---

## Variables de entorno

### Backend (`.env`)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-...` |
| `DEBUG` | Modo debug | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `localhost,127.0.0.1` |
| `USE_SUPABASE` | Activa la conexión a PostgreSQL/Supabase | `False` |
| `DB_NAME` | Nombre de la BD (Supabase) | `postgres` |
| `DB_USER` | Usuario de la BD | `postgres` |
| `DB_PASSWORD` | Contraseña de la BD | `...` |
| `DB_HOST` | Host de la BD | `db.xxx.supabase.co` |
| `DB_PORT` | Puerto de la BD | `5432` |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS permitidos | `http://localhost:5173` |
| `EMAIL_BACKEND` | Backend de correo | `django.core.mail.backends.console.EmailBackend` |
| `EMAIL_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | Puerto SMTP | `587` |
| `EMAIL_HOST_USER` | Usuario SMTP | `tu@correo.com` |
| `EMAIL_HOST_PASSWORD` | Contraseña SMTP | `...` |
| `DEFAULT_FROM_EMAIL` | Remitente por defecto | `ABP Platform <noreply@ufps.edu.co>` |
| `SENDGRID_API_KEY` | API Key de SendGrid (opcional) | `SG.xxx` |

### Frontend (`.env`)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `VITE_API_URL` | URL base del backend | `http://localhost:8000` |

---

## Convención de ramas y commits

### Ramas

```
main              → producción, protegida, solo merge vía PR
develop           → integración, rama base para PRs
feature/HU-XXX    → rama por historia de usuario
```

### Flujo de trabajo

1. Crear rama desde `develop`: `git checkout -b feature/HU-XXX`
2. Hacer commits pequeños y descriptivos
3. Abrir Pull Request hacia `develop`
4. Mínimo 1 revisión de otro integrante antes de hacer merge
5. Borrar la rama después del merge

### Formato de commits

```
[HU-XXX] tipo: descripción corta

tipos: feat | fix | test | docs | refactor | chore
```

**Ejemplos:**

```
[HU-001] feat: agregar endpoint POST /api/usuarios/
[HU-012] feat: constructor de rúbricas con criterios y niveles
[HU-024] fix: validar nivel seleccionado pertenece al criterio
[HU-031] test: pruebas unitarias de autoevaluación
```

---

## Equipo

| Persona | Rol |
|---|---|
| Zharick Nicole Hernandez Arevalo | Desarrollador Backend |
| Angie Nikol Ortiz Amaya | Desarrollador Frontend |
| Daniela Garcia Peñaranda | Tester y Apoyo Backend |
| Jesús Gabriel Torres Daza | Desarrollador Backend |
| Alejandro Ovallos Torrado | Desarrollador Frontend |
| Emerson Amir Vera González | Tester y Apoyo Backend |
