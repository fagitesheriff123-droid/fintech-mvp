import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (!file || busy) return
    setBusy(true); setStatus('Uploading and reading your statement…')
    const form = new FormData()
    form.append('file', file)
    try {
      await api.post('/transactions/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      navigate('/')
    } catch (err) {
      setStatus(err.response?.data?.detail || 'Upload failed — the server may be waking up, try again.')
    } finally { setBusy(false) }
  }

  return (
    <div className="max-w-md mx-auto mt-12 px-4">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-xl font-bold mb-1">Upload a statement</h1>
        <p className="text-sm text-slate-500 mb-6">CSV (date, description, amount) or a PDF bank statement. Max 5MB.</p>
        <form onSubmit={submit} className="space-y-4">
          <label className="block border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-6 text-center cursor-pointer text-sm text-slate-500">
            {file ? <span className="text-slate-800 font-medium">{file.name}</span> : 'Tap to choose a .csv or .pdf file'}
            <input type="file" accept=".csv,.pdf" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
          </label>
          <button disabled={!file || busy} className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl py-2.5 font-semibold">
            {busy ? 'Working…' : 'Upload'}
          </button>
        </form>
        {status && <p className="text-sm text-slate-600 mt-4">{status}</p>}
      </div>
    </div>
  )
}
