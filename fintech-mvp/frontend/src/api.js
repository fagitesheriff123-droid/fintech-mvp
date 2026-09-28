import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
// 60s timeout: the free-tier backend can take ~30-60s to wake from idle.
const api = axios.create({ baseURL: API_BASE, timeout: 60000 })

// --- Offline / low-data cache ------------------------------------------
// Every successful GET is saved locally. Offline (or on a failed network call)
// the saved copy is served. In Lite mode, a copy under 10 min old is served
// without touching the network at all. Any write clears the cache.
const P = 'cache:'
const keyOf = (c) => P + c.url + JSON.stringify(c.params || {})
const read = (c) => { try { return JSON.parse(localStorage.getItem(keyOf(c))) } catch { return null } }
export const isLite = () => localStorage.getItem('lite') === '1'
export const clearCache = () =>
  Object.keys(localStorage).filter((k) => k.startsWith(P)).forEach((k) => localStorage.removeItem(k))

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.method === 'get' && isLite()) {
    const hit = read(config)
    if (hit && Date.now() - hit.t < 600000) {
      config._cached = true
      config.adapter = async () => ({ data: hit.d, status: 200, statusText: 'OK', headers: {}, config })
    }
  }
  return config
})

api.interceptors.response.use(
  (res) => {
    if (res.config.method !== 'get') clearCache()
    else if (!res.config._cached) {
      try { localStorage.setItem(keyOf(res.config), JSON.stringify({ t: Date.now(), d: res.data })) } catch {}
    }
    return res
  },
  (err) => {
    const c = err.config
    if (c?.method === 'get' && !err.response) {
      const hit = read(c)
      if (hit) {
        window.dispatchEvent(new Event('served-from-cache'))
        return { data: hit.d, status: 200, statusText: 'OK', headers: {}, config: c }
      }
    }
    if (err.response?.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token'); clearCache(); window.location.hash = '#/login'; window.location.reload()
    }
    return Promise.reject(err)
  }
)

export default api
