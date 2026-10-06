import { Toaster } from 'react-hot-toast'
import AppRouter from './router/index.jsx'

export default function App() {
  return (
    <>
      <AppRouter />
      <Toaster position="top-right" toastOptions={{ style: { fontFamily: "'Manrope', sans-serif", fontSize: 13 } }} />
    </>
  )
}
