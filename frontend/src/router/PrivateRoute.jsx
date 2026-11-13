/**  Redirige a /login si no hay token activo.
Si se pasa `allowedRoles`, también valida el rol del usuario.
IMPORTANTE: esta comprobación es solo de interfaz. Lee el token y
el rol desde localStorage, que el usuario puede modificar, así que únicamente
oculta pantallas. El permiso real lo decide el backend en cada petición
JWT + permisos de DRF); ningún dato sensible debe depender de esta ruta.
*/

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