import { BrowserRouter, Routes, Route, Navigate, Link, } from 'react-router-dom'
import PrivateRoute from './PrivateRoute'
import LoginForm from '../components/LoginForm'
import RegistroUsuarioForm from '../components/RegistroUsuarioForm'
import ConfiguracionParametros from '../components/ConfiguracionParametros'
import GestionPeriodos from '../components/GestionPeriodos'
import GestionRoles from '../components/GestionRoles'

// Paneles
function PanelAdmin() {
  return (
    <div className="min-h-screen bg-gray-50 p-10">
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">
        Panel Administrador
      </h1>

      <Link
        to="/admin/registro"
        className="bg-red-600 text-white px-4 py-2 rounded"
      >
        Registrar usuario
      </Link>
      <Link
        to="/admin/configuracion"
        className="bg-red-600 text-white px-4 py-2 rounded"
      >
        Configurar parámetros
      </Link>
      <Link
        to="/admin/periodos"
        className="bg-red-600 text-white px-4 py-2 rounded"
      >
        Gestión de Periodos
      </Link>
      <Link
        to="/admin/roles"
        className="bg-red-600 text-white px-4 py-2 rounded"
      >
        Gestión de Roles
      </Link>

    </div>
  )
}

function PanelDocente() { return <div className="p-10">Docente</div> }
function PanelDirector() { return <div className="p-10">Director</div> }
function PanelEstudiante() { return <div className="p-10">Estudiante</div> }
function PanelLider() { return <div className="p-10">Líder</div> }

function PaginaRegistro() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <RegistroUsuarioForm />
    </div>
  )
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>

        {/* PUBLICA */}
        <Route path="/login" element={<LoginForm />} />

        {/* ADMIN */}
        <Route element={<PrivateRoute allowedRoles={['administrador']} />}>
          <Route path="/admin" element={<PanelAdmin />} />
          <Route path="/admin/registro" element={<PaginaRegistro />} />
          <Route path="/admin/configuracion" element={<ConfiguracionParametros />} />
          <Route path="/admin/periodos" element={<GestionPeriodos />} />
          <Route path="/admin/roles" element={<GestionRoles />} />
        </Route>

        {/* DOCENTE */}
        <Route element={<PrivateRoute allowedRoles={['docente']} />}>
          <Route path="/docente" element={<PanelDocente />} />
        </Route>

        {/* DIRECTOR */}
        <Route element={<PrivateRoute allowedRoles={['director']} />}>
          <Route path="/director" element={<PanelDirector />} />
        </Route>

        {/* ESTUDIANTE */}
        <Route element={<PrivateRoute allowedRoles={['estudiante']} />}>
          <Route path="/estudiante" element={<PanelEstudiante />} />
        </Route>

        {/* LIDER */}
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