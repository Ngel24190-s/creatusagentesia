import { useState, useEffect } from 'react'
import { api } from '../services/api'
import {
  Bot, Brain, TrendingUp, Heart, Send, Loader2,
  AlertTriangle, Lightbulb, BarChart3, Leaf
} from 'lucide-react'

export default function Agents() {
  const [health, setHealth] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [question, setQuestion] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [asking, setAsking] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getAgentHealth().catch(() => null),
      api.getAgentRecommendations().catch(() => null),
      api.getAgentForecast().catch(() => null),
    ]).then(([h, r, f]) => {
      setHealth(h)
      setRecommendations(r)
      setForecast(f)
      setLoading(false)
    })
  }, [])

  const askQuestion = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    setAsking(true)
    const q = question
    setQuestion('')
    setChatHistory(prev => [...prev, { role: 'user', text: q }])
    try {
      const res = await api.askAgent(q)
      setChatHistory(prev => [...prev, { role: 'agent', text: res.answer || res.response || JSON.stringify(res) }])
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'agent', text: `Error: ${err.message}` }])
    }
    setAsking(false)
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">Consultando agentes IA...</div></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot className="w-7 h-7 text-farm-600" /> Agentes IA
        </h1>
        <p className="text-gray-500">Inteligencia artificial para el pilotaje de la granja</p>
      </div>

      {/* Health score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-5 h-5 text-red-500" />
            <h3 className="font-semibold">Salud de la granja</h3>
          </div>
          {health ? (
            <div className="space-y-4">
              <div className="text-center">
                <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full text-2xl font-bold ${
                  health.overall_score >= 80 ? 'bg-green-100 text-green-700' :
                  health.overall_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {health.overall_score}
                </div>
                <p className="text-sm text-gray-500 mt-2">Puntuacion global /100</p>
              </div>
              <div className="space-y-2">
                {health.metrics && Object.entries(health.metrics).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                    <div className="w-24 bg-gray-100 rounded-full h-2">
                      <div className="bg-farm-500 h-2 rounded-full" style={{ width: `${val}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              {health.alerts?.length > 0 && (
                <div className="space-y-2 pt-2 border-t">
                  {health.alerts.map((alert, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                      <span className="text-gray-600">{alert}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : <p className="text-gray-400 text-sm">No hay datos suficientes</p>}
        </div>

        {/* Recommendations */}
        <div className="card lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            <h3 className="font-semibold">Recomendaciones IA</h3>
          </div>
          {recommendations?.items?.length > 0 ? (
            <div className="space-y-3">
              {recommendations.items.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`p-1.5 rounded-lg shrink-0 ${
                    rec.priority === 'high' ? 'bg-red-100' :
                    rec.priority === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
                  }`}>
                    <Leaf className={`w-4 h-4 ${
                      rec.priority === 'high' ? 'text-red-600' :
                      rec.priority === 'medium' ? 'text-yellow-600' : 'text-green-600'
                    }`} />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{rec.title}</p>
                    <p className="text-gray-500 text-xs mt-0.5">{rec.description}</p>
                    {rec.action && <p className="text-farm-600 text-xs font-medium mt-1">{rec.action}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">El agente analizara los datos cuando haya suficiente informacion</p>
          )}
        </div>
      </div>

      {/* Forecast */}
      {forecast && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold">Proyecciones</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {forecast.projections?.map((proj, i) => (
              <div key={i} className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-blue-600 font-medium">{proj.label}</p>
                <p className="text-2xl font-bold text-blue-800 mt-1">{proj.value}</p>
                <p className="text-xs text-blue-500 mt-1">{proj.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat with AI */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold">Pregunta al agente</h3>
        </div>
        <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
          {chatHistory.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-4">
              Pregunta lo que quieras sobre tu granja. Ejemplos:<br />
              "Cuando debo alimentar el IBC-003?"<br />
              "Cuanto puedo producir este mes?"<br />
              "Que lote de precompost tiene mejor receta?"
            </p>
          )}
          {chatHistory.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-farm-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {msg.text}
              </div>
            </div>
          ))}
          {asking && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-xl px-4 py-2.5 text-sm text-gray-400 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Analizando...
              </div>
            </div>
          )}
        </div>
        <form onSubmit={askQuestion} className="flex gap-2">
          <input
            className="input-field flex-1"
            placeholder="Escribe tu pregunta..."
            value={question}
            onChange={e => setQuestion(e.target.value)}
          />
          <button type="submit" disabled={asking} className="btn-primary flex items-center gap-2">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
