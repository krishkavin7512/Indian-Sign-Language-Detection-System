import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Learn from './pages/Learn'
import Upload from './pages/Upload'
import Vocab from './pages/Vocab'
import About from './pages/About'
import Teach from './pages/Teach'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/vocab" element={<Vocab />} />
            <Route path="/about" element={<About />} />
            <Route path="/teach" element={<Teach />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
