import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import api, { isLite } from '../api'

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6', '#ec4899', '#64748b']
const naira = (n) => '₦' + Math.round(n).toLocaleString()

const Card = ({ title, children, className = '' }) => (
  <section className={`bg-white rounded-2xl border border-slate-200 shadow-sm p-5 ${className}`}>
    {title && <h2 className="text-sm font-semibold text-slate-700 mb-3">{title}</h2>}
    {children}
  </section>
)

function Ring({ score }) {
  const c = 2 * Math.PI * 42
  const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <svg width="110" height="110" viewBox="0 0 100 100" className="shrink-0">
      <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="9" />
      <circle cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="9" strokeLinecap="round"
        strokeDasharray={`${(score / 100) * c} ${c}`} transform="rotate(-90 50 50)" />
      <text x="50" y="57" textAnchor="middle" fontSize="26" fontWeight="700" fill="#0f172a">{score}</text>
    </svg>
  )
}

export default function Dashboard() {
  const [txns, setTxns] = useState([])
  const [forecast, setForecast] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAll, setShowAll] = useState(false)
  const lite = isLite()

  useEffect(() => {
    Promise.allSettled([
      api.get('/transactions/'), api.get('/analytics/forecast'),
      api.get('/analytics/anomalies'), api.get('/analytics/health-score'),
    ]).then(([t, f, a, h]) => {
      if (t.status === 'fulfilled') setTxns(t.value.data)
      else setError('Could not reach the server. It may be waking up — refresh in a moment.')
      if (f.status === 'fulfilled') setForecast(f.value.data)
      if (a.status === 'fulfilled') setAnomalies(a.value.data)
      if (h.status === 'fulfilled') setHealth(h.value.data)
      setLoading(false)
    })
  }, [])

  const income = txns.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0)
  const spend = txns.filter((t) => t.amount < 0).reduce((s, t) => s - t.amount, 0)
  const byCategory = Object.values(
    txns.filter((t) => t.amount < 0).reduce((acc, t) => {
      acc[t.category] = acc[t.category] || { name: t.category, value: 0 }
      acc[t.category].value += Math.abs(t.amount)
      return acc
    }, {})
  ).sort((a, b) => b.value - a.value)
  const maxForecast = Math.max(1, ...forecast.map((f) => f.predicted_amount))
  const rows = showAll || !lite ? txns : txns.slice(0, 15)

  return (
    <div className="max-w-5xl mx-auto mt-6 px-4 pb-16">
      <div className="flex justify-between items-center mb-5">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <Link to="/upload" className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl px-4 py-2">
          + Upload statement
        </Link>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {loading && <p className="text-slate-500 text-sm">Loading your data… (the server can take up to a minute to wake up)</p>}

      {!loading && txns.length === 0 && !error && (
        <Card className="text-center py-12">
          <p className="text-slate-600 mb-4">No transactions yet. Upload a CSV or PDF statement to see your insights.</p>
          <Link to="/upload" className="inline-block bg-emerald-600 text-white text-sm font-semibold rounded-xl px-5 py-2">Upload statement</Link>
        </Card>
      )}

      {txns.length > 0 && (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-3">
            {[['Income', income, 'text-emerald-600'], ['Spending', spend, 'text-rose-600'], ['Net saved', income - spend, income - spend >= 0 ? 'text-slate-900' : 'text-rose-600']].map(([l, v, c]) => (
              <Card key={l} className="!p-4">
                <p className="text-xs text-slate-500">{l}</p>
                <p className={`text-base sm:text-xl font-bold mt-1 ${c}`}>{naira(v)}</p>
              </Card>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-5">
            {health?.score != null && (
              <Card title="Financial health score">
                <div className="flex items-center gap-4">
                  <Ring score={health.score} />
                  <p className="text-sm text-slate-600">{health.reason}</p>
                </div>
              </Card>
            )}
            {!lite && byCategory.length > 0 && (
              <Card title="Where your money goes">
                <div className="flex items-center gap-4">
                  <div style={{ width: 130, height: 130 }}>
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie data={byCategory} dataKey="value" innerRadius={38} outerRadius={62} paddingAngle={2}>
                          {byCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(v) => naira(v)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <ul className="text-xs space-y-1 flex-1">
                    {byCategory.map((c, i) => (
                      <li key={c.name} className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                        <span className="capitalize flex-1">{c.name}</span><span className="text-slate-500">{naira(c.value)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </Card>
            )}
          </div>

          {forecast.length > 0 && (
            <Card title="Predicted spending next month">
              <div className="space-y-3">
                {forecast.map((f) => (
                  <div key={f.category}>
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium">{f.category}</span><span>{naira(f.predicted_amount)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full mt-1"><div className="h-1.5 bg-emerald-500 rounded-full" style={{ width: `${(f.predicted_amount / maxForecast) * 100}%` }} /></div>
                    <p className="text-xs text-slate-500 mt-1">{f.reason}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {anomalies.length > 0 && (
            <Card title="Unusual transactions" className="!bg-amber-50 !border-amber-200">
              <div className="space-y-3">
                {anomalies.map((a) => (
                  <div key={a.transaction_id} className="text-sm">
                    <div className="flex justify-between"><span>{a.description}</span><span className="font-medium">{naira(Math.abs(a.amount))}</span></div>
                    <p className="text-amber-800 text-xs">{a.reason}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card title="Transactions" className="!p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-slate-500 text-xs uppercase">
                  <tr><th className="px-4 py-2">Date</th><th className="px-4 py-2">Description</th><th className="px-4 py-2">Category</th><th className="px-4 py-2 text-right">Amount</th></tr>
                </thead>
                <tbody>
                  {rows.map((t) => (
                    <tr key={t.id} className="border-t border-slate-100">
                      <td className="px-4 py-2 whitespace-nowrap">{t.date}</td>
                      <td className="px-4 py-2">{t.description}</td>
                      <td className="px-4 py-2 capitalize text-slate-500">{t.category}</td>
                      <td className={`px-4 py-2 text-right whitespace-nowrap font-medium ${t.amount >= 0 ? 'text-emerald-600' : 'text-slate-800'}`}>{t.amount >= 0 ? '+' : '−'}{naira(Math.abs(t.amount))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {lite && txns.length > 15 && !showAll && (
              <button onClick={() => setShowAll(true)} className="w-full text-sm text-emerald-700 py-3 border-t">Show all {txns.length} transactions</button>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
