import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import Navbar    from './components/Navbar'
import Feed      from './pages/Feed'
import Profile   from './pages/Profile'
import Generate  from './pages/Generate'
import Detect    from './pages/Detect'
import Admin     from './pages/Admin'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-white text-gray-900 dark:bg-slate-900 dark:text-slate-100">
          <Navbar />
          <main className="max-w-2xl mx-auto px-4 pt-20 pb-12">
            <Routes>
              <Route path="/"                    element={<Feed />} />
              <Route path="/profile/:username"   element={<Profile />} />
              <Route path="/generate"            element={<Generate />} />
              <Route path="/detect"              element={<Detect />} />
              <Route path="/admin"               element={<Admin />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  )
}
