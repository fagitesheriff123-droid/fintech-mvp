import { useEffect, useRef, useState } from 'react'
import api from '../api'
import { Card, Stat, Badge, naira, input, btn, errMsg } from '../ui'

const emptyGoal = { name: '', target_amount: '', target_date: '' }
const emptyDebt = { name: '', balance: '', interest_rate: '', min_payment: '' }

export default function Planning() {
  const [extra, setExtra] = useState(0)
  const [sim, setSim] = useState(null)
  const [simErr, setSimErr] = useState('')
  const timer = useRef(); const seq = useRef(0)

  const [goals, setGoals] = useState([]); const [proj, setProj] = useState({}); const [gf, setGf] = useState(emptyGoal)
  const [debts, setDebts] = useState([]); const [df, setDf] = useState(emptyDebt)
  const [strategy, setStrategy] = useState('avalanche'); const [order, setOrder] = useState(null)
  const [busy, setBusy] = useState(''); const [err, setErr] = useState('')

  // Debounced so dragging the slider doesn't fire a request per pixel.
  function runSim(val, delay = 300) {
    setExtra(val); clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      const n = ++seq.current
      try {
        const r = await api.get('/planning/simulate', { params: { extra_savings: val } })
        if (n === seq.current) { setSim(r.data); setSimErr('') }
      } catch (e) { if (n === seq.current) setSimErr(errMsg(e, 'Upload a statement first so the simulator has your numbers to work from.')) }
    }, delay)
  }

  async function loadGoals() {
    const list = (await api.get('/planning/goals')).data
    setGoals(list)
    const pairs = await Promise.all(list.map((g) => api.get(`/planning/goals/${g.id}/projection`).then((r) => [g.id, r.data]).catch(() => [g.id, null])))
    setProj(Object.fromEntries(pairs))
  }
  async function loadOrder(s) {
    setStrategy(s)
    setOrder((await api.get('/planning/debts/payoff-order', { params: { strategy: s } })).data)
  }
  async function loadDebts(s = strategy) {
    const list = (await api.get('/planning/debts')).data
    setDebts(list)
    if (list.length) await loadOrder(s); else setOrder(null)
  }

  useEffect(() => {
    runSim(0, 0)
    loadGoals().catch(() => {}); loadDebts().catch(() => {})
  }, [])

  async function submit(e, kind) {
    e.preventDefault()
    if (busy) return
    setBusy(kind); setErr('')
    try {
      if (kind === 'goal') {
        await api.post('/planning/goals', { name: gf.name, target_amount: parseFloat(gf.target_amount), target_date: gf.target_date })
        setGf(emptyGoal); await loadGoals()
      } else {
        await api.post('/planning/debts', { name: df.name, balance: parseFloat(df.balance), interest_rate: parseFloat(df.interest_rate), min_payment: parseFloat(df.min_payment) })
        setDf(emptyDebt); await loadDebts()
      }
    } catch (e2) { setErr(errMsg(e2)) } finally { setBusy('') }
  }

  const set = (setter, obj, k) => (e) => setter({ ...obj, [k]: e.target.value })

  return (
    <div className="max-w-4xl mx-auto mt-6 px-4 pb-16 space-y-5">
      <h1 className="text-2xl font-bold text-slate-900">Planning</h1>
      {err && <p className="text-sm text-red-600">{err}</p>}

      <Card title="Scenario simulator" sub="What if you saved more each month? Uses your own uploaded income and spending.">
        <input type="range" min="0" max="200000" step="5000" value={extra} onChange={(e) => runSim(Number(e.target.value))} className="w-full accent-emerald-600" />
        <p className="text-sm mt-1 mb-3">Extra savings: <b>{naira(extra)}</b> / month</p>
        {simErr && <p className="text-sm text-amber-700">{simErr}</p>}
        {sim && !simErr && (
          <>
            <div className="grid grid-cols-3 gap-2">
              <Stat label="Saving now" value={naira(sim.current_avg_monthly_savings)} />
              <Stat label="With change" value={naira(sim.projected_monthly_savings)} tone="text-emerald-600" />
              <Stat label="Spend would be" value={naira(sim.implied_monthly_spend)} />
            </div>
            <p className="text-xs text-slate-500 mt-3">{sim.reason}</p>
          </>
        )}
      </Card>

      <Card title="Savings goals" sub="Set a target and date — we work backwards to what you'd need to save monthly.">
        <form onSubmit={(e) => submit(e, 'goal')} className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
          <input className={input} placeholder="Goal name" value={gf.name} onChange={set(setGf, gf, 'name')} required />
          <input className={input} placeholder="Target amount (₦)" type="number" min="1" value={gf.target_amount} onChange={set(setGf, gf, 'target_amount')} required />
          <input className={input} type="date" value={gf.target_date} onChange={set(setGf, gf, 'target_date')} required />
          <button disabled={busy === 'goal'} className={`${btn} sm:col-span-3`}>{busy === 'goal' ? 'Adding…' : 'Add goal'}</button>
        </form>
        {goals.length === 0 && <p className="text-sm text-slate-400">No goals yet.</p>}
        <div className="space-y-4">
          {goals.map((g) => {
            const p = proj[g.id]
            const pct = p ? Math.max(0, Math.min(100, (p.current_avg_monthly_savings / p.required_monthly_savings) * 100)) : 0
            return (
              <div key={g.id} className="border-t border-slate-100 pt-3">
                <div className="flex justify-between items-center gap-2 text-sm">
                  <span className="font-medium">{g.name}</span>
                  {p && <Badge ok={p.feasible}>{p.feasible ? 'On track' : 'Behind'}</Badge>}
                </div>
                <p className="text-xs text-slate-500">{naira(g.target_amount)} by {g.target_date}</p>
                {p && (
                  <>
                    <div className="h-1.5 bg-slate-100 rounded-full mt-2"><div className={`h-1.5 rounded-full ${p.feasible ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${pct}%` }} /></div>
                    <p className="text-xs text-slate-600 mt-2">{p.reason}</p>
                  </>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      <Card title="Debt payoff helper" sub="Enter your debts and compare the two classic strategies. This is arithmetic, not financial advice.">
        <form onSubmit={(e) => submit(e, 'debt')} className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          <input className={`${input} col-span-2 sm:col-span-1`} placeholder="Debt name" value={df.name} onChange={set(setDf, df, 'name')} required />
          <input className={input} placeholder="Balance (₦)" type="number" min="1" value={df.balance} onChange={set(setDf, df, 'balance')} required />
          <input className={input} placeholder="Interest %" type="number" min="0" step="0.01" value={df.interest_rate} onChange={set(setDf, df, 'interest_rate')} required />
          <input className={input} placeholder="Min payment" type="number" min="0" value={df.min_payment} onChange={set(setDf, df, 'min_payment')} required />
          <button disabled={busy === 'debt'} className={`${btn} col-span-2 sm:col-span-4`}>{busy === 'debt' ? 'Adding…' : 'Add debt'}</button>
        </form>
        {debts.length === 0 && <p className="text-sm text-slate-400">No debts added.</p>}
        {order && (
          <>
            <div className="inline-flex rounded-full border border-slate-300 overflow-hidden text-xs mb-3">
              {['avalanche', 'snowball'].map((s) => (
                <button key={s} onClick={() => loadOrder(s)} className={`px-4 py-1.5 capitalize ${strategy === s ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}>{s}</button>
              ))}
            </div>
            <p className="text-xs text-slate-500 mb-3">{order.reason}</p>
            <ol className="space-y-2">
              {order.details.map((d, i) => (
                <li key={d.name + i} className="flex items-center gap-3 bg-slate-50 rounded-xl px-3 py-2">
                  <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs grid place-items-center shrink-0">{i + 1}</span>
                  <span className="flex-1 text-sm font-medium">{d.name}</span>
                  <span className="text-xs text-slate-500 text-right">{naira(d.balance)} · {d.interest_rate}%</span>
                </li>
              ))}
            </ol>
            <p className="text-xs text-slate-500 mt-3">Estimated interest per year if untouched: <b>{naira(order.estimated_annual_interest_if_untouched)}</b></p>
          </>
        )}
      </Card>
    </div>
  )
}
