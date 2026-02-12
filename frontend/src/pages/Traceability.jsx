import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import { Sprout, Package, Factory, FlaskConical, CheckCircle, Leaf } from 'lucide-react'

export default function Traceability() {
  const { batchCode } = useParams()
  const [trace, setTrace] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getTrace(batchCode)
      .then(setTrace)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [batchCode])

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-b from-farm-50 to-white flex items-center justify-center">
      <div className="animate-pulse text-farm-600">Cargando trazabilidad...</div>
    </div>
  )

  if (error) return (
    <div className="min-h-screen bg-gradient-to-b from-farm-50 to-white flex items-center justify-center">
      <div className="card max-w-md text-center">
        <p className="text-red-500 mb-2">Producto no encontrado</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-b from-farm-50 to-white">
      <div className="max-w-2xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-farm-100 rounded-full mb-4">
            <Sprout className="w-8 h-8 text-farm-600" />
          </div>
          <h1 className="text-2xl font-bold text-farm-800">NosVers</h1>
          <p className="text-gray-500">Trazabilidad del producto</p>
          <p className="font-mono text-lg font-bold mt-2 text-farm-700">{batchCode}</p>
        </div>

        {/* Timeline */}
        <div className="space-y-0">
          {/* Product info */}
          <TimelineItem
            icon={<Package className="w-5 h-5" />}
            color="bg-blue-500"
            title="Producto final"
          >
            <p>Tipo: <strong>{trace.product?.type === 'LEACHATE' ? 'Lixiviado' : 'Vermicompost solido'}</strong></p>
            <p>Envase: {trace.product?.packaging_size}</p>
            {trace.product?.harvest_date && <p>Cosecha: {new Date(trace.product.harvest_date).toLocaleDateString('es')}</p>}
          </TimelineItem>

          {/* IBC source */}
          {trace.source_ibc && (
            <TimelineItem
              icon={<Factory className="w-5 h-5" />}
              color="bg-purple-500"
              title={`IBC: ${trace.source_ibc.code}`}
            >
              <p>Ubicacion: {trace.source_ibc.location}</p>
              <p>Biomasa lombrices: {trace.source_ibc.worm_biomass_kg} kg</p>
              <p>Inicio: {new Date(trace.source_ibc.start_date).toLocaleDateString('es')}</p>
            </TimelineItem>
          )}

          {/* Feedings */}
          {trace.feedings?.map((feeding, i) => (
            <TimelineItem
              key={i}
              icon={<Leaf className="w-5 h-5" />}
              color="bg-farm-500"
              title={`Alimentacion: ${feeding.batch?.code || 'Lote ' + feeding.batch_id}`}
            >
              <p>Cantidad: {feeding.quantity_kg} kg</p>
              <p>Fecha: {new Date(feeding.timestamp).toLocaleDateString('es')}</p>
              {feeding.batch?.recipe_details && (
                <div className="mt-1 bg-farm-50 rounded p-2 text-xs">
                  <p className="font-medium text-farm-700">Receta del precompost:</p>
                  <p>{typeof feeding.batch.recipe_details === 'string'
                    ? feeding.batch.recipe_details
                    : JSON.stringify(feeding.batch.recipe_details, null, 2)
                  }</p>
                </div>
              )}
            </TimelineItem>
          ))}

          {/* Certification */}
          <TimelineItem
            icon={<CheckCircle className="w-5 h-5" />}
            color="bg-green-500"
            title="Producto verificado"
            isLast
          >
            <p>Trazabilidad completa desde materia prima hasta producto final.</p>
            <p className="text-farm-600 font-medium mt-1">Lombricompostaje regenerativo - Neuvic, France</p>
          </TimelineItem>
        </div>

        <div className="text-center mt-8 text-gray-400 text-sm">
          nosvers.com
        </div>
      </div>
    </div>
  )
}

function TimelineItem({ icon, color, title, children, isLast }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`${color} text-white p-2 rounded-full`}>{icon}</div>
        {!isLast && <div className="w-0.5 bg-gray-200 flex-1 my-1" />}
      </div>
      <div className="pb-6 flex-1">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <div className="text-sm text-gray-600 mt-1 space-y-0.5">{children}</div>
      </div>
    </div>
  )
}
