// import { Link } from 'react-router-dom'

// function Navbar() {
//   return (
//     // <nav className="sticky top-0 z-50 bg-grey-600 shadow-md shadow-sm">
//     <nav className="sticky top-0 left-0 w-full bg-blue-600 shadow-md z-50">
//       <div className="container flex items-center justify-center max-w-6xl mx-auto px-4 py-3 ">
//         <ul className="flex justify-center items-center space-x-10 text-white text-lg font-medium list-none m-0 p-0">
//           <li>
//             <Link to="/" className="inline-flex items-center hover:text-yellow-300 transition">🏠 Home</Link>
//           </li>
//           <li>
//             <Link to="/upload" className="inline-flex items-center hover:text-yellow-300 transition">📤 Upload</Link>
//           </li>
//           <li>
//             <Link to="/analysis" className="inline-flex items-center hover:text-yellow-300 transition">⚙️ Analysis</Link>
//           </li>
//           <li>
//             <Link to="/result" className="inline-flex items-center hover:text-yellow-300 transition">📊 Result</Link>
//           </li>
//         </ul>
//       </div>
//     </nav>
//   )
// }

// export default Navbar


// src/components/Navbar.jsx
import React from 'react'
import { NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="w-full bg-blue-900 text-white">
      {/* flex: for flexible horizontal arr, jst-c: center, space-x-N: sep between items, py-3: padding yaxis 3, list-none: rm bullet points*/}
      <ul className="flex justify-center items-center space-x-2 py-3 list-none m-0 p-0">
        {[
          { to: '/',         label: '🏠 Home'     },
          { to: '/upload',   label: '📤 Upload'   },
          { to: '/analysis', label: '⚙️ Analysis' },
          { to: '/result',   label: '📊 Result'   },
        ].map(({ to, label }) => (
          <li key={to}>
            <NavLink
              to={to} 
              // Styling in each Button in Nav Bar
              // pxpy: padding, text-blue-300 trans.: change colour when pointing
              className="px-4 py-1 no-underline hover:text-blue-300 transition">
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
