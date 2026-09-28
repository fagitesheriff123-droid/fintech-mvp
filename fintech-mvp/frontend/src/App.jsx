import { useEffect, useState } from 'react'
import { HashRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Upload from './pages/Upload.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Planning from './pages/Planning.jsx'
import Experimental from './pages/Experimental.jsx'
import { clearCache } from './api'

const link = ({ isActive }) =>
  `px-3 py-1.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'}`

export default function App() {
  const [, force] = useState(0)
  const [lite, setLite] = useState(localStorage.getItem('lite') === '1')
  const [offline, setOffline] = useState(!navigator.onLine)
  const authed = !!localStorage.getItem('token')

  useEffect(() => {
    const off = () => setOffline(true)
    const on = () => setOffline(false)
    window.addEventListener('offline', off); window.addEventListener('online', on)
    window.addEventListener('served-from-cache', off)
    return () => { window.removeEventListener('offline', off); window.removeEventListener('online', on); window.removeEventListener('served-from-cache', off) }
  }, [])

  const toggleLite = () => {
    const next = !lite
    localStorage.setItem('lite', next ? '1' : '0'); setLite(next); window.location.reload()
  }
  const logout = () => { localStorage.removeItem('token'); clearCache(); window.location.hash = '#/login'; window.location.reload() }
  const guard = (el) => (authed ? el : <Navigate to="/login" />)

  return (
    <HashRouter>
      <div className="min-h-screen bg-slate-50 text-slate-800">
        <nav className="bg-white/90 backdrop-blur border-b border-slate-200 px-4 sm:px-6 py-3 flex flex-wrap gap-y-2 justify-between items-center sticky top-0 z-10">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="flex items-center gap-2 font-bold text-slate-900">
              <span className="w-7 h-7 rounded-lg bg-emerald-600 grid place-items-center text-white text-sm">₦</span>
              Finance Platform
            </span>
            {authed && (
              <div className="flex gap-1">
                <NavLink to="/" end className={link}>Dashboard</NavLink>
                <NavLink to="/planning" className={link}>Planning</NavLink>
                <NavLink to="/experimental" className={link}>Experimental</NavLink>
              </div>
            )}
          </div>
          {authed && (
            <div className="flex items-center gap-3">
              <button onClick={toggleLite} title="Serves saved data for 10 min and hides charts, to save mobile data"
                className={`text-xs px-2.5 py-1 rounded-full border ${lite ? 'bg-emerald-600 text-white border-emerald-600' : 'text-slate-600 border-slate-300'}`}>
                {lite ? 'Lite mode: on' : 'Lite mode'}
              </button>
              <button className="text-sm text-slate-500 hover:text-slate-900" onClick={logout}>Log out</button>
            </div>
          )}
        </nav>
        {offline && (
          <div className="bg-amber-50 border-b border-amber-200 text-amber-800 text-sm text-center py-1.5 px-3">
            You're offline or the server is unreachable — showing your last saved data.
          </div>
        )}
        <Routes>
          <Route path="/login" element={<Login onLogin={() => force((n) => n + 1)} />} />
          <Route path="/upload" element={guard(<Upload />)} />
          <Route path="/planning" element={guard(<Planning />)} />
          <Route path="/experimental" element={guard(<Experimental />)} />
          <Route path="/" element={guard(<Dashboard />)} />
        </Routes>
      </div>
    </HashRouter>
  )
}
