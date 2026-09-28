import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('login')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (busy) return // prevents double-submit (this caused duplicate signups)
    setError(''); setBusy(true)
    try {
      if (mode === 'signup') await api.post('/auth/signup', { email, password })
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', res.data.access_token)
      onLogin(); navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || (err.code === 'ECONNABORTED' || !err.response
        ? 'Server is waking up — please try again in a few seconds.' : 'Something went wrong'))
    } finally { setBusy(false) }
  }

  const input = 'w-full border border-slate-300 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500'
  return (
    <div className="max-w-4xl mx-auto mt-10 sm:mt-16 px-4 grid md:grid-cols-2 gap-6 items-stretch">
      <div className="hidden md:flex flex-col justify-center rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white p-8">
        <h2 className="text-2xl font-bold mb-3">Understand your money, in plain language.</h2>
        <ul className="space-y-2 text-emerald-50 text-sm">
          <li>• Upload a CSV or PDF bank statement</li>
          <li>• Forecasts and unusual spending, each with a reason</li>
          <li>• A health score, savings goals and a "what if" simulator</li>
        </ul>
      </div>
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-xl font-bold mb-6">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
        <form onSubmit={submit} className="space-y-4">
          <input className={input} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input className={input} type="password" placeholder="Password (min 8 characters)" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <button disabled={busy} className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white rounded-xl py-2.5 font-semibold">
            {busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Sign up'}
          </button>
        </form>
        <div className="flex justify-between items-center mt-4">
          <button className="text-sm text-slate-500 hover:text-slate-800" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
            {mode === 'login' ? 'Need an account? Sign up' : 'Have an account? Log in'}
          </button>
          {mode === 'login' && <Link to="/forgot-password" className="text-sm text-slate-500 hover:text-slate-800">Forgot password?</Link>}
        </div>
      </div>
    </div>
  )
}
