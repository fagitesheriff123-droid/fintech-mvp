import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../api'

export default function Dashboard() {
  const [txns, setTxns] = useState([])
  const [forecast, setForecast] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [healthScore, setHealthScore] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/transactions/').then((res) => setTxns(res.data)).catch(() => {})
    api.get('/analytics/forecast').then((res) => setForecast(res.data)).catch(() => {})
    api.get('/analytics/anomalies').then((res) => setAnomalies(res.data)).catch(() => {})
    api
      .get('/analytics/health-score')
      .then((res) => setHealthScore(res.data))
      .catch((err) => setError(err.response?.data?.detail || ''))
  }, [])

  const byCategory = Object.values(
    txns.reduce((acc, t) => {
      acc[t.category] = acc[t.category] || { category: t.category, total: 0 }
      acc[t.category].total += Math.abs(t.amount)
      return acc
    }, {})
  )

  return (
    <div className="max-w-4xl mx-auto mt-10 px-4 pb-16">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <Link to="/upload" className="bg-gray-900 text-white text-sm rounded-lg px-4 py-2">
          Upload statement
        </Link>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {txns.length === 0 ? (
        <p className="text-gray-500">No transactions yet — upload a statement to get started.</p>
      ) : (
        <>
          {/* Financial Health Score */}
          {healthScore?.score !== null && healthScore?.score !== undefined && (
            <div className="bg-white rounded-xl border p-5 mb-6 flex items-center gap-5">
              <div className="text-4xl font-bold">{healthScore.score}</div>
              <div>
                <p className="text-sm font-medium text-gray-700">Financial Health Score</p>
                <p className="text-sm text-gray-500">{healthScore.reason}</p>
              </div>
            </div>
          )}

          {/* Spend by category */}
          <div className="bg-white rounded-xl border p-4 mb-6" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byCategory}>
                <XAxis dataKey="category" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="total" fill="#111827" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Forecast */}
          {forecast.length > 0 && (
            <div className="bg-white rounded-xl border p-5 mb-6">
              <p className="text-sm font-medium text-gray-700 mb-3">Predicted next month</p>
              <div className="space-y-2">
                {forecast.map((f) => (
                  <div key={f.category} className="text-sm">
                    <div className="flex justify-between">
                      <span className="capitalize font-medium">{f.category}</span>
                      <span>₦{f.predicted_amount.toLocaleString()}</span>
                    </div>
                    <p className="text-gray-500 text-xs">{f.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies */}
          {anomalies.length > 0 && (
            <div className="bg-white rounded-xl border border-amber-200 bg-amber-50 p-5 mb-6">
              <p className="text-sm font-medium text-amber-800 mb-3">Flagged transactions</p>
              <div className="space-y-2">
                {anomalies.map((a) => (
                  <div key={a.transaction_id} className="text-sm">
                    <div className="flex justify-between">
                      <span>{a.description}</span>
                      <span>₦{Math.abs(a.amount).toLocaleString()}</span>
                    </div>
                    <p className="text-amber-700 text-xs">{a.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transactions table */}
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-2">Date</th>
                  <th className="px-4 py-2">Description</th>
                  <th className="px-4 py-2">Category</th>
                  <th className="px-4 py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {txns.map((t) => (
                  <tr key={t.id} className="border-t">
                    <td className="px-4 py-2">{t.date}</td>
                    <td className="px-4 py-2">{t.description}</td>
                    <td className="px-4 py-2 capitalize">{t.category}</td>
                    <td className="px-4 py-2 text-right">{t.amount.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
