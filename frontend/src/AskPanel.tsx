import { useState } from 'react'

function AskPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function ask() {
    if (!question.trim()) {
      setError('Type a question first.')
      return
    }
    setLoading(true)
    setError('')
    setAnswer('')
    setSources([])
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail ?? `Request failed (${res.status})`)
      }
      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>2. Ask</h2>
      <input
        size={60}
        placeholder="Ask a question about the document"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button onClick={ask} disabled={loading}>
        {loading ? 'Asking...' : 'Ask'}
      </button>
      {error && <p>Error: {error}</p>}
      {answer ? (
        <>
          <p>{answer}</p>
          <h3>Sources</h3>
          <ol>
            {sources.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </>
      ) : (
        !loading && !error && <p>No answer yet.</p>
      )}
    </section>
  )
}

export default AskPanel
