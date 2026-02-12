import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Kitchen from './pages/Kitchen'
import Production from './pages/Production'
import Laboratory from './pages/Laboratory'
import Sales from './pages/Sales'
import Agents from './pages/Agents'
import Traceability from './pages/Traceability'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen">Cargando...</div>
  if (!user) return <Navigate to="/login" />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/trace/:batchCode" element={<Traceability />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/kitchen" element={<Kitchen />} />
                <Route path="/production" element={<Production />} />
                <Route path="/laboratory" element={<Laboratory />} />
                <Route path="/sales" element={<Sales />} />
                <Route path="/agents" element={<Agents />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
