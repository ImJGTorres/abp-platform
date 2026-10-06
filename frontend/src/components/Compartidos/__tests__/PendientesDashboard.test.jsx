import '@testing-library/jest-dom/vitest'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import PendientesDashboard from '../PendientesDashboard'
import DashboardEstudiante from '../../Estudiante/DashboardEstudiante'

// Respuesta según api-contract.md — GET /api/dashboard/pendientes/ (HU-038)
const CON_PENDIENTES = {
    al_dia: false,
    pendientes: [
        { tipo: 'vencido', titulo: 'Actividad vencida: Diagrama ER', fecha: '2026-10-03', urgencia: 3,
          enlace: '/estudiante/proyectos/1/actividades' },
        { tipo: 'proximo', titulo: 'Actividad por vencer: Informe final', fecha: '2026-10-06', urgencia: 2,
          enlace: '/estudiante/proyectos/1/actividades/7/entregables' },
        { tipo: 'alerta', titulo: 'Alerta sin proyecto', fecha: '2026-10-01', urgencia: 1, enlace: null },
    ],
    resumen: { total: 3, vencido: 1, proximo: 1, sin_calificar: 0, alerta: 1 },
}

const AL_DIA = {
    al_dia: true,
    pendientes: [],
    resumen: { total: 0, vencido: 0, proximo: 0, sin_calificar: 0, alerta: 0 },
}

function jsonResponse(body, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function mockFetch(rutas) {
    const fn = vi.fn(async (url) => {
        const path = new URL(url, 'http://localhost').pathname
        const r = rutas[path]
        if (!r) return jsonResponse({ detail: 'No encontrado' }, 404)
        return typeof r === 'function' ? r() : jsonResponse(r)
    })
    vi.stubGlobal('fetch', fn)
    return fn
}

function Ubicacion() {
    const { pathname } = useLocation()
    return <div data-testid="ubicacion">{pathname}</div>
}

function renderPanel(inicio = '/inicio') {
    return render(
        <MemoryRouter initialEntries={[inicio]}>
            <Routes>
                <Route path="/inicio" element={<PendientesDashboard />} />
                <Route path="*" element={<Ubicacion />} />
            </Routes>
        </MemoryRouter>
    )
}

beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('access_token', 'token-de-prueba')
})

afterEach(() => {
    vi.unstubAllGlobals()
})

describe('PendientesDashboard (HU-038 / SCRUM-513)', () => {
    it('consume GET /api/dashboard/pendientes/ con el token del usuario', async () => {
        const fetchMock = mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        await screen.findByText('Actividad vencida: Diagrama ER')
        expect(fetchMock).toHaveBeenCalledTimes(1)
        const [url, opts] = fetchMock.mock.calls[0]
        expect(url).toBe('/api/dashboard/pendientes/')
        expect(opts.headers.Authorization).toBe('Bearer token-de-prueba')
    })

    it('muestra las tarjetas de resumen por tipo con sus conteos', async () => {
        mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        await screen.findByText('Actividad vencida: Diagrama ER')
        const conteo = (label) => screen.getByText(label, { selector: 'p' }).previousSibling.textContent
        expect(conteo('Vencidos')).toBe('1')
        expect(conteo('Próximos')).toBe('1')
        expect(conteo('Sin calificar')).toBe('0')
        expect(conteo('Alertas')).toBe('1')
    })

    it('lista los pendientes en el orden de urgencia que entrega el backend', async () => {
        mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        await screen.findByText('Actividad vencida: Diagrama ER')
        const items = within(screen.getByRole('list')).getAllByRole('listitem')
        expect(items.map(li => li.textContent)).toEqual([
            expect.stringContaining('Diagrama ER'),
            expect.stringContaining('Informe final'),
            expect.stringContaining('Alerta sin proyecto'),
        ])
        expect(items[0]).toHaveTextContent('Vencido')
        expect(items[1]).toHaveTextContent('Próximo')
        expect(items[2]).toHaveTextContent('Alerta')
    })

    it('formatea la fecha YYYY-MM-DD sin desfase de zona horaria', async () => {
        mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        const item = (await screen.findByText('Actividad vencida: Diagrama ER')).closest('li')
        expect(item).toHaveTextContent(/3 .*oct.* 2026/i)
    })

    it('navega al enlace directo del pendiente al hacer clic', async () => {
        mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        await userEvent.click(await screen.findByRole('button', { name: /Informe final/ }))
        expect(screen.getByTestId('ubicacion')).toHaveTextContent('/estudiante/proyectos/1/actividades/7/entregables')
    })

    it('un pendiente con enlace null no es clicable', async () => {
        mockFetch({ '/api/dashboard/pendientes/': CON_PENDIENTES })
        renderPanel()

        const item = (await screen.findByText('Alerta sin proyecto')).closest('li')
        expect(within(item).queryByRole('button')).toBeNull()
    })

    it('muestra el estado "al día" cuando no hay pendientes', async () => {
        mockFetch({ '/api/dashboard/pendientes/': AL_DIA })
        renderPanel()

        expect(await screen.findByText('¡Estás al día!')).toBeInTheDocument()
        expect(screen.queryByRole('list')).toBeNull()
        expect(screen.queryByText('Vencidos')).toBeNull()
    })

    it('muestra el error del backend si la petición falla', async () => {
        mockFetch({ '/api/dashboard/pendientes/': () => jsonResponse({ detail: 'Error interno' }, 500) })
        renderPanel()

        expect(await screen.findByText('Error interno')).toBeInTheDocument()
    })

    it('el botón Actualizar vuelve a consultar el endpoint', async () => {
        let llamada = 0
        const fetchMock = mockFetch({
            '/api/dashboard/pendientes/': () => jsonResponse(++llamada === 1 ? CON_PENDIENTES : AL_DIA),
        })
        renderPanel()

        await screen.findByText('Actividad vencida: Diagrama ER')
        await userEvent.click(screen.getByTitle('Actualizar'))
        expect(await screen.findByText('¡Estás al día!')).toBeInTheDocument()
        expect(fetchMock).toHaveBeenCalledTimes(2)
    })
})

describe('Integración en pantallas de inicio', () => {
    it('DashboardEstudiante muestra el panel de pendientes junto a sus proyectos', async () => {
        mockFetch({
            '/api/mis-equipos/': [],
            '/api/dashboard/pendientes/': CON_PENDIENTES,
        })
        render(
            <MemoryRouter>
                <DashboardEstudiante />
            </MemoryRouter>
        )

        expect(await screen.findByText('Mis pendientes')).toBeInTheDocument()
        expect(await screen.findByText('Actividad vencida: Diagrama ER')).toBeInTheDocument()
        expect(screen.getByText('Mis proyectos')).toBeInTheDocument()
    })
})
