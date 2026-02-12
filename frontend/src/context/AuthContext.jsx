import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      api.setToken(token)
      setUser({ authenticated: true })
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    await api.login(username, password)
    setUser({ authenticated: true, username })
  }

  const logout = () => {
    api.setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
