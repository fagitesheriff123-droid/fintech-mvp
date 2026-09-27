import { useState } from 'react'
import api from '../api'

// Phase 5 — matches the backend's opt-in gating. This page assumes
// ENABLE_EXPERIMENTAL=true on the backend; if it's off, these calls 404,
// which is the correct behavior for a track that's off by default.
export default function Experimental() {
  const [sandboxLink, setSandboxLink] = useState(null)
  const [trend, setTrend] = useState(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [err, setErr] = useState('')

  async function tryCall(fn) {
    setErr('')
    try {
      await fn()
    } catch {
      setErr('Experimental endpoints are off by default — set ENABLE_EXPERIMENTAL=true on the backend to try these.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto mt-10 px-4 pb-16 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Experimental (Phase 5)</h1>
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-2">
          Off by default. Everything on this page is sandbox data, synthetic
          data, or scoped strictly to your own uploaded transactions — never
          real bank access, market data, or investment advice.
        </p>
      </div>

      {err && <p className="text-sm text-red-500">{err}</p>}

      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-2">Sandbox account link</h2>
        <button
          className="text-sm bg-gray-900 text-white rounded-lg px-4 py-2"
          onClick={() => tryCall(async () => setSandboxLink((await api.get('/experimental/sandbox-link')).data))}
        >
          Simulate linking an account
        </button>
        {sandboxLink && (
          <pre className="text-xs bg-gray-50 rounded-lg p-3 mt-3 overflow-auto">
            {JSON.stringify(sandboxLink, null, 2)}
          </pre>
        )}
      </section>

      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-2">Market trend module (synthetic data)</h2>
        <button
          className="text-sm bg-gray-900 text-white rounded-lg px-4 py-2"
          onClick={() => tryCall(async () => setTrend((await api.get('/experimental/market-trend')).data))}
        >
          Run experimental signal
        </button>
        {trend && <p className="text-sm text-gray-600 mt-3">{trend.reason}</p>}
      </section>

      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-2">Ask about your spending</h2>
        <div className="flex gap-2">
          <input
            className="flex-1 border rounded-lg px-3 py-2 text-sm"
            placeholder="e.g. what's my biggest spending category?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            className="text-sm bg-gray-900 text-white rounded-lg px-4 py-2"
            onClick={() =>
              tryCall(async () =>
                setAnswer((await api.post('/experimental/ask', { question })).data)
              )
            }
          >
            Ask
          </button>
        </div>
        {answer && <p className="text-sm text-gray-600 mt-3">{answer.answer}</p>}
      </section>
    </div>
  )
}
