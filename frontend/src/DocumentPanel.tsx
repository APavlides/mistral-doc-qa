import { useState } from 'react'

function DocumentPanel() {
  const [text, setText] = useState('')
  const [chunkCount, setChunkCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function loadFile(file: File | undefined) {
    if (file) setText(await file.text())
  }

  async function save() {
    if (!text.trim()) {
      setError('Paste or upload some text first.')
      return
    }
    setLoading(true)
    setError('')
    setChunkCount(null)
    try {
      const res = await fetch('/api/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail ?? `Request failed (${res.status})`)
      }
      const data = await res.json()
      setChunkCount(data.chunk_count)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>1. Document</h2>
      <input
        type="file"
        accept=".txt,text/plain"
        onChange={(e) => loadFile(e.target.files?.[0])}
      />
      <div>
        <textarea
          rows={10}
          cols={70}
          placeholder="Paste your document here"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>
      <button onClick={save} disabled={loading}>
        {loading ? 'Saving...' : 'Save document'}
      </button>
      {error && <p>Error: {error}</p>}
      {chunkCount !== null && <p>Saved: {chunkCount} chunks</p>}
    </section>
  )
}

export default DocumentPanel
