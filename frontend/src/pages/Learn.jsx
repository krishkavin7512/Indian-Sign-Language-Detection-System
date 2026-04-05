import { useState, useEffect } from 'react'
import { Trophy, Zap, RotateCcw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

const ALPHABET_SIGNS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
const STORAGE_KEY = 'isl_learn_score'

function getScore() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || { score: 0, streak: 0, best: 0 } }
  catch { return { score: 0, streak: 0, best: 0 } }
}
function saveScore(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)) }

export default function Learn() {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en
  const { prediction, confidence } = useRecognitionStore()
  const [scoreData, setScoreData] = useState(getScore)
  const [target, setTarget] = useState(() => ALPHABET_SIGNS[Math.floor(Math.random() * 26)])
  const [feedback, setFeedback] = useState(null) // 'correct' | 'wrong' | null

  useEffect(() => {
    if (!prediction?.label || confidence < 0.8) return
    if (prediction.label === target) {
      setFeedback('correct')
      const next = { ...scoreData, score: scoreData.score + 10, streak: scoreData.streak + 1 }
      next.best = Math.max(next.best, next.streak)
      setScoreData(next)
      saveScore(next)
      setTimeout(() => {
        setTarget(ALPHABET_SIGNS[Math.floor(Math.random() * 26)])
        setFeedback(null)
      }, 1200)
    }
  }, [prediction?.label, confidence])

  const reset = () => {
    const z = { score: 0, streak: 0, best: 0 }
    setScoreData(z)
    saveScore(z)
    setFeedback(null)
    setTarget(ALPHABET_SIGNS[Math.floor(Math.random() * 26)])
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">{t.learn.title}</h1>
        <p className="text-slate-400 text-sm mt-1">{t.learn.subtitle}</p>
      </div>

      {/* Score row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { icon: Trophy, label: t.learn.score, value: scoreData.score, color: 'text-yellow-400' },
          { icon: Zap, label: t.learn.streak, value: scoreData.streak, color: 'text-blue-400' },
          { icon: Trophy, label: 'Best Streak', value: scoreData.best, color: 'text-purple-400' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="card p-4 text-center">
            <Icon className={`w-5 h-5 mx-auto mb-1 ${color}`} />
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <p className="text-xs text-slate-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Target sign */}
      <div className="card p-10 text-center mb-6">
        <p className="text-slate-400 text-sm mb-4">{t.learn.practice} ISL sign for:</p>
        <AnimatePresence mode="wait">
          <motion.div
            key={target + feedback}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.1, opacity: 0 }}
            className={`text-8xl font-bold mb-4 ${
              feedback === 'correct' ? 'text-green-400' :
              feedback === 'wrong' ? 'text-red-400' : 'text-blue-400'
            }`}
          >
            {target}
          </motion.div>
        </AnimatePresence>
        {feedback === 'correct' && (
          <p className="text-green-400 font-medium animate-fade-in">Correct! +10</p>
        )}
        <p className="text-slate-500 text-sm mt-3">
          Use live recognition on the Home page, then come back here to track score.
        </p>
      </div>

      <div className="flex justify-center">
        <button onClick={reset} className="btn-secondary flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Reset Score
        </button>
      </div>
    </div>
  )
}
