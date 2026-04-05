import { NavLink } from 'react-router-dom'
import { Hand, BookOpen, Upload, BookMarked, Info, GraduationCap } from 'lucide-react'
import LanguageToggle from './LanguageToggle'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

const links = [
  { to: '/', label: 'home', icon: Hand },
  { to: '/learn', label: 'learn', icon: BookOpen },
  { to: '/teach', label: 'teach', icon: GraduationCap },
  { to: '/upload', label: 'upload', icon: Upload },
  { to: '/vocab', label: 'vocab', icon: BookMarked },
  { to: '/about', label: 'about', icon: Info },
]

export default function Navbar() {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  return (
    <nav style={{
      background: 'rgba(5, 13, 26, 0.85)',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      boxShadow: '0 1px 0 rgba(0,212,255,0.08), 0 4px 30px rgba(0,0,0,0.5)',
    }} className="sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">

        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div style={{
            background: 'linear-gradient(135deg, #00d4ff, #6366f1)',
            borderRadius: '8px',
            padding: '5px',
            boxShadow: '0 0 14px rgba(99,102,241,0.45)',
          }}>
            <Hand className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white tracking-tight text-sm sm:text-base">
            ISL <span className="text-gradient">Recognition</span>
          </span>
        </div>

        {/* Desktop nav */}
        <div className="hidden sm:flex items-center gap-0.5">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive ? 'text-white' : 'text-slate-400 hover:text-slate-100'
                }`
              }
              style={({ isActive }) => isActive ? {
                background: 'linear-gradient(135deg, rgba(0,212,255,0.1), rgba(99,102,241,0.1))',
                border: '1px solid rgba(99,102,241,0.22)',
                boxShadow: '0 0 14px rgba(99,102,241,0.12)',
              } : {}}
            >
              <Icon className="w-4 h-4" />
              {t.nav[label]}
            </NavLink>
          ))}
        </div>

        <LanguageToggle />
      </div>

      {/* Mobile bottom nav */}
      <div className="sm:hidden flex" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-2 text-xs font-medium transition-all ${
                isActive ? 'text-cyan-400' : 'text-slate-500'
              }`
            }
          >
            <Icon className="w-5 h-5 mb-0.5" />
            {t.nav[label]}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
