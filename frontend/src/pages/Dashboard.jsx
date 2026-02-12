import { useState, useEffect } from 'react'
import { api } from '../services/api'
import {
  TrendingUp, Package, AlertTriangle, Euro, ShoppingCart,
  Factory, FlaskConical, Bot, ArrowUpRight
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#16a34a', '#22c55e', '#4ade80', '#86efac']

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [aiHealth, setAiHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getDashboard().catch(() => null),
      api.getHungryAlerts().catch(() => []),
      api.getAgentHealth().catch(() => null),
    ]).then(([d, a, h]) => {
      setDashboard(d)
      setAlerts(a || [])
      setAiHealth(h)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Cargando dashboard...</div></div>

  const stats = [
    {
      label: 'Ingresos del mes',
      value: `${dashboard?.monthly_revenue?.toFixed(2) || '0.00'} EUR`,
      icon: Euro,
      color: 'text-green-600 bg-green-100',
    },
    {
      label: 'Objetivo mensual',
      value: `${dashboard?.progress_pct?.toFixed(0) || 0}%`,
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100',
      sub: `de 1.800 EUR`,
    },
    {
      label: 'IBCs activos',
      value: dashboard?.active_ibcs || 0,
      icon: Factory,
      color: 'text-purple-600 bg-purple-100',
    },
    {
      label: 'Stock productos',
      value: dashboard?.total_stock || 0,
      icon: Package,
      color: 'text-orange-600 bg-orange-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Vista general de la granja</p>
        </div>
        <Link to="/agents" className="btn-primary flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Consultar IA
        </Link>
      </div>

      {/* Alert banner */}
      {alerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium text-red-800">
              {alerts.length} IBC(s) necesitan alimentacion
            </p>
            <p className="text-red-600 text-sm mt-1">
              {alerts.map(a => a.code || a.ibc_code).join(', ')} llevan mas de 3 dias sin comer
            </p>
            <Link to="/production" className="text-red-700 text-sm font-medium underline mt-1 inline-block">
              Ir a Produccion
            </Link>
          </div>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="card">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-xl font-bold">{stat.value}</p>
                {stat.sub && <p className="text-xs text-gray-400">{stat.sub}</p>}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue progress */}
        <div className="card">
          <h3 className="font-semibold mb-4">Progreso objetivo mensual</h3>
          <div className="relative pt-1">
            <div className="flex mb-2 items-center justify-between">
              <span className="text-sm font-medium text-farm-700">
                {dashboard?.monthly_revenue?.toFixed(0) || 0} EUR
              </span>
              <span className="text-sm font-medium text-gray-500">1.800 EUR</span>
            </div>
            <div className="overflow-hidden h-4 text-xs flex rounded-full bg-farm-100">
              <div
                style={{ width: `${Math.min(dashboard?.progress_pct || 0, 100)}%` }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-farm-500 rounded-full transition-all duration-500"
              />
            </div>
          </div>
        </div>

        {/* AI Health summary */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-5 h-5 text-farm-600" />
            <h3 className="font-semibold">Analisis IA de la granja</h3>
          </div>
          {aiHealth ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  aiHealth.overall_score >= 80 ? 'bg-green-500' :
                  aiHealth.overall_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="font-medium">Salud general: {aiHealth.overall_score}/100</span>
              </div>
              {aiHealth.alerts?.slice(0, 3).map((alert, i) => (
                <div key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-yellow-500 mt-0.5">!</span>
                  <span>{alert}</span>
                </div>
              ))}
              <Link to="/agents" className="text-farm-600 text-sm font-medium flex items-center gap-1">
                Ver analisis completo <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Conecta con los agentes IA para ver el analisis</p>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { to: '/kitchen', icon: '🧪', label: 'Nuevo precompost', desc: 'Crear lote' },
          { to: '/production', icon: '🐛', label: 'Alimentar IBC', desc: 'Registrar comida' },
          { to: '/laboratory', icon: '📦', label: 'Nuevo producto', desc: 'Registrar cosecha' },
          { to: '/sales', icon: '💰', label: 'Nueva venta', desc: 'Registrar venta' },
        ].map(action => (
          <Link key={action.to} to={action.to} className="card hover:shadow-md transition-shadow group">
            <span className="text-2xl">{action.icon}</span>
            <p className="font-medium mt-2 group-hover:text-farm-600 transition-colors">{action.label}</p>
            <p className="text-xs text-gray-400">{action.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
