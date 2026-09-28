import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { input, btn } from '../ui'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    try { await api.post('/auth/forgot-password', { email }) } catch {}
    // Same message whether or not the email is registered — matches the backend,
    // so this page can't be used to check which emails have accounts.
    setSent(true); setBusy(false)
  }

  return (
    <div className="max-w-sm mx-auto mt-16 px-4">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-xl font-bold mb-1">Reset your password</h1>
        {sent ? (
          <p className="text-sm text-slate-600 mt-4">
            If <b>{email}</b> is registered, a reset link has been sent. It expires in 30 minutes.
          </p>
        ) : (
          <>
            <p className="text-sm text-slate-500 mb-6">Enter your email and we'll send you a reset link.</p>
            <form onSubmit={submit} className="space-y-4">
              <input className={input} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <button disabled={busy} className={`w-full ${btn}`}>{busy ? 'Sending…' : 'Send reset link'}</button>
            </form>
          </>
        )}
        <Link to="/login" className="text-sm text-slate-500 hover:text-slate-800 mt-4 inline-block">Back to log in</Link>
      </div>
    </div>
  )
}
