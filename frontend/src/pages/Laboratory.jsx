import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, QrCode, ExternalLink, Package, Droplets, Mountain } from 'lucide-react'

export default function Laboratory() {
  const [products, setProducts] = useState([])
  const [ibcs, setIbcs] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const [form, setForm] = useState({
    batch_code: '', type: 'LEACHATE', packaging_size: '', sku: '',
    stock_qty: '', source_ibc_id: '', notes: '',
  })

  useEffect(() => {
    Promise.all([
      api.getProducts().catch(() => []),
      api.getIBCs().catch(() => []),
    ]).then(([p, i]) => {
      setProducts(p || [])
      setIbcs(i || [])
      setLoading(false)
    })
  }, [])

  const submitProduct = async (e) => {
    e.preventDefault()
    const data = {
      ...form,
      stock_qty: parseInt(form.stock_qty),
      source_ibc_id: form.source_ibc_id ? parseInt(form.source_ibc_id) : null,
    }
    const result = await api.createProduct(data)
    setProducts([result, ...products])
    setForm({ batch_code: '', type: 'LEACHATE', packaging_size: '', sku: '', stock_qty: '', source_ibc_id: '', notes: '' })
    setShowForm(false)
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Cargando...</div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Laboratorio</h1>
          <p className="text-gray-500">Productos, QR y trazabilidad</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo producto
        </button>
      </div>

      {/* Product form */}
      {showForm && (
        <form onSubmit={submitProduct} className="card space-y-4">
          <h3 className="font-semibold">Registrar producto cosechado</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input className="input-field" placeholder="Codigo lote (ej: PROD-2026-001)" value={form.batch_code} onChange={e => setForm({...form, batch_code: e.target.value})} required />
            <select className="input-field" value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
              <option value="LEACHATE">Lixiviado (liquido)</option>
              <option value="SOLID">Vermicompost (solido)</option>
            </select>
            <input className="input-field" placeholder="Tamano envase (ej: 5L, 20kg)" value={form.packaging_size} onChange={e => setForm({...form, packaging_size: e.target.value})} required />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input className="input-field" placeholder="SKU" value={form.sku} onChange={e => setForm({...form, sku: e.target.value})} />
            <input className="input-field" type="number" placeholder="Stock inicial" value={form.stock_qty} onChange={e => setForm({...form, stock_qty: e.target.value})} required />
            <select className="input-field" value={form.source_ibc_id} onChange={e => setForm({...form, source_ibc_id: e.target.value})}>
              <option value="">IBC de origen (opcional)</option>
              {ibcs.map(ibc => <option key={ibc.id} value={ibc.id}>{ibc.code}</option>)}
            </select>
          </div>
          <input className="input-field" placeholder="Notas" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Crear producto</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* Products grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map(product => (
          <div key={product.id} className="card">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                {product.type === 'LEACHATE'
                  ? <Droplets className="w-5 h-5 text-blue-500" />
                  : <Mountain className="w-5 h-5 text-amber-600" />
                }
                <span className="font-mono font-bold text-sm">{product.batch_code}</span>
              </div>
              <span className={product.type === 'LEACHATE' ? 'badge-blue' : 'badge-yellow'}>
                {product.type === 'LEACHATE' ? 'Lixiviado' : 'Solido'}
              </span>
            </div>
            <div className="space-y-1 text-sm text-gray-600">
              <p><Package className="w-4 h-4 inline mr-1" /> {product.packaging_size} | Stock: <strong>{product.stock_qty}</strong></p>
              {product.sku && <p className="text-gray-400">SKU: {product.sku}</p>}
            </div>
            <div className="flex gap-2 mt-3">
              <a
                href={api.getProductQR(product.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
              >
                <QrCode className="w-4 h-4" /> QR Code
              </a>
              <a
                href={`/trace/${product.batch_code}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1 py-2 bg-farm-100 hover:bg-farm-200 text-farm-700 rounded-lg text-sm font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" /> Trazabilidad
              </a>
            </div>
          </div>
        ))}
        {products.length === 0 && <p className="text-gray-400 col-span-full">No hay productos registrados</p>}
      </div>
    </div>
  )
}
