import { useEffect, useState } from 'react'
import AskPanel from './AskPanel'
import DocumentPanel from './DocumentPanel'

function App() {
  const [backend, setBackend] = useState('checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setBackend(data.status))
      .catch(() => setBackend('unreachable'))
  }, [])

  return (
    <main>
      <h1>Document Q&A</h1>
      <p>Backend: {backend}</p>
      <DocumentPanel />
      <AskPanel />
    </main>
  )
}

export default App
