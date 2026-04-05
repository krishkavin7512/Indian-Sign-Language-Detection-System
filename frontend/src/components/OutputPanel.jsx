import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { useRecognitionStore } from '../store/recognitionStore'
import ConfidenceMeter from './ConfidenceMeter'
import SentenceBuilder from './SentenceBuilder'
import en from '../translations/en'
import hi from '../translations/hi'

export default function OutputPanel() {
  const { prediction, confidence, alternatives, modelUsed, language } = useRecognitionStore()
  const t = language === 'hi' ? hi : en
  const hasSign = prediction?.label && prediction.label !== '—'

  const displayLabel = language === 'hi' && prediction?.label_hindi
    ? prediction.label_hindi
    : prediction?.label

  const labelLen = displayLabel ? displayLabel.length : 0
  const fontSize = labelLen > 12 ? '2.5rem' : labelLen > 8 ? '3.5rem' : '5rem'

  return (
    <div
      className="card p-6 flex flex-col h-full"
      style={{
        border: hasSign
          ? '1px solid rgba(0,212,255,0.22)'
          : '1px solid rgba(255,255,255,0.07)',
        boxShadow: hasSign
          ? '0 8px 32px rgba(0,0,0,0.5), 0 0 50px rgba(0,212,255,0.07)'
          : '0 8px 32px rgba(0,0,0,0.5)',
        transition: 'border-color 0.5s ease, box-shadow 0.5s ease',
        gap: '20px',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4" style={{ color: '#00d4ff' }} />
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
          {t.output.recognized}
        </p>
      </div>

      {/* Main prediction */}
      <div className="flex-1 flex flex-col items-center justify-center relative py-4">
        {hasSign && (
          <div style={{
            position: 'absolute',
            width: '220px',
            height: '220px',
            background: 'radial-gradient(circle, rgba(0,212,255,0.07) 0%, transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }} />
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={displayLabel}
            initial={{ opacity: 0, scale: 0.75, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.75, y: -12 }}
            transition={{ duration: 0.22, type: 'spring', stiffness: 320, damping: 26 }}
            className={`relative text-center font-extrabold tracking-tight leading-none ${language === 'hi' ? 'font-hindi' : ''}`}
            style={{
              fontSize,
              background: hasSign ? 'linear-gradient(135deg, #00d4ff, #6366f1)' : undefined,
              WebkitBackgroundClip: hasSign ? 'text' : undefined,
              WebkitTextFillColor: hasSign ? 'transparent' : undefined,
              backgroundClip: hasSign ? 'text' : undefined,
              color: hasSign ? undefined : 'rgba(100,116,139,0.35)',
            }}
          >
            {displayLabel || '—'}
          </motion.div>
        </AnimatePresence>

        {hasSign && language === 'en' && prediction.label_hindi && (
          <motion.p
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 text-slate-400 font-hindi text-xl"
          >
            {prediction.label_hindi}
          </motion.p>
        )}
      </div>

      {/* Confidence */}
      <ConfidenceMeter confidence={confidence} />

      {/* Meta badges */}
      {modelUsed && (
        <div className="flex gap-2 flex-wrap">
          <span style={{
            display: 'inline-flex', alignItems: 'center', padding: '2px 10px',
            borderRadius: '9999px', fontSize: '11px', fontWeight: 500,
            background: 'rgba(0,212,255,0.07)', border: '1px solid rgba(0,212,255,0.2)',
            color: '#00d4ff',
          }}>
            {modelUsed}
          </span>
          {prediction?.mode && (
            <span className="badge">{t.modes[prediction.mode] || prediction.mode}</span>
          )}
        </div>
      )}

      {/* Alternatives */}
      {alternatives?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-slate-500">{t.output.alternatives}</p>
          <div className="flex gap-2 flex-wrap">
            {alternatives.map((alt, i) => (
              <span key={i} className="badge">
                {language === 'hi' && alt.label_hindi ? alt.label_hindi : alt.label}
                <span className="ml-1.5 text-[10px] text-slate-500">{Math.round(alt.confidence * 100)}%</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sentence */}
      <SentenceBuilder />
    </div>
  )
}
