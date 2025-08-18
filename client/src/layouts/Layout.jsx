
import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

export default function Layout() {
  return (
    // Main Layout
    <div className="flex flex-col min-h-screen bg-gray-900 text-white justify-center items-center">
      {/* Navbar fixed at top */}
      <Navbar />

      {/* Main content area */}
      <main className="flex-1 flex justify-center items-center w-full px-4 py-8">
        {/* Optional: Limit height of main content */}
        <div className="w-full max-w-2xl">
          <Outlet /> {/* <-- required for child routes */}
        </div>
      </main>
    </div>
  );
}
