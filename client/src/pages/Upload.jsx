// src/pages/Upload.jsx
import axios from 'axios'; //HTTP request
import { useState } from 'react'; //React hook to manage local state
import { useNavigate } from 'react-router-dom'; //moving page
import { API_BASE } from '../api/api';

export default function Upload() {
  const [exprFile, setExprFile] = useState(null)
  const [covFile, setCovFile]   = useState(null)
  const [uploaded, setUploaded] = useState(false)  // upload
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  //Check file upload, make sure that both file are uplaoded before start the analysis
  const handleUpload = async () => {
    if (!exprFile || !covFile) {
      alert('Please select both files before starting analysis')
      return
    }
    setLoading(true)
    const formData = new FormData()
    formData.append('expression_matrix', exprFile) //expresison file
    formData.append('covariate_table', covFile) //covariate file

    //? Handle file loading
    //*8000: local backend fastapi
    //route this back to the /upload ->//! FASTAPI backend
    try {
      //! await axios.post('http://localhost:8000/upload', formData)
      // Backend AWS EC2 HOSTING
      await axios.post(`${API_BASE}/upload`, formData) //use ` `
      
      alert('Upload Successful')
      setUploaded(true)
    } catch (err) {
      alert('Uplaod Failed' + (err.message || err))
    } finally {
      setLoading(false)
    }
  }

  //? Handling pipeline execution
  const handleAnalyze = async () => {
    setLoading(true)
    try {
      //Pipeline execution: Send post -> to FASTAPI
      //! const response = await axios.post('http://localhost:8000/run')
      // Backend AWS EC2 HOSTING: from local host :8000 to api:8000
      const response = await axios.post(`${API_BASE}/run`)

      //Page navigation: if SUCCESS => auto nav, if NOT => Error
      if (response.status === 200 && response.data.success !== false) {
            navigate('/analysis')  // move to analysis page
          } else {
            const msg = response.data.error || response.data.detail || 'Unknown error'
            alert('Analysis failed: ' + msg)
          }
        } catch (err) {
          alert('Analysis execution failed: ' + (err.response?.data?.detail || err.message))
        } finally {
          setLoading(false)
        }
    }


  // Rendering
  return (
    <div className="bg-white rounded-2xl shadow-lg p-10 max-w-xl mx-auto mt-16">
      {/* File Uplaod */}
      <div>
        <h2 className="text-3xl font-bold text-blue-600 mb-6">
          📁 Upload Your Data
        </h2>

        {/* Expression Matrix Upload */}
        {/* Section: uplaod file */}
        <label className="block mb-2">
          <span className="text-lg font-medium text-gray-700">
            🧬 Expression Matrix
          </span>
          <p className="text-black">Please uplaod the expresison matrix table file</p>
          <input
            type="file"
            accept=".csv,.tsv"
            onChange={e => setExprFile(e.target.files?.[0] ?? null)}
            className="mt-2 block w-full text-gray-700 border border-gray-300 rounded p-2"
          />
          <br></br>
        </label>

        {/* Covariate Table Upload */}
        <label className="block mb-4">
          <span className="text-lg font-medium text-gray-700">
            📊 Covariate Table
          </span>
          <p className="text-black">Please uplaod the metadata, covariate table file</p>
          <input
            type="file"
            accept=".csv,.tsv"
            onChange={e => setCovFile(e.target.files?.[0] ?? null)}
            className="mt-2 block w-full text-gray-700 border border-gray-300 rounded p-2"
          />
        </label>

        {/* Upload & Analyze Button */}
        {/* Need to 1) Upload the files, 2) run the analysis */}
        {/* SVG spinning during loading */}
        <button
          onClick={handleUpload}
          disabled={loading}      
          className={`
            mt-4 w-full bg-blue-500 hover:bg-blue-700 text-white py-3 rounded-full shadow
            transition ${loading ? 'opacity-70 cursor-not-allowed' : ''}
          `}
        >
          {/* TODO: improve later */}
          {loading ? 'Uploading...' : 'Upload Files'}
        </button>
        
        {/* Start Analysis Button */}
        <button
          onClick={handleAnalyze}
          disabled={!uploaded}
          className={`
            w-full bg-green-500 hover:bg-green-600 text-white py-3 rounded-full shadow
            transition ${(!uploaded || loading) ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {/* {loading ? 'Initialising...' : 'Start Analysis'} */}
          Start Analysis
        </button>
      </div>
    </div>
  )
}
