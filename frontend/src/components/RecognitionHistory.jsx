import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Trash2 } from 'lucide-react'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function RecognitionHistory() {
  const { history, clearHistory, language } = useRecognitionStore()
  const t = language === 'hi' ? hi : en

  if (history.length === 0) return null

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm" style={{ color: '#475569' }}>
          <Clock className="w-3.5 h-3.5" />
          <span>
            Recent{' '}
            <span style={{ color: 'rgba(0,212,255,0.65)', fontWeight: 600 }}>
              ({history.length})
            </span>
          </span>
        </div>
        <button
          onClick={clearHistory}
          className="transition-all duration-200 p-1 rounded-lg hover:bg-red-500/10"
          style={{ color: '#475569' }}
          onMouseEnter={e => e.currentTarget.style.color = '#f87171'}
          onMouseLeave={e => e.currentTarget.style.color = '#475569'}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
        <AnimatePresence initial={false}>
          {history.slice(0, 20).map(item => {
            const c = item.confidence
            const rgb = c >= 0.5 ? '0,212,255' : c >= 0.3 ? '245,158,11' : '248,113,113'
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.7 }}
                transition={{ type: 'spring', stiffness: 420, damping: 28 }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold cursor-default"
                style={{
                  background: `rgba(${rgb},0.08)`,
                  border: `1px solid rgba(${rgb},0.22)`,
                  color: `rgba(${rgb},0.9)`,
                }}
              >
                <span>{language === 'hi' && item.labelHindi ? item.labelHindi : item.label}</span>
                <span style={{ color: `rgba(${rgb},0.5)`, fontSize: '10px' }}>
                  {Math.round(c * 100)}%
                </span>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
