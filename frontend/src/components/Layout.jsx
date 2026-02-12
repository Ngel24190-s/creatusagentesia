import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, ChefHat, Factory, FlaskConical, ShoppingCart,
  Bot, Menu, X, LogOut, Sprout
} from 'lucide-react'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/kitchen', icon: ChefHat, label: 'Cocina' },
  { path: '/production', icon: Factory, label: 'Produccion' },
  { path: '/laboratory', icon: FlaskConical, label: 'Laboratorio' },
  { path: '/sales', icon: ShoppingCart, label: 'Ventas' },
  { path: '/agents', icon: Bot, label: 'Agentes IA' },
]

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const { logout } = useAuth()

  return (
    <div className="min-h-screen flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-farm-800 text-white
        transform transition-transform lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <Sprout className="w-8 h-8 text-farm-300" />
            <div>
              <h1 className="text-xl font-bold">NosVers</h1>
              <p className="text-farm-300 text-xs">Pilotage Granja</p>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map(({ path, icon: Icon, label }) => {
              const active = location.pathname === path
              return (
                <Link
                  key={path}
                  to={path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    active
                      ? 'bg-farm-700 text-white'
                      : 'text-farm-200 hover:bg-farm-700/50 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{label}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2.5 w-full text-farm-300 hover:text-white hover:bg-farm-700/50 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Cerrar sesion</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <header className="bg-white border-b border-gray-200 px-4 py-3 lg:hidden flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)} className="p-1">
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex items-center gap-2">
            <Sprout className="w-5 h-5 text-farm-600" />
            <span className="font-bold text-farm-800">NosVers</span>
          </div>
        </header>
        <main className="p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
