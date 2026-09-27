import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Upload from './pages/Upload.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Planning from './pages/Planning.jsx'
import Experimental from './pages/Experimental.jsx'

function useIsAuthed() {
  return !!localStorage.getItem('token')
}

export default function App() {
  const [, force] = useState(0)
  const authed = useIsAuthed()

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-lg">Finance Platform v1</span>
            {authed && (
              <div className="flex gap-4 text-sm">
                <a href="/" className="text-gray-600 hover:text-gray-900">Dashboard</a>
                <a href="/planning" className="text-gray-600 hover:text-gray-900">Planning</a>
                <a href="/experimental" className="text-amber-700 hover:text-amber-900">Experimental</a>
              </div>
            )}
          </div>
          {authed && (
            <button
              className="text-sm text-gray-500 hover:text-gray-800"
              onClick={() => {
                localStorage.removeItem('token')
                force((n) => n + 1)
                window.location.href = '/login'
              }}
            >
              Log out
            </button>
          )}
        </nav>
        <Routes>
          <Route path="/login" element={<Login onLogin={() => force((n) => n + 1)} />} />
          <Route
            path="/upload"
            element={authed ? <Upload /> : <Navigate to="/login" />}
          />
          <Route
            path="/planning"
            element={authed ? <Planning /> : <Navigate to="/login" />}
          />
          <Route
            path="/experimental"
            element={authed ? <Experimental /> : <Navigate to="/login" />}
          />
          <Route
            path="/"
            element={authed ? <Dashboard /> : <Navigate to="/login" />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
