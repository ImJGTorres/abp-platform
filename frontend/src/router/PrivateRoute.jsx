// Redirige a /login si no hay token activo.
// Si se pasa `allowedRoles`, también valida el rol del usuario.

import { Navigate, Outlet } from 'react-router-dom'
import { session } from '../services/api'

export default function PrivateRoute({ allowedRoles }) {
    // Sin token → redirige a login
    if (!session.isAuthenticated()) {
        return <Navigate to="/login" replace />
    }

    // Token presente pero rol no permitido → redirige a login
    if (allowedRoles) {
        const user = session.getUser()
        if (!user || !allowedRoles.includes(user.tipo_rol)) {
            return <Navigate to="/login" replace />
        }
    }

    // Todo OK → renderiza la ruta hija
    return <Outlet />
}