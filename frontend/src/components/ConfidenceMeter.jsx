import { motion } from 'framer-motion'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function ConfidenceMeter({ confidence = 0 }) {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en
  const pct = Math.round(confidence * 100)

  const color = confidence >= 0.5 ? '#00d4ff' : confidence >= 0.3 ? '#f59e0b' : '#f87171'
  const endColor = confidence >= 0.5 ? '#6366f1' : confidence >= 0.3 ? '#ef4444' : '#dc2626'
  const glow = confidence >= 0.5
    ? 'rgba(0,212,255,0.45)'
    : confidence >= 0.3 ? 'rgba(245,158,11,0.45)' : 'rgba(248,113,113,0.45)'

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-xs">
        <span className="text-slate-400 uppercase tracking-wider font-medium">{t.output.confidence}</span>
        <motion.span
          key={pct}
          initial={{ scale: 1.4, opacity: 0.6 }}
          animate={{ scale: 1, opacity: 1 }}
          className="font-bold tabular-nums"
          style={{ color }}
        >
          {pct}%
        </motion.span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          style={{
            background: `linear-gradient(90deg, ${color}, ${endColor})`,
            boxShadow: pct > 5 ? `0 0 10px ${glow}` : 'none',
          }}
        />
      </div>
    </div>
  )
}
