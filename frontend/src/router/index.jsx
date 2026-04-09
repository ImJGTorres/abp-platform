// Router principal de la aplicación ABP
// Todas las rutas definidas aquí — App.jsx solo monta este componente

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PrivateRoute from './PrivateRoute'
import LoginForm from '../components/LoginForm'
import RegistroUsuarioForm from '../components/RegistroUsuarioForm'

//Paneles placeholder

function PanelAdmin() {
  return (
    <div className="min-h-screen bg-gray-50 p-10">
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">Panel Administrador</h1>
      <a
        href="/admin/registro"
        className="inline-block bg-indigo-600 text-white text-sm font-medium  px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
      >
        + Registrar nuevo usuario
      </a>
    </div>
  )
}

function PanelDocente() { return <div className="p-10 text-xl text-gray-700">Panel Docente</div> }
function PanelDirector() { return <div className="p-10 text-xl text-gray-700">Panel Director</div> }
function PanelEstudiante() { return <div className="p-10 text-xl text-gray-700">Panel Estudiante</div> }
function PanelLider() { return <div className="p-10 text-xl text-gray-700">Panel Líder de Equipo</div> }

function ConfiguracionSistema() {
  return <div className="p-10 text-xl text-gray-700">Configuración del Sistema</div>
}

function PaginaRegistro() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <RegistroUsuarioForm />
    </div>
  )
}

//Router

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Pública */}
        <Route path="/login" element={<LoginForm />} />

        {/* Administrador */}
        <Route element={<PrivateRoute allowedRoles={['administrador']} />}>
          <Route path="/admin" element={<PanelAdmin />} />
          <Route path="/admin/registro" element={<PaginaRegistro />} />
          <Route path="/configuracionsistema" element={<ConfiguracionSistema />} />
        </Route>

        {/* Docente */}
        <Route element={<PrivateRoute allowedRoles={['docente']} />}>
          <Route path="/docente/*" element={<PanelDocente />} />
        </Route>

        {/* Director */}
        <Route element={<PrivateRoute allowedRoles={['director']} />}>
          <Route path="/director/*" element={<PanelDirector />} />
        </Route>

        {/* Estudiante */}
        <Route element={<PrivateRoute allowedRoles={['estudiante']} />}>
          <Route path="/estudiante/*" element={<PanelEstudiante />} />
        </Route>

        {/* Líder de equipo */}
        <Route element={<PrivateRoute allowedRoles={['lider_equipo']} />}>
          <Route path="/lider/*" element={<PanelLider />} />
        </Route>

        {/* Raíz y fallback → login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  )
}