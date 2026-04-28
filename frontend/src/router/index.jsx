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

function PanelDirector() { return <div className="p-10">Director</div> }
function PanelEstudiante() { return <div className="p-10">Estudiante</div> }
function PanelLider() { return <div className="p-10">Líder</div> }

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
            <Route path="/docente/proyectos/:proyectoId/equipos" element={<GestionEquipos />} />
            <Route path="/docente/equipos/:equipoId/asignar" element={<AsignarEstudiantes />} />
          </Route>
        </Route>

        {/* DIRECTOR */}
        <Route element={<PrivateRoute allowedRoles={['director']} />}>
          <Route path="/director" element={<PanelDirector />} />
        </Route>

        {/* ESTUDIANTE */}
        <Route element={<PrivateRoute allowedRoles={['estudiante']} />}>
          <Route path="/estudiante" element={<PanelEstudiante />} />
        </Route>

        {/* LÍDER */}
        <Route element={<PrivateRoute allowedRoles={['lider_equipo']} />}>
          <Route path="/lider" element={<PanelLider />} />
        </Route>

        {/* DEFAULT */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  )
}