import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  return token ? children : <Navigate to="/login" replace />
}

// Placeholders — reemplazar con páginas reales
const LoginPage = () => <div>Login</div>
const AdminPage = () => <div>Admin</div>
const DocentePage = () => <div>Docente</div>
const EstudiantePage = () => <div>Estudiante</div>
const DirectorPage = () => <div>Director</div>
const PerfilPage = () => <div>Perfil</div>

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <AdminPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/docente"
          element={
            <PrivateRoute>
              <DocentePage />
            </PrivateRoute>
          }
        />
        <Route
          path="/estudiante"
          element={
            <PrivateRoute>
              <EstudiantePage />
            </PrivateRoute>
          }
        />
        <Route
          path="/director"
          element={
            <PrivateRoute>
              <DirectorPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/perfil"
          element={
            <PrivateRoute>
              <PerfilPage />
            </PrivateRoute>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
