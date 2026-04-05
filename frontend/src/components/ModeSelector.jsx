import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

const MODES = ['auto', 'alphabet', 'number', 'word', 'sentence']

export default function ModeSelector() {
  const { mode, setMode, language } = useRecognitionStore()
  const t = language === 'hi' ? hi : en

  return (
    <div className="flex gap-1 flex-wrap">
      {MODES.map(m => (
        <button
          key={m}
          onClick={() => setMode(m)}
          className="px-3 py-1 rounded-full text-xs font-semibold transition-all duration-200"
          style={mode === m ? {
            background: 'linear-gradient(135deg, #00d4ff, #6366f1)',
            color: 'white',
            boxShadow: '0 2px 14px rgba(99,102,241,0.45)',
            border: 'none',
          } : {
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.07)',
            color: '#64748b',
            cursor: 'pointer',
          }}
        >
          {t.modes[m]}
        </button>
      ))}
    </div>
  )
}
