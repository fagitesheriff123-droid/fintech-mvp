import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('login')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      if (mode === 'signup') {
        await api.post('/auth/signup', { email, password })
      }
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', res.data.access_token)
      onLogin()
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20 bg-white p-8 rounded-xl shadow-sm border">
      <h1 className="text-xl font-semibold mb-6">
        {mode === 'login' ? 'Log in' : 'Create account'}
      </h1>
      <form onSubmit={submit} className="space-y-4">
        <input
          className="w-full border rounded-lg px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button className="w-full bg-gray-900 text-white rounded-lg py-2 font-medium">
          {mode === 'login' ? 'Log in' : 'Sign up'}
        </button>
      </form>
      <button
        className="text-sm text-gray-500 mt-4"
        onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
      >
        {mode === 'login' ? "Need an account? Sign up" : 'Have an account? Log in'}
      </button>
    </div>
  )
}
