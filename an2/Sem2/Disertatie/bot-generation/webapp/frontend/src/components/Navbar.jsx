import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

const links = [
  { to: '/',         label: 'Feed'     },
  { to: '/generate', label: 'Generate' },
  { to: '/detect',   label: 'Detect'   },
  { to: '/admin',    label: 'Admin'    },
]

export default function Navbar() {
  const { pathname }    = useLocation()
  const { dark, toggle } = useTheme()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50
                    bg-white/95 dark:bg-slate-900/95
                    backdrop-blur
                    border-b border-gray-200 dark:border-slate-700">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="font-bold text-lg text-blue-500 dark:text-blue-400 flex items-center gap-2 mr-4">
          BotFarm
        </Link>

        {/* Nav links + theme toggle */}
        <div className="flex items-center gap-1">
          {links.map(({ to, label }) => {
            const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
            return (
              <Link key={to} to={to}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium
                      ${active
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-gray-100 dark:hover:bg-slate-800'}`}>
                {label}
              </Link>
            )
          })}

          {/* ☀️ / 🌙 toggle */}
          <button
            onClick={toggle}
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            className="ml-2 w-8 h-8 flex items-center justify-center rounded-lg
                       text-gray-500 dark:text-slate-400
                       hover:bg-gray-100 dark:hover:bg-slate-800
                       hover:text-gray-900 dark:hover:text-slate-100">
            {dark ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  )
}
