import { useEffect, useState } from 'react'
import api from '../api'

export default function Planning() {
  // Simulator
  const [extra, setExtra] = useState(0)
  const [simResult, setSimResult] = useState(null)

  // Goals
  const [goals, setGoals] = useState([])
  const [goalForm, setGoalForm] = useState({ name: '', target_amount: '', target_date: '' })
  const [goalProjections, setGoalProjections] = useState({})

  // Debts
  const [debts, setDebts] = useState([])
  const [debtForm, setDebtForm] = useState({ name: '', balance: '', interest_rate: '', min_payment: '' })
  const [strategy, setStrategy] = useState('avalanche')
  const [payoffOrder, setPayoffOrder] = useState(null)

  useEffect(() => {
    api.get('/planning/simulate', { params: { extra_savings: 0 } }).then((r) => setSimResult(r.data))
    refreshGoals()
    refreshDebts()
  }, [])

  function refreshGoals() {
    api.get('/planning/goals').then((r) => setGoals(r.data))
  }

  function refreshDebts() {
    api.get('/planning/debts').then((r) => setDebts(r.data))
  }

  async function runSimulation(val) {
    setExtra(val)
    const r = await api.get('/planning/simulate', { params: { extra_savings: val } })
    setSimResult(r.data)
  }

  async function submitGoal(e) {
    e.preventDefault()
    await api.post('/planning/goals', {
      name: goalForm.name,
      target_amount: parseFloat(goalForm.target_amount),
      target_date: goalForm.target_date,
    })
    setGoalForm({ name: '', target_amount: '', target_date: '' })
    refreshGoals()
  }

  async function loadProjection(goalId) {
    const r = await api.get(`/planning/goals/${goalId}/projection`)
    setGoalProjections((prev) => ({ ...prev, [goalId]: r.data }))
  }

  async function submitDebt(e) {
    e.preventDefault()
    await api.post('/planning/debts', {
      name: debtForm.name,
      balance: parseFloat(debtForm.balance),
      interest_rate: parseFloat(debtForm.interest_rate),
      min_payment: parseFloat(debtForm.min_payment),
    })
    setDebtForm({ name: '', balance: '', interest_rate: '', min_payment: '' })
    refreshDebts()
  }

  async function loadPayoffOrder(s) {
    setStrategy(s)
    const r = await api.get('/planning/debts/payoff-order', { params: { strategy: s } })
    setPayoffOrder(r.data)
  }

  const inputCls = 'w-full border rounded-lg px-3 py-2 text-sm'

  return (
    <div className="max-w-4xl mx-auto mt-10 px-4 pb-16 space-y-8">
      <h1 className="text-xl font-semibold">Planning</h1>

      {/* Scenario Simulator */}
      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-1">Scenario simulator</h2>
        <p className="text-sm text-gray-500 mb-4">What if you saved more per month?</p>
        <input
          type="range"
          min="0"
          max="200000"
          step="5000"
          value={extra}
          onChange={(e) => runSimulation(Number(e.target.value))}
          className="w-full"
        />
        <p className="text-sm mt-2">Extra savings: ₦{extra.toLocaleString()}/mo</p>
        {simResult && <p className="text-sm text-gray-600 mt-2">{simResult.reason}</p>}
      </section>

      {/* Goals */}
      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-4">Savings goals</h2>
        <form onSubmit={submitGoal} className="grid grid-cols-3 gap-2 mb-4">
          <input
            className={inputCls}
            placeholder="Goal name"
            value={goalForm.name}
            onChange={(e) => setGoalForm({ ...goalForm, name: e.target.value })}
            required
          />
          <input
            className={inputCls}
            placeholder="Target amount"
            type="number"
            value={goalForm.target_amount}
            onChange={(e) => setGoalForm({ ...goalForm, target_amount: e.target.value })}
            required
          />
          <input
            className={inputCls}
            type="date"
            value={goalForm.target_date}
            onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
            required
          />
          <button className="col-span-3 bg-gray-900 text-white rounded-lg py-2 text-sm font-medium">
            Add goal
          </button>
        </form>
        <div className="space-y-3">
          {goals.map((g) => (
            <div key={g.id} className="border-t pt-3">
              <div className="flex justify-between text-sm">
                <span className="font-medium">{g.name}</span>
                <span>
                  ₦{g.target_amount.toLocaleString()} by {g.target_date}
                </span>
              </div>
              <button
                className="text-xs text-blue-600 mt-1"
                onClick={() => loadProjection(g.id)}
              >
                Check if I'm on track
              </button>
              {goalProjections[g.id] && (
                <p className="text-xs text-gray-600 mt-1">{goalProjections[g.id].reason}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Debt payoff */}
      <section className="bg-white rounded-xl border p-5">
        <h2 className="font-medium mb-4">Debt payoff helper</h2>
        <form onSubmit={submitDebt} className="grid grid-cols-4 gap-2 mb-4">
          <input
            className={inputCls}
            placeholder="Debt name"
            value={debtForm.name}
            onChange={(e) => setDebtForm({ ...debtForm, name: e.target.value })}
            required
          />
          <input
            className={inputCls}
            placeholder="Balance"
            type="number"
            value={debtForm.balance}
            onChange={(e) => setDebtForm({ ...debtForm, balance: e.target.value })}
            required
          />
          <input
            className={inputCls}
            placeholder="Interest rate %"
            type="number"
            value={debtForm.interest_rate}
            onChange={(e) => setDebtForm({ ...debtForm, interest_rate: e.target.value })}
            required
          />
          <input
            className={inputCls}
            placeholder="Min payment"
            type="number"
            value={debtForm.min_payment}
            onChange={(e) => setDebtForm({ ...debtForm, min_payment: e.target.value })}
            required
          />
          <button className="col-span-4 bg-gray-900 text-white rounded-lg py-2 text-sm font-medium">
            Add debt
          </button>
        </form>

        {debts.length > 0 && (
          <>
            <div className="flex gap-2 mb-3">
              <button
                onClick={() => loadPayoffOrder('avalanche')}
                className={`text-xs px-3 py-1 rounded-full border ${strategy === 'avalanche' ? 'bg-gray-900 text-white' : ''}`}
              >
                Avalanche
              </button>
              <button
                onClick={() => loadPayoffOrder('snowball')}
                className={`text-xs px-3 py-1 rounded-full border ${strategy === 'snowball' ? 'bg-gray-900 text-white' : ''}`}
              >
                Snowball
              </button>
            </div>
            {payoffOrder && (
              <div className="text-sm">
                <p className="text-gray-600 mb-2">{payoffOrder.reason}</p>
                <ol className="list-decimal list-inside space-y-1">
                  {payoffOrder.order.map((name) => (
                    <li key={name}>{name}</li>
                  ))}
                </ol>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}
