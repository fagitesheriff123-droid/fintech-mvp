import { useState } from 'react'
import api from '../api'
import { Card, Stat, Badge, naira, input, btn } from '../ui'

// Phase 5 — opt-in track. Off by default on the backend (ENABLE_EXPERIMENTAL);
// everything here is sandbox data, synthetic data, or scoped to your own uploads.
const SUGGESTIONS = ["What's my biggest spending category?", 'How much did I spend in total?', 'How much did I spend on transport?']

export default function Experimental() {
  const [link, setLink] = useState(null)
  const [trend, setTrend] = useState(null)
  const [q, setQ] = useState('')
  const [answer, setAnswer] = useState(null)
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')

  async function run(kind, fn) {
    if (busy) return
    setBusy(kind); setErr('')
    try { await fn() } catch (e) {
      setErr(e.response?.status === 404
        ? 'Experimental endpoints are switched off on this server (ENABLE_EXPERIMENTAL is false).'
        : e.response?.data?.detail || 'Request failed — the server may be waking up, try again.')
    } finally { setBusy('') }
  }
  const ask = (text) => { setQ(text); run('ask', async () => setAnswer((await api.post('/experimental/ask', { question: text })).data)) }

  return (
    <div className="max-w-4xl mx-auto mt-6 px-4 pb-16 space-y-5">
      <div>
        <div className="flex items-center gap-2"><h1 className="text-2xl font-bold text-slate-900">Experimental</h1><Badge>Phase 5</Badge></div>
        <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mt-3">
          <b>Not real, not advice.</b> Everything here is sandbox data, synthetic data, or limited strictly to your own uploaded
          transactions — never real bank access, live market data, or investment advice.
        </p>
      </div>
      {err && <p className="text-sm text-red-600">{err}</p>}

      <Card title="Sandbox account link" sub="Shows the shape a real Mono/Okra bank-linking response would have — with fabricated data.">
        <button disabled={busy === 'link'} className={btn} onClick={() => run('link', async () => setLink((await api.get('/experimental/sandbox-link')).data))}>
          {busy === 'link' ? 'Linking…' : 'Simulate linking an account'}
        </button>
        {link && (
          <div className="mt-4 space-y-3">
            <p className="text-xs font-medium text-amber-700">{link.mode}</p>
            <div className="grid sm:grid-cols-2 gap-2">
              {link.accounts.map((a, i) => (
                <Stat key={i} label={`${a.institution} · ${a.account_type}`} value={naira(a.balance)} />
              ))}
            </div>
            <p className="text-xs text-slate-500">{link.note}</p>
          </div>
        )}
      </Card>

      <Card title="Market trend module" sub="A toy moving-average signal on a synthetic random walk — it demonstrates labelling, not prediction.">
        <button disabled={busy === 'trend'} className={btn} onClick={() => run('trend', async () => setTrend((await api.get('/experimental/market-trend')).data))}>
          {busy === 'trend' ? 'Running…' : 'Run experimental signal'}
        </button>
        {trend && (
          <div className="mt-4 space-y-2">
            <div className="flex flex-wrap gap-2 items-center">
              <Badge ok={trend.naive_signal.startsWith('up')}>{trend.naive_signal}</Badge>
              <span className="text-xs text-slate-500">{trend.data_source}</span>
            </div>
            <p className="text-xs text-slate-600">{trend.reason}</p>
          </div>
        )}
      </Card>

      <Card title="Ask about your spending" sub="Answers come only from your own uploaded transactions — it can't give market or allocation opinions.">
        <form onSubmit={(e) => { e.preventDefault(); if (q.trim()) ask(q) }} className="flex gap-2">
          <input className={`${input} flex-1`} placeholder="e.g. what's my biggest spending category?" value={q} onChange={(e) => setQ(e.target.value)} />
          <button disabled={busy === 'ask' || !q.trim()} className={btn}>{busy === 'ask' ? '…' : 'Ask'}</button>
        </form>
        <div className="flex flex-wrap gap-2 mt-3">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => ask(s)} className="text-xs border border-slate-300 rounded-full px-3 py-1 text-slate-600 hover:bg-slate-50">{s}</button>
          ))}
        </div>
        {answer && <p className="text-sm bg-emerald-50 border border-emerald-100 text-slate-800 rounded-xl px-4 py-3 mt-4">{answer.answer}</p>}
      </Card>
    </div>
  )
}
