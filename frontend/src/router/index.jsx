import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PrivateRoute from './PrivateRoute'
import AdminLayout from '../components/AdminLayout'
import AdminPlaceholder from '../components/AdminPlaceholder'
import LoginForm from '../components/LoginForm'
import RegistroUsuarioForm from '../components/RegistroUsuarioForm'
import CargaMasivaEstudiantes from '../components/CargaMasivaEstudiantes'
import GestionUsuarios from '../components/GestionUsuarios'
import GestionCursosAdmin from '../components/GestionCursosAdmin'
import ConfiguracionParametros from '../components/ConfiguracionParametros'
import GestionPeriodos from '../components/GestionPeriodos'
import GestionRoles from '../components/GestionRoles'
import BitacorasAuditoria from '../components/BitacorasAuditoria'
import ProfileEdit from '../components/ProfileEdit'
import OlvidarContrasena from '../components/OlvidarContrasena'
import ResetContrasena from '../components/ResetContrasena'

import DocenteLayout from '../components/docente/DocenteLayout'
import GestionCursos from '../components/docente/GestionCursos'
import DetalleCurso from '../components/docente/DetalleCurso'
import GestionEquipos from '../components/docente/GestionEquipos'
import AsignarEstudiantes from '../components/docente/AsignarEstudiantes'
import EstudiantesCurso from '../components/docente/EstudiantesCurso'
import ObjetivosProyecto from '../components/docente/ObjetivosProyecto'
import RAPsProyecto from '../components/docente/RAPsProyecto'
import ProyectoLayout from '../components/docente/ProyectoLayout'
import CronogramaProyecto from '../components/docente/CronogramaProyecto'
import PerfilesRolesProyecto from '../components/docente/PerfilesRolesProyecto'
import EquipoProyecto from '../components/docente/EquipoProyecto'
import ReorganizarEquipos from '../components/docente/ReorganizarEquipos'
import CronogramaHitos from '../components/docente/CronogramaHitos'
import EquiposCurso from '../components/docente/EquiposCurso'
import GestionFases from '../components/docente/GestionFases'
import GestionActividades from '../components/docente/GestionActividades'
import PanelRevisionEntregables from '../components/docente/PanelRevisionEntregables'

import EstudianteLayout from '../components/estudiante/EstudianteLayout'
import DashboardEstudiante from '../components/estudiante/DashboardEstudiante'
import EntregablesActividad from '../components/estudiante/EntregablesActividad'

import LiderLayout from '../components/LiderEquipo/LiderLayout'
import DashboardLider from '../components/LiderEquipo/DashboardLider'
import DistribucionTrabajo from '../components/LiderEquipo/DistribucionTrabajo'
import CargaTrabajoMiembros from '../components/LiderEquipo/CargaTrabajoMiembros'


import EstudianteLayout from '../components/Estudiante/EstudianteLayout'
import DetalleProyectoEstudiante from '../components/Estudiante/DetalleProyectoEstudiante'
import TableroKanban from '../components/Compartidos/TableroKanban'
import DashboardProgreso from '../components/Estudiante/DashboardProgreso'

function PanelDirector() { return <div className="p-10">Director</div> }
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
            <Route path="/admin/configuracion" element={<Pagina><ConfiguracionParametros /></Pagina>} />
            <Route path="/admin/periodos" element={<Pagina><GestionPeriodos /></Pagina>} />
            <Route path="/admin/bitacoras" element={<Pagina><BitacorasAuditoria /></Pagina>} />
            <Route path="/admin/roles" element={<GestionRoles />} />
          </Route>
        </Route>

        {/* DOCENTE */}
        <Route element={<PrivateRoute allowedRoles={['docente']} />}>
          <Route element={<DocenteLayout />}>
            <Route path="/docente" element={<Navigate to="/docente/cursos" replace />} />
            <Route path="/docente/cursos" element={<GestionCursos />} />
            <Route path="/docente/cursos/:id" element={<DetalleCurso />} />
            <Route path="/docente/cursos/:id/estudiantes" element={<EstudiantesCurso />} />
            <Route path="/docente/cursos/:id/equipos" element={<EquiposCurso />} />
            <Route path="/docente/cursos/:cursoId/proyectos/:proyectoId/equipo" element={<EquipoProyecto />} />
            <Route path="/docente/cursos/:cursoId/reorganizar" element={<ReorganizarEquipos />} />
            <Route path="/docente/cursos/:cursoId/proyectos/:proyectoId/cronograma" element={<CronogramaHitos />} />
            <Route path="/docente/proyectos/:proyectoId/equipos" element={<GestionEquipos />} />
            <Route path="/docente/equipos/:equipoId/asignar" element={<AsignarEstudiantes />} />
          </Route>

          <Route element={<ProyectoLayout />}>
            <Route path="/docente/proyectos/:proyectoId/objetivos" element={<ObjetivosProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/raps" element={<RAPsProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/cronograma" element={<CronogramaProyecto />} />
            <Route path="/docente/proyectos/:proyectoId/fases" element={<GestionFases />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades" element={<GestionActividades />} />
            <Route path="/docente/proyectos/:proyectoId/kanban" element={<TableroKanban />} />
            <Route path="/docente/proyectos/:proyectoId/fases/:faseId/actividades/:actividadId/entregables" element={<PanelRevisionEntregables />} />
            <Route path="/docente/proyectos/:proyectoId/perfiles-roles" element={<PerfilesRolesProyecto />} />
          </Route>
        </Route>

        {/* DIRECTOR */}
        <Route element={<PrivateRoute allowedRoles={['director']} />}>
          <Route path="/director" element={<PanelDirector />} />
        </Route>

        {/* ESTUDIANTE */}
        <Route element={<PrivateRoute allowedRoles={['estudiante']} />}>
          <Route element={<EstudianteLayout />}>
            <Route path="/estudiante" element={<Navigate to="/estudiante/dashboard" replace />} />
            <Route path="/estudiante/dashboard" element={<DashboardProgreso />} />
            {/* OVALLOS --> <Route path="/estudiante/dashboard" element={<DashboardEstudiante />} /> */}
            <Route path="/estudiante/proyectos/:proyectoId" element={<DetalleProyectoEstudiante />} />
            <Route path="/estudiante/proyectos/:proyectoId/progreso" element={<DashboardProgreso />} />
            <Route path="/estudiante/proyectos/:proyectoId/kanban" element={<TableroKanban />} />
            <Route path="/estudiante/actividades/:actividadId/entregables" element={<EntregablesActividad />} />
          </Route>
        </Route>

        {/* LÍDER */}
        <Route element={<PrivateRoute allowedRoles={['lider_equipo']} />}>
          <Route element={<LiderLayout />}>
            <Route path="/lider" element={<Navigate to="/lider/dashboard" replace />} />
            <Route path="/lider/dashboard" element={<DashboardLider />} />
            <Route path="/lider/distribucion" element={<DistribucionTrabajo />} />
            <Route path="/lider/carga-trabajo" element={<CargaTrabajoMiembros />} />
          </Route>
        </Route>

        {/* DEFAULT */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  )
}