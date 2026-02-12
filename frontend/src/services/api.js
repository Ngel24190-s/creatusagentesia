const API_BASE = '/api/v1'

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token')
  }

  setToken(token) {
    this.token = token
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  }

  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
    if (res.status === 401) {
      this.setToken(null)
      window.location.href = '/login'
      throw new Error('Session expired')
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error de servidor' }))
      throw new Error(err.detail || `Error ${res.status}`)
    }
    if (res.status === 204) return null
    return res.json()
  }

  get(path) { return this.request(path) }
  post(path, data) { return this.request(path, { method: 'POST', body: JSON.stringify(data) }) }
  put(path, data) { return this.request(path, { method: 'PUT', body: JSON.stringify(data) }) }
  delete(path) { return this.request(path, { method: 'DELETE' }) }

  // Auth
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    })
    if (!res.ok) throw new Error('Credenciales incorrectas')
    const data = await res.json()
    this.setToken(data.access_token)
    return data
  }

  // Kitchen
  getMaterials() { return this.get('/kitchen/materials') }
  createMaterial(data) { return this.post('/kitchen/materials', data) }
  getBatches() { return this.get('/kitchen/batches') }
  createBatch(data) { return this.post('/kitchen/batches', data) }
  updateBatchStatus(id, status) { return this.put(`/kitchen/batches/${id}/status?status=${status}`) }

  // Production
  getIBCs() { return this.get('/production/ibcs') }
  createIBC(data) { return this.post('/production/ibcs', data) }
  getFeedings(ibcId) { return this.get(`/production/ibcs/${ibcId}/feedings`) }
  createFeeding(data) { return this.post('/production/feedings', data) }
  getHungryAlerts() { return this.get('/production/alerts/hungry-ibcs') }

  // Laboratory
  getProducts() { return this.get('/laboratory/products') }
  createProduct(data) { return this.post('/laboratory/products', data) }
  getProductQR(productId) { return `${API_BASE}/laboratory/products/${productId}/qr` }
  getTrace(batchCode) { return this.get(`/laboratory/trace/${batchCode}`) }

  // Sales
  getSales() { return this.get('/sales/') }
  createSale(data) { return this.post('/sales/', data) }
  getDashboard() { return this.get('/sales/dashboard') }

  // AI Agents
  getAgentRecommendations() { return this.get('/agents/recommendations') }
  getAgentForecast() { return this.get('/agents/forecast') }
  getAgentHealth() { return this.get('/agents/farm-health') }
  askAgent(question) { return this.post('/agents/ask', { question }) }
}

export const api = new ApiClient()
