import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (!file) return
    setStatus('Uploading...')
    const form = new FormData()
    form.append('file', file)
    try {
      await api.post('/transactions/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setStatus('Done')
      navigate('/')
    } catch (err) {
      setStatus(err.response?.data?.detail || 'Upload failed')
    }
  }

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-8 rounded-xl shadow-sm border">
      <h1 className="text-xl font-semibold mb-2">Upload a statement</h1>
      <p className="text-sm text-gray-500 mb-6">
        CSV with date, description, amount columns — or a PDF bank statement.
      </p>
      <form onSubmit={submit} className="space-y-4">
        <input
          type="file"
          accept=".csv,.pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="block w-full text-sm"
        />
        <button className="w-full bg-gray-900 text-white rounded-lg py-2 font-medium">
          Upload
        </button>
      </form>
      {status && <p className="text-sm text-gray-500 mt-4">{status}</p>}
    </div>
  )
}
