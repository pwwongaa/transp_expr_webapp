import axios from 'axios'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

// function Home() {

//Use Tailwind CSS
export default function Home() {
  const navigate = useNavigate() //for navigation
 
  //Reset start - automatic execution
  //execute the fastapi backend - /reset route to execute this reset
  useEffect(() => {
    axios.post('http://localhost:8000/reset')
      .catch(err => console.error('Reset failed:', err))
  }, [])

  // Main content
  return (
    //The Main Box: white colour, round corner, shadow, max width, margin-auto
    <div className="bg-white rounded-2xl shadow-lg p-10 max-w-x1 mx-auto mt-10">
      {/* Header1: Text size: text size, bold font, blue text, word widening, word shadow */}
      <h1 className="text-4xl font-bold text-center text-blue-600 tracking-wide drop-shadow mb-4">
         🧬 Expression Matrix Web App</h1>
      <h4 className="text-2xl font-bold text-center text-black justify-center tracking-wide drop-shadow mb-4">
        Welcome to the analysis web platform! </h4>
      <div className="mt-4 text-center text-gray-700 italic-700">
        <p>Upload your data, run analysis</p>
        <p>and visualize results seamlessly.</p>
      </div>

      {/* Button */}
      <div className="mt-8 text-center">
        {/* Move to uplaod page */}
        <button
          // Button: hover:colour: the colour change when pointing
          className="bg-blue-500 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-full shadow transition"
          onClick={() => navigate('/upload')}
        >
          Start Analysis
        </button>
      </div>
    </div>
  )
}

