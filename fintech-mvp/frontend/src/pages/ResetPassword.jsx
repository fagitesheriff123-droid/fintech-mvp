import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '../api'
import { input, btn, errMsg } from '../ui'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (busy) return
    if (password !== confirm) { setError("Passwords don't match"); return }
    setError(''); setBusy(true)
    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setDone(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }

  return (
    <div className="max-w-sm mx-auto mt-16 px-4">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-xl font-bold mb-1">Set a new password</h1>
        {!token && <p className="text-sm text-red-600 mt-4">This link is missing its token. Request a new one from the <Link className="underline" to="/forgot-password">forgot password</Link> page.</p>}
        {token && done && <p className="text-sm text-emerald-700 mt-4">Password reset — taking you to log in…</p>}
        {token && !done && (
          <form onSubmit={submit} className="space-y-4 mt-4">
            <input className={input} type="password" placeholder="New password (min 8 characters)" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <input className={input} type="password" placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button disabled={busy} className={`w-full ${btn}`}>{busy ? 'Resetting…' : 'Reset password'}</button>
          </form>
        )}
      </div>
    </div>
  )
}
