import CameraPanel from '../components/CameraPanel'
import OutputPanel from '../components/OutputPanel'
import RecognitionHistory from '../components/RecognitionHistory'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'
import { useQuery } from '@tanstack/react-query'
import { checkHealth } from '../services/api'
import { Brain, Zap, Layers } from 'lucide-react'

export default function Home() {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 30000,
  })

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1.5 flex-wrap">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">{t.home.title}</h1>
          {health?.models_loaded && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '2px 12px', borderRadius: '9999px', fontSize: '11px', fontWeight: 600,
              background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)',
              color: '#34d399', boxShadow: '0 0 12px rgba(16,185,129,0.1)',
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34d399', display: 'inline-block', boxShadow: '0 0 6px #34d399' }} />
              Live
            </span>
          )}
        </div>
        <p className="text-slate-400 text-sm">{t.home.subtitle}</p>

        {health && !health.models_loaded && (
          <div className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs text-yellow-400"
            style={{ background: 'rgba(234,179,8,0.07)', border: '1px solid rgba(234,179,8,0.2)' }}>
            ⚠ Models not loaded. Run training scripts first (see README).
          </div>
        )}

        {/* Stat pills */}
        {health?.models_loaded && (
          <div className="flex gap-2 mt-4 flex-wrap">
            {[
              { icon: Brain,  label: '296 Signs',          color: '#00d4ff', rgb: '0,212,255' },
              { icon: Zap,    label: '92.2% Accuracy',     color: '#6366f1', rgb: '99,102,241' },
              { icon: Layers, label: 'BiLSTM + Attention', color: '#a78bfa', rgb: '167,139,250' },
            ].map(({ icon: Icon, label, color, rgb }) => (
              <div key={label}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{
                  background: `rgba(${rgb},0.07)`,
                  border: `1px solid rgba(${rgb},0.18)`,
                  color,
                }}>
                <Icon className="w-3 h-3" />
                {label}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <CameraPanel />
          <RecognitionHistory />
        </div>
        <div>
          <OutputPanel />
        </div>
      </div>
    </div>
  )
}
