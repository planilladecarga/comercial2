import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Package, Search, FileText, Settings, Command } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: Command, label: 'Comando 360' },
  { to: '/envios', icon: Package, label: 'Envíos' },
  { to: '/trazabilidad', icon: Search, label: 'Trazabilidad' },
  { to: '/reportes', icon: FileText, label: 'Reportes' },
  { to: '/settings', icon: Settings, label: 'Configuración' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200 p-4">
        <h1 className="text-xl font-bold text-blue-700 mb-8">🐄 Trazabilidad</h1>
        <nav className="space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx('flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100')
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
