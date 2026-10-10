import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import AppRouter from './router/index.jsx'

// Caché de datos del servidor (React Query). Un reintento y sin recargar al volver a la pestaña.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
      <Toaster position="top-right" toastOptions={{ style: { fontFamily: "'Manrope', sans-serif", fontSize: 13 } }} />
    </QueryClientProvider>
  )
}
