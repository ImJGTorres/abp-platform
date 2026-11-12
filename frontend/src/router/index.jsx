import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import PrivateRoute from './PrivateRoute'
const AdminLayout = lazy(() => import('../components/AdminLayout'))
const AdminPlaceholder = lazy(() => import('../components/AdminPlaceholder'))
const LoginForm = lazy(() => import('../components/LoginForm'))
const RegistroUsuarioForm = lazy(() => import('../components/RegistroUsuarioForm'))
const CargaMasivaEstudiantes = lazy(() => import('../components/CargaMasivaEstudiantes'))
const GestionUsuarios = lazy(() => import('../components/GestionUsuarios'))
const GestionCursosAdmin = lazy(() => import('../components/GestionCursosAdmin'))
const ConfiguracionParametros = lazy(() => import('../components/ConfiguracionParametros'))
const GestionPeriodos = lazy(() => import('../components/GestionPeriodos'))
const GestionRoles = lazy(() => import('../components/GestionRoles'))
const BitacorasAuditoria = lazy(() => import('../components/BitacorasAuditoria'))
const ProfileEdit = lazy(() => import('../components/ProfileEdit'))
const OlvidarContrasena = lazy(() => import('../components/OlvidarContrasena'))
const ResetContrasena = lazy(() => import('../components/ResetContrasena'))

const DocenteLayout = lazy(() => import('../components/docente/DocenteLayout'))
const GestionCursos = lazy(() => import('../components/docente/GestionCursos'))
const DetalleCurso = lazy(() => import('../components/docente/DetalleCurso'))
const GestionEquipos = lazy(() => import('../components/docente/GestionEquipos'))
const AsignarEstudiantes = lazy(() => import('../components/docente/AsignarEstudiantes'))
const EstudiantesCurso = lazy(() => import('../components/docente/EstudiantesCurso'))
const ObjetivosProyecto = lazy(() => import('../components/docente/ObjetivosProyecto'))
const RAPsProyecto = lazy(() => import('../components/docente/RAPsProyecto'))
const ProyectoLayout = lazy(() => import('../components/docente/ProyectoLayout'))
const CronogramaProyecto = lazy(() => import('../components/docente/CronogramaProyecto'))
const PerfilesRolesProyecto = lazy(() => import('../components/docente/PerfilesRolesProyecto'))
const ReorganizarEquipos = lazy(() => import('../components/docente/ReorganizarEquipos'))
const EquiposCurso = lazy(() => import('../components/docente/EquiposCurso'))
const GestionFases = lazy(() => import('../components/docente/GestionFases'))
const GestionActividades = lazy(() => import('../components/docente/GestionActividades'))
const PanelRevisionEntregables = lazy(() => import('../components/docente/PanelRevisionEntregables'))
const ActividadLayout = lazy(() => import('../components/docente/ActividadLayout'))
const DetalleActividad = lazy(() => import('../components/docente/DetalleActividad'))
const ConstructorRubricas = lazy(() => import('../components/docente/ConstructorRubricas'))
const HistorialEvaluaciones = lazy(() => import('../components/docente/HistorialEvaluaciones'))
const EstudiantesRiesgo = lazy(() => import('../components/docente/EstudiantesRiesgo'))
const PerfilRendimientoEstudiante = lazy(() => import('../components/docente/PerfilRendimientoEstudiante'))
const MonitoreoProyecto = lazy(() => import('../components/docente/MonitoreoProyecto'))
const PanelSemaforosDocente = lazy(() => import('../components/docente/PanelSemaforosDocente'))
const BancoRubricas = lazy(() => import('../components/docente/BancoRubricas'))
const AutoevaluacionesDocente = lazy(() => import('../components/docente/AutoevaluacionesDocente'))
const CoevaluacionesDocente = lazy(() => import('../components/docente/CoevaluacionesDocente'))

const EstudianteLayout = lazy(() => import('../components/Estudiante/EstudianteLayout'))
const DashboardEstudiante = lazy(() => import('../components/Estudiante/DashboardEstudiante'))
const MisProyectos = lazy(() => import('../components/Estudiante/MisProyectos'))
const EntregablesActividad = lazy(() => import('../components/Estudiante/EntregablesActividad'))
const ProyectoEstudianteLayout = lazy(() => import('../components/Estudiante/ProyectoEstudianteLayout'))
const Autoevaluacion = lazy(() => import('../components/Estudiante/Autoevaluacion'))
const Coevaluacion = lazy(() => import('../components/Estudiante/Coevaluacion'))

const LiderLayout = lazy(() => import('../components/LiderEquipo/LiderLayout'))
const DashboardLider = lazy(() => import('../components/LiderEquipo/DashboardLider'))
const DistribucionTrabajo = lazy(() => import('../components/LiderEquipo/DistribucionTrabajo'))
const AsignarResponsables = lazy(() => import('../components/LiderEquipo/AsignarResponsables'))

const DetalleProyectoEstudiante = lazy(() => import('../components/Estudiante/DetalleProyectoEstudiante'))
const HistorialEvaluacionesEstudiante = lazy(() => import('../components/Estudiante/HistorialEvaluacionesEstudiante'))
const TableroKanban = lazy(() => import('../components/Compartidos/TableroKanban'))
const CalendarioPage = lazy(() => import('../components/Compartidos/CalendarioPage'))
const DashboardProgreso = lazy(() => import('../components/Estudiante/DashboardProgreso'))

const DirectorLayout = lazy(() => import('../components/director/DirectorLayout'))
const DashboardDirector = lazy(() => import('../components/director/DashboardDirector'))
const ListaReportes = lazy(() => import('../components/director/ListaReportes'))
const ReporteProyecto = lazy(() => import('../components/director/ReporteProyecto'))
const EstudiantesRiesgoDirector = lazy(() => import('../components/director/EstudiantesRiesgoDirector'))
const ResultadosBusqueda = lazy(() => import('../components/Compartidos/ResultadosBusqueda'))
const IdentidadInstitucional = lazy(() => import('../components/IdentidadInstitucional'))

// Redirige conservando location.state (origen de navegación, nombres para migas)
function RedirigirConEstado({ to }) {
  const { state } = useLocation()
  return <Navigate to={to} replace state={state} />
}

function PanelEstudiante() { return <div className="p-10">Estudiante</div> }

function Pagina({ children }) {
  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6">
      {children}
    </div>
  )
}

function PaginaRegistro() {
  return (
    <Pagina>
      <div className="flex flex-col gap-6 pt-2">
        <GestionUsuarios />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RegistroUsuarioForm />
          <CargaMasivaEstudiantes />
        </div>
      </div>
    </Pagina>
  )
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="p-6 text-sm text-gray-500">Cargando…</div>}>
      <Routes>

        {/* PÚBLICA */}
        <Route path="/login" element={<LoginForm />} />
        <Route path="/olvidar-contrasena" element={<OlvidarContrasena />} />
        <Route path="/recuperar-contrasena" element={<ResetContrasena />} />

        {/* PERFIL */}
        <Route element={<PrivateRoute />}>
          <Route path="/perfil" element={<ProfileEdit />} />
        </Route>

        {/* ADMIN */}
        <Route element={<PrivateRoute allowedRoles={['administrador']} />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminPlaceholder />} />
            <Route path="/admin/registro" element={<PaginaRegistro />} />
            <Route path="/admin/cursos" element={<Pagina><GestionCursosAdmin /></Pagina>} />
            <Route path="/admin/cursos/:id" element={<DetalleCurso />} />
            <Route path="/admin/configuracion" element={<Pagina><ConfiguracionParametros /></Pagina>} />
            <Route path="/admin/periodos" element={<Pagina><GestionPeriodos /></Pagina>} />
            <Route path="/admin/bitacoras" element={<Pagina><BitacorasAuditoria /></Pagina>} />
            <Route path="/admin/roles" element={<GestionRoles />} />
            <Route path="/admin/identidad" element={<Pagina><IdentidadInstitucional /></Pagina>} />
            <Route path="/admin/busqueda" element={<ResultadosBusqueda />} />
          </Route>
        </Route>

        {/* DOCENTE */}
        <Route element={<PrivateRoute allowedRoles={['docente', 'administrador']} />}>
          <Route element={<DocenteLayout />}>
            <Route path="/docente" element={<Navigate to="/docente/cursos" replace />} />
            <Route path="/docente/cursos" element={<GestionCursos />} />
            <Route path="/docente/calendario" element={<CalendarioPage />} />
            <Route path="/docente/semaforos" element={<PanelSemaforosDocente />} />
            <Route path="/docente/rubricas" element={<BancoRubricas />} />
            <Route path="/docente/cursos/:id" element={<DetalleCurso />} />
            <Route path="/docente/cursos/:id/estudiantes" element={<EstudiantesCurso />} />
            <Route path="/docente/cursos/:id/equipos" element={<EquiposCurso />} />
            <Route path="/docente/cursos/:cursoId/reorganizar" element={<ReorganizarEquipos />} />
            <Route path="/docente/proyectos/:proyectoId/equipos" element={<GestionEquipos />} />
            <Route path="/docente/equipos/:equipoId/asignar" element={<AsignarEstudiantes />} />
            <Route path="/docente/cursos/:cursoId/riesgo" element={<EstudiantesRiesgo />} />
            <Route path="/docente/estudiantes/:estudianteId/rendimiento" element={<PerfilRendimientoEstudiante />} />
          </Route>

          <Route element={<ProyectoLayout />}>
            <Route path="/docente/proyectos/:proyectoId/objetivos" element={<ObjetivosProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/raps" element={<RAPsProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/cronograma" element={<CronogramaProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/fases" element={<GestionFases />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades" element={<GestionActividades />} />
            <Route path="/docente/proyectos/:proyectoId/kanban" element={<TableroKanban />} />
            <Route path="/docente/proyectos/:proyectoId/perfiles-roles" element={<PerfilesRolesProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/historial" element={<HistorialEvaluaciones />} />
            <Route path="/docente/proyectos/:proyectoId/autoevaluaciones" element={<AutoevaluacionesDocente />} />
            <Route path="/docente/proyectos/:proyectoId/coevaluaciones" element={<CoevaluacionesDocente />} />
            <Route path="/docente/proyectos/:proyectoId/monitoreo" element={<MonitoreoProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/rubricas" element={<ConstructorRubricas />} />
          </Route>

          {/* Layout de actividad — Actividad / Entregables / Rúbricas */}
          <Route element={<ActividadLayout />}>
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades/:actividadId" element={<RedirigirConEstado to="actividad" />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades/:actividadId/actividad" element={<DetalleActividad />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades/:actividadId/entregables" element={<PanelRevisionEntregables />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades/:actividadId/rubricas" element={<ConstructorRubricas />} />
          </Route>
        </Route>

        {/* DIRECTOR */}
        <Route element={<PrivateRoute allowedRoles={['director', 'administrador']} />}>
          <Route element={<DirectorLayout />}>
            <Route path="/director" element={<DashboardDirector />} />
            <Route path="/director/indicadores" element={<DashboardDirector />} />
            <Route path="/director/riesgo" element={<EstudiantesRiesgoDirector />} />
            <Route path="/director/reportes" element={<ListaReportes />} />
            <Route path="/director/reportes/proyecto/:proyectoId" element={<ReporteProyecto />} />
            <Route path="/director/calendario" element={<CalendarioPage />} />
            <Route path="/director/busqueda" element={<ResultadosBusqueda />} />
          </Route>
        </Route>

        {/* ESTUDIANTE */}
        <Route element={<PrivateRoute allowedRoles={['estudiante', 'lider_equipo']} />}>
          {/* Dashboard */}
          <Route element={<EstudianteLayout />}>
            <Route path="/estudiante" element={<Navigate to="/estudiante/dashboard" replace />} />
            <Route path="/estudiante/dashboard" element={<DashboardEstudiante />} />
            <Route path="/estudiante/proyectos" element={<MisProyectos />} />
            <Route path="/estudiante/calendario" element={<CalendarioPage />} />
          </Route>

          {/* Layout por proyecto — sidebar centralizado */}
          <Route element={<ProyectoEstudianteLayout />}>
            <Route path="/estudiante/proyectos/:proyectoId" element={<RedirigirConEstado to="actividades" />} />
            <Route path="/estudiante/proyectos/:proyectoId/actividades" element={<DetalleProyectoEstudiante />} />
            <Route path="/estudiante/proyectos/:proyectoId/actividades/:actividadId/entregables" element={<EntregablesActividad />} />
            <Route path="/estudiante/proyectos/:proyectoId/kanban" element={<TableroKanban />} />
            <Route path="/estudiante/proyectos/:proyectoId/progreso" element={<DashboardProgreso />} />
            <Route path="/estudiante/proyectos/:proyectoId/autoevaluacion" element={<Autoevaluacion />} />
            <Route path="/estudiante/proyectos/:proyectoId/coevaluacion" element={<Coevaluacion />} />
            <Route path="/estudiante/proyectos/:proyectoId/historial" element={<HistorialEvaluacionesEstudiante />} />
            {/* Líder de Equipo — gestión del equipo dentro del proyecto */}
            <Route path="/estudiante/proyectos/:proyectoId/equipo/dashboard" element={<DashboardLider />} />
            <Route path="/estudiante/proyectos/:proyectoId/equipo/distribucion" element={<DistribucionTrabajo />} />
            <Route path="/estudiante/proyectos/:proyectoId/equipo/responsables" element={<AsignarResponsables />} />
          </Route>
        </Route>

        {/* LÍDER */}
        <Route element={<PrivateRoute allowedRoles={['lider_equipo']} />}>
          <Route element={<LiderLayout />}>
            <Route path="/lider" element={<Navigate to="/lider/inicio" replace />} />
            <Route path="/lider/inicio" element={<DashboardEstudiante />} />
            <Route path="/lider/proyectos" element={<MisProyectos />} />
            <Route path="/lider/dashboard" element={<DashboardLider />} />
            <Route path="/lider/distribucion" element={<DistribucionTrabajo />} />
            <Route path="/lider/asignar-responsables" element={<AsignarResponsables />} />
            <Route path="/lider/actividades/:actividadId/entregables" element={<EntregablesActividad />} />
            <Route path="/lider/proyectos/:proyectoId/kanban" element={<TableroKanban />} />
            <Route path="/lider/calendario" element={<CalendarioPage />} />
          </Route>
        </Route>

        {/* DEFAULT */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
      </Suspense>
    </BrowserRouter>
  )
}