import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Package, FlaskConical, Clock, CheckCircle, XCircle } from 'lucide-react'

const STATUS_BADGES = {
  FERMENTING: { label: 'Fermentando', class: 'badge-yellow' },
  READY: { label: 'Listo', class: 'badge-green' },
  DEPLETED: { label: 'Agotado', class: 'badge-red' },
}

export default function Kitchen() {
  const [materials, setMaterials] = useState([])
  const [batches, setBatches] = useState([])
  const [showMaterialForm, setShowMaterialForm] = useState(false)
  const [showBatchForm, setShowBatchForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const [materialForm, setMaterialForm] = useState({ type: '', origin: '', quantity_kg: '', notes: '' })
  const [batchForm, setBatchForm] = useState({ code: '', recipe_details: '', notes: '' })

  useEffect(() => {
    Promise.all([
      api.getMaterials().catch(() => []),
      api.getBatches().catch(() => []),
    ]).then(([m, b]) => {
      setMaterials(m || [])
      setBatches(b || [])
      setLoading(false)
    })
  }, [])

  const submitMaterial = async (e) => {
    e.preventDefault()
    const data = { ...materialForm, quantity_kg: parseFloat(materialForm.quantity_kg) }
    const result = await api.createMaterial(data)
    setMaterials([result, ...materials])
    setMaterialForm({ type: '', origin: '', quantity_kg: '', notes: '' })
    setShowMaterialForm(false)
  }

  const submitBatch = async (e) => {
    e.preventDefault()
    let recipe = {}
    try { recipe = JSON.parse(batchForm.recipe_details || '{}') } catch { recipe = { description: batchForm.recipe_details } }
    const result = await api.createBatch({ code: batchForm.code, recipe_details: recipe, notes: batchForm.notes })
    setBatches([result, ...batches])
    setBatchForm({ code: '', recipe_details: '', notes: '' })
    setShowBatchForm(false)
  }

  const updateStatus = async (id, status) => {
    await api.updateBatchStatus(id, status)
    setBatches(batches.map(b => b.id === id ? { ...b, status } : b))
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Cargando...</div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Cocina</h1>
          <p className="text-gray-500">Materias primas y precompost</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowMaterialForm(!showMaterialForm)} className="btn-secondary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Materia prima
          </button>
          <button onClick={() => setShowBatchForm(!showBatchForm)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Lote precompost
          </button>
        </div>
      </div>

      {/* Material form */}
      {showMaterialForm && (
        <form onSubmit={submitMaterial} className="card space-y-4">
          <h3 className="font-semibold flex items-center gap-2"><Package className="w-5 h-5" /> Nueva materia prima</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input className="input-field" placeholder="Tipo (ej: estiercol caballo)" value={materialForm.type} onChange={e => setMaterialForm({...materialForm, type: e.target.value})} required />
            <input className="input-field" placeholder="Origen" value={materialForm.origin} onChange={e => setMaterialForm({...materialForm, origin: e.target.value})} required />
            <input className="input-field" type="number" step="0.1" placeholder="Cantidad (kg)" value={materialForm.quantity_kg} onChange={e => setMaterialForm({...materialForm, quantity_kg: e.target.value})} required />
          </div>
          <input className="input-field" placeholder="Notas (opcional)" value={materialForm.notes} onChange={e => setMaterialForm({...materialForm, notes: e.target.value})} />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Guardar</button>
            <button type="button" onClick={() => setShowMaterialForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* Batch form */}
      {showBatchForm && (
        <form onSubmit={submitBatch} className="card space-y-4">
          <h3 className="font-semibold flex items-center gap-2"><FlaskConical className="w-5 h-5" /> Nuevo lote de precompost</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input-field" placeholder="Codigo del lote (ej: PRE-2026-001)" value={batchForm.code} onChange={e => setBatchForm({...batchForm, code: e.target.value})} required />
            <input className="input-field" placeholder="Notas" value={batchForm.notes} onChange={e => setBatchForm({...batchForm, notes: e.target.value})} />
          </div>
          <textarea className="input-field" rows={3} placeholder="Receta (descripcion o JSON)" value={batchForm.recipe_details} onChange={e => setBatchForm({...batchForm, recipe_details: e.target.value})} />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Crear lote</button>
            <button type="button" onClick={() => setShowBatchForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* Batches */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Lotes de precompost ({batches.length})</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {batches.map(batch => {
            const badge = STATUS_BADGES[batch.status] || STATUS_BADGES.FERMENTING
            const maturityDate = batch.maturity_date ? new Date(batch.maturity_date).toLocaleDateString('es') : '—'
            return (
              <div key={batch.id} className="card">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono font-bold text-sm">{batch.code}</span>
                  <span className={badge.class}>{badge.label}</span>
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <p className="flex items-center gap-2"><Clock className="w-4 h-4" /> Madurez: {maturityDate}</p>
                  {batch.notes && <p className="text-gray-400">{batch.notes}</p>}
                </div>
                {batch.status === 'FERMENTING' && (
                  <button onClick={() => updateStatus(batch.id, 'READY')} className="mt-3 text-sm text-farm-600 hover:text-farm-700 font-medium flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" /> Marcar como listo
                  </button>
                )}
                {batch.status === 'READY' && (
                  <button onClick={() => updateStatus(batch.id, 'DEPLETED')} className="mt-3 text-sm text-red-600 hover:text-red-700 font-medium flex items-center gap-1">
                    <XCircle className="w-4 h-4" /> Marcar agotado
                  </button>
                )}
              </div>
            )
          })}
          {batches.length === 0 && <p className="text-gray-400 col-span-full">No hay lotes de precompost aun</p>}
        </div>
      </div>

      {/* Materials */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Materias primas ({materials.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 font-medium">Tipo</th>
                <th className="pb-2 font-medium">Origen</th>
                <th className="pb-2 font-medium">Cantidad</th>
                <th className="pb-2 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {materials.map(m => (
                <tr key={m.id} className="border-b border-gray-50">
                  <td className="py-2 font-medium">{m.type}</td>
                  <td className="py-2 text-gray-600">{m.origin}</td>
                  <td className="py-2">{m.quantity_kg} kg</td>
                  <td className="py-2 text-gray-400">{new Date(m.date_received || m.created_at).toLocaleDateString('es')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {materials.length === 0 && <p className="text-gray-400 py-4 text-center">No hay materias primas registradas</p>}
        </div>
      </div>
    </div>
  )
}
