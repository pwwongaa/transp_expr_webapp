// src/pages/Analysis.jsx
import axios from 'axios';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../api/api'; // Hosting: import your API base URL

export default function Analysis() {
  const [status, setStatus] = useState('processing')
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // Poll /analysis every 5 seconds, check the complete flag -> FASTAPI will udpate state once found
  // analysis the backend status
  useEffect(() => {
    let intervalId
    async function pollStatus() {
      try {
        // const res = await axios.get('http://localhost:8000/analysis')
        const res = await axios.get(`${API_BASE}/analysis`) // ✅ Use dynamic backend URL
        
        if (res.data.status === 'done') {
          setStatus('done')
          clearInterval(intervalId)
          navigate('/result')
        }
      } catch (err) {
        setError(err.message)
        clearInterval(intervalId)
      }
    }
    // Start polling
    pollStatus()
    intervalId = setInterval(pollStatus, 5000)
    return () => clearInterval(intervalId)
  }, [])

  if (error) {
    return <div className="p-10 text-red-500">Error: {error}</div>
  }

  return (
    <div className="p-10 max-w-3xl mx-auto text-center space-y-4">
      <h2 className="text-3xl font-bold text-blue-600 mb-6">📊 Analysis status</h2>
      {status === 'processing' ? (
        <>
          <p className="text-lg">Analysis in progress...</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 bg-gray-300 text-gray-700 py-2 px-4 rounded"
          >
            Cancel
          </button>
        </>
      ) : (
        <>
          <p className="text-green-600 text-xl">Analysis complete!</p>
          <button
            onClick={() => navigate('/result')}
            className="mt-4 bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-full shadow transition"
          >
            View Results
          </button>
        </>
      )}
    </div>
  )
}
