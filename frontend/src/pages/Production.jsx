import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, AlertTriangle, Utensils, MapPin, Bug } from 'lucide-react'

export default function Production() {
  const [ibcs, setIbcs] = useState([])
  const [alerts, setAlerts] = useState([])
  const [batches, setBatches] = useState([])
  const [showIBCForm, setShowIBCForm] = useState(false)
  const [feedingIBC, setFeedingIBC] = useState(null)
  const [loading, setLoading] = useState(true)

  const [ibcForm, setIbcForm] = useState({ code: '', location: '', worm_biomass_kg: '' })
  const [feedForm, setFeedForm] = useState({ batch_id: '', quantity_kg: '' })

  useEffect(() => {
    Promise.all([
      api.getIBCs().catch(() => []),
      api.getHungryAlerts().catch(() => []),
      api.getBatches().catch(() => []),
    ]).then(([i, a, b]) => {
      setIbcs(i || [])
      setAlerts(a || [])
      setBatches((b || []).filter(x => x.status === 'READY'))
      setLoading(false)
    })
  }, [])

  const alertCodes = new Set(alerts.map(a => a.code || a.ibc_code))

  const submitIBC = async (e) => {
    e.preventDefault()
    const result = await api.createIBC({ ...ibcForm, worm_biomass_kg: parseFloat(ibcForm.worm_biomass_kg) })
    setIbcs([result, ...ibcs])
    setIbcForm({ code: '', location: '', worm_biomass_kg: '' })
    setShowIBCForm(false)
  }

  const submitFeeding = async (e) => {
    e.preventDefault()
    await api.createFeeding({
      ibc_id: feedingIBC.id,
      batch_id: parseInt(feedForm.batch_id),
      quantity_kg: parseFloat(feedForm.quantity_kg),
    })
    setAlerts(alerts.filter(a => (a.code || a.ibc_code) !== feedingIBC.code))
    setFeedForm({ batch_id: '', quantity_kg: '' })
    setFeedingIBC(null)
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Cargando...</div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Produccion</h1>
          <p className="text-gray-500">IBCs y alimentacion de lombrices</p>
        </div>
        <button onClick={() => setShowIBCForm(!showIBCForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo IBC
        </button>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="font-semibold text-red-800">IBCs hambrientos</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {alerts.map((alert, i) => (
              <div key={i} className="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-red-100">
                <span className="font-mono text-sm font-bold text-red-700">{alert.code || alert.ibc_code}</span>
                <span className="text-xs text-red-500">
                  Ultima comida: {alert.last_fed ? new Date(alert.last_fed).toLocaleDateString('es') : 'Nunca'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* IBC Form */}
      {showIBCForm && (
        <form onSubmit={submitIBC} className="card space-y-4">
          <h3 className="font-semibold">Nuevo IBC</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input className="input-field" placeholder="Codigo (ej: IBC-001)" value={ibcForm.code} onChange={e => setIbcForm({...ibcForm, code: e.target.value})} required />
            <input className="input-field" placeholder="Ubicacion" value={ibcForm.location} onChange={e => setIbcForm({...ibcForm, location: e.target.value})} required />
            <input className="input-field" type="number" step="0.1" placeholder="Biomasa lombrices (kg)" value={ibcForm.worm_biomass_kg} onChange={e => setIbcForm({...ibcForm, worm_biomass_kg: e.target.value})} required />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Crear IBC</button>
            <button type="button" onClick={() => setShowIBCForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* Feeding modal */}
      {feedingIBC && (
        <form onSubmit={submitFeeding} className="card border-2 border-farm-300 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Utensils className="w-5 h-5" /> Alimentar {feedingIBC.code}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select className="input-field" value={feedForm.batch_id} onChange={e => setFeedForm({...feedForm, batch_id: e.target.value})} required>
              <option value="">Seleccionar lote de precompost...</option>
              {batches.map(b => (
                <option key={b.id} value={b.id}>{b.code}</option>
              ))}
            </select>
            <input className="input-field" type="number" step="0.1" placeholder="Cantidad (kg)" value={feedForm.quantity_kg} onChange={e => setFeedForm({...feedForm, quantity_kg: e.target.value})} required />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Registrar comida</button>
            <button type="button" onClick={() => setFeedingIBC(null)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {/* IBCs grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ibcs.map(ibc => {
          const isHungry = alertCodes.has(ibc.code)
          return (
            <div key={ibc.id} className={`card ${isHungry ? 'border-2 border-red-300 bg-red-50/30' : ''}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono font-bold">{ibc.code}</span>
                {isHungry && <span className="badge-red">Hambriento</span>}
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <p className="flex items-center gap-2"><MapPin className="w-4 h-4" /> {ibc.location}</p>
                <p className="flex items-center gap-2"><Bug className="w-4 h-4" /> {ibc.worm_biomass_kg} kg biomasa</p>
              </div>
              <button
                onClick={() => setFeedingIBC(ibc)}
                className={`mt-3 w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                  isHungry
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-farm-100 text-farm-700 hover:bg-farm-200'
                }`}
              >
                <Utensils className="w-4 h-4 inline mr-1" /> Alimentar
              </button>
            </div>
          )
        })}
        {ibcs.length === 0 && <p className="text-gray-400 col-span-full">No hay IBCs registrados</p>}
      </div>
    </div>
  )
}
