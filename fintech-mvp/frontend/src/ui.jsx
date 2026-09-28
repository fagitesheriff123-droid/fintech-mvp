// Shared building blocks so every page looks the same.
export const naira = (n) => '₦' + Math.round(Number(n) || 0).toLocaleString()
export const input = 'w-full border border-slate-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500'
export const btn = 'bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl px-4 py-2 text-sm font-semibold'
export const errMsg = (e, fallback = 'Something went wrong — the server may be waking up, try again.') =>
  e?.response?.data?.detail || fallback

export const Card = ({ title, sub, children, className = '' }) => (
  <section className={`bg-white rounded-2xl border border-slate-200 shadow-sm p-5 ${className}`}>
    {title && <h2 className="text-sm font-semibold text-slate-800">{title}</h2>}
    {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
    {(title || sub) && <div className="mb-3" />}
    {children}
  </section>
)

export const Stat = ({ label, value, tone = 'text-slate-900' }) => (
  <div className="bg-slate-50 rounded-xl p-3">
    <p className="text-xs text-slate-500">{label}</p>
    <p className={`text-base sm:text-lg font-bold mt-0.5 ${tone}`}>{value}</p>
  </div>
)

export const Badge = ({ ok, children }) => (
  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ok ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{children}</span>
)
