# Plataforma ABP — Gestión Integral del Aprendizaje Basado en Proyectos
Universidad Francisco de Paula Santander · Ingeniería de Sistemas · 2026

## Descripción
Sistema web para centralizar y estructurar los procesos del modelo de Aprendizaje Basado en Proyectos (ABP) en los cursos de Ingeniería de Sistemas.

## Tecnologías
| Capa | Tecnología |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Django 4.2 + Django REST Framework |
| Base de datos | PostgreSQL 15 |
| Autenticación | JWT (SimpleJWT) |

## Estructura del repositorio
```
abp-platform/
├── backend/          # Django + DRF
│   ├── apps/
│   │   ├── usuarios/
│   │   ├── roles/
│   │   ├── bitacora/
│   │   ├── cursos/
│   │   ├── equipos/
│   │   ├── entregables/
│   │   └── evaluacion/
│   ├── config/       # settings, urls, wsgi
│   ├── requirements.txt
│   └── manage.py
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/  # llamadas a la API
│   │   ├── hooks/
│   │   └── router/
│   ├── package.json
│   └── vite.config.js
├── api-contract.md   # Contrato de endpoints (fuente de verdad)
├── .gitignore
└── README.md
```

## Cómo levantar el proyecto localmente

### Requisitos previos
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 (local o Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # completar variables
python manage.py migrate
python manage.py loaddata seed_roles_permisos
python manage.py runserver
```
El backend queda disponible en http://localhost:8000

### Frontend
```bash
cd frontend
npm install
cp .env.example .env          # completar variables
npm run dev
```
El frontend queda disponible en http://localhost:5173

### Base de datos con Docker (opcional)
```bash
docker run --name abp-db \
  -e POSTGRES_DB=abp_db \
  -e POSTGRES_USER=abp_user \
  -e POSTGRES_PASSWORD=abp_pass \
  -p 5432:5432 \
  -d postgres:15
```

## Convención de ramas
```
main              → producción, protegida, solo merge via PR
develop           → integración, rama base para PRs
feature/HU-001    → rama por historia de usuario
feature/HU-002
...
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
Ejemplos:
```
[HU-001] feat: agregar endpoint POST /api/usuarios/
[HU-002] test: pruebas unitarias de autenticación JWT
[HU-003] fix: validar correo duplicado en serializer
```

## Equipo
| Persona | Rol | Sub-equipo |
|---|---|---|
| Persona 1 | Backend/BD | A (HU-001 a HU-004) |
| Persona 2 | Frontend | A (HU-001 a HU-004) |
| Persona 3 | Testing | A (HU-001 a HU-004) |
| Persona 4 | Backend/BD | B (HU-035, 036, 037) |
| Persona 5 | Frontend | B (HU-035, 036, 037) |
| Persona 6 | Testing | B (HU-035, 036, 037) |
