
// src/App.jsx
import { BrowserRouter, Route, Routes } from 'react-router-dom'; //Own router setting, Route:for layout
import './index.css'; // import Tailwind CSS
import Layout from './layouts/Layout';
import Analysis from './pages/Analysis';
import Home from './pages/Home';
import Result from './pages/Result';
import Upload from './pages/Upload';



function App() {
  return (
    //Browser router, add  basename="/transp_expr_webapp"> for GH page
    <BrowserRouter basename="/transp_expr_webapp">
      <Routes>
        {/* Routes, use / as root to wrap all pages */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="result" element={<Result />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;


