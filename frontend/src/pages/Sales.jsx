import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Euro, TrendingUp, ShoppingCart, Globe, Store } from 'lucide-react'

export default function Sales() {
  const [sales, setSales] = useState([])
  const [products, setProducts] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const [form, setForm] = useState({ product_id: '', source: 'DIRECT', quantity: '', amount_eur: '' })

  useEffect(() => {
    Promise.all([
      api.getSales().catch(() => []),
      api.getProducts().catch(() => []),
      api.getDashboard().catch(() => null),
    ]).then(([s, p, d]) => {
      setSales(s || [])
      setProducts(p || [])
      setDashboard(d)
      setLoading(false)
    })
  }, [])

  const submitSale = async (e) => {
    e.preventDefault()
    const data = {
      product_id: parseInt(form.product_id),
      source: form.source,
      quantity: parseInt(form.quantity),
      amount_eur: parseFloat(form.amount_eur),
    }
    const result = await api.createSale(data)
    setSales([result, ...sales])
    setForm({ product_id: '', source: 'DIRECT', quantity: '', amount_eur: '' })
    setShowForm(false)
    // Refresh dashboard
    api.getDashboard().then(d => setDashboard(d)).catch(() => {})
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Cargando...</div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ventas</h1>
          <p className="text-gray-500">Registro y seguimiento de ventas</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva venta
        </button>
      </div>

      {/* Stats */}
      {dashboard && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="card flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-green-100">
              <Euro className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Ingresos del mes</p>
              <p className="text-xl font-bold">{dashboard.monthly_revenue?.toFixed(2)} EUR</p>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-100">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Progreso objetivo</p>
              <p className="text-xl font-bold">{dashboard.progress_pct?.toFixed(1)}%</p>
            </div>
          </div>
          <div className="card flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-100">
              <ShoppingCart className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Ventas totales</p>
              <p className="text-xl font-bold">{sales.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* Sale form */}
      {showForm && (
        <form onSubmit={submitSale} className="card space-y-4">
          <h3 className="font-semibold">Registrar venta</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <select className="input-field" value={form.product_id} onChange={e => setForm({...form, product_id: e.target.value})} required>
              <option value="">Seleccionar producto...</option>
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.batch_code} ({p.packaging_size} - Stock: {p.stock_qty})</option>
              ))}
            </select>
            <select className="input-field" value={form.source} onChange={e => setForm({...form, source: e.target.value})}>
              <option value="DIRECT">Venta directa</option>
              <option value="WEB">Web (WooCommerce)</option>
            </select>
            <input className="input-field" type="number" placeholder="Cantidad" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} required />
            <input className="input-field" type="number" step="0.01" placeholder="Importe (EUR)" value={form.amount_eur} onChange={e => setForm({...form, amount_eur: e.target.value})} required />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Registrar venta</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* Sales table */}
      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-4">Historial de ventas</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="pb-2 font-medium">Fecha</th>
              <th className="pb-2 font-medium">Producto</th>
              <th className="pb-2 font-medium">Canal</th>
              <th className="pb-2 font-medium">Cantidad</th>
              <th className="pb-2 font-medium text-right">Importe</th>
            </tr>
          </thead>
          <tbody>
            {sales.map(sale => (
              <tr key={sale.id} className="border-b border-gray-50">
                <td className="py-2.5">{new Date(sale.date || sale.created_at).toLocaleDateString('es')}</td>
                <td className="py-2.5 font-mono text-sm">{sale.product?.batch_code || `#${sale.product_id}`}</td>
                <td className="py-2.5">
                  <span className={`inline-flex items-center gap-1 ${sale.source === 'WEB' ? 'text-blue-600' : 'text-gray-600'}`}>
                    {sale.source === 'WEB' ? <Globe className="w-3 h-3" /> : <Store className="w-3 h-3" />}
                    {sale.source === 'WEB' ? 'Web' : 'Directa'}
                  </span>
                </td>
                <td className="py-2.5">{sale.quantity}</td>
                <td className="py-2.5 text-right font-medium">{sale.amount_eur?.toFixed(2)} EUR</td>
              </tr>
            ))}
          </tbody>
        </table>
        {sales.length === 0 && <p className="text-gray-400 py-4 text-center">No hay ventas registradas</p>}
      </div>
    </div>
  )
}
