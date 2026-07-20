import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Shipments } from './pages/Shipments'
import { Trace } from './pages/Trace'
import { Reports } from './pages/Reports'
import { Settings } from './pages/Settings'
import { Login } from './pages/Login'
import { Comando360 } from './pages/Comando360'
import { BusinessQuery } from './pages/BusinessQuery'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <Layout>
              <Routes>
                <Route path="/" element={<Comando360 />} />
                <Route path="/query" element={<BusinessQuery />} />
                <Route path="/envios" element={<Shipments />} />
                <Route path="/trazabilidad" element={<Trace />} />
                <Route path="/reportes" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          } />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}
