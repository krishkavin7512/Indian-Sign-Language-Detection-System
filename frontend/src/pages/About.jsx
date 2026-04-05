import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, Info, Cpu, Database } from 'lucide-react'
import { checkHealth } from '../services/api'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

const DATASETS = [
  { name: 'Kaggle ISL', desc: 'A-Z + 0-9 static hand signs', size: '~87K images' },
  { name: 'INCLUDE', desc: '263 ISL word signs', size: '4287 videos' },
  { name: 'ISL-CSLTR', desc: 'Continuous sentence signing', size: '700 videos' },
  { name: 'iSign', desc: 'Additional word-level signs', size: 'Variable' },
]

const MODELS = [
  { name: 'Static Classifier', desc: 'MLP on 63-dim hand landmarks', use: 'Alphabets & Numbers' },
  { name: 'Dynamic LSTM', desc: 'BiLSTM + Attention on 45-frame sequences', use: '263 INCLUDE words' },
  { name: 'Sentence CTC', desc: 'Conv1D + BiLSTM with CTC loss', use: 'Continuous sentences' },
]

function StatusDot({ ok }) {
  return ok
    ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
    : <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
}

export default function About() {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: checkHealth })

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white">{t.about.title}</h1>
        <p className="text-slate-400 text-sm mt-1">{t.about.subtitle}</p>
      </div>

      {/* System status */}
      {health && (
        <section className="card p-6 space-y-3">
          <h2 className="font-semibold text-white flex items-center gap-2"><Cpu className="w-4 h-4 text-blue-400" /> System Status</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['API Server', true],
              ['Static Model', health.static_model],
              ['Dynamic Model', health.dynamic_model],
              ['Sentence Model', health.sentence_model],
            ].map(([label, ok]) => (
              <div key={label} className="flex items-center gap-2 text-slate-300">
                <StatusDot ok={ok} /> {label}
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500">API v{health.version}</p>
        </section>
      )}

      {/* Datasets */}
      <section className="space-y-3">
        <h2 className="font-semibold text-white flex items-center gap-2"><Database className="w-4 h-4 text-blue-400" /> Datasets</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DATASETS.map(d => (
            <div key={d.name} className="card p-4 space-y-1">
              <p className="font-medium text-slate-200">{d.name}</p>
              <p className="text-sm text-slate-400">{d.desc}</p>
              <p className="text-xs text-slate-500">{d.size}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Models */}
      <section className="space-y-3">
        <h2 className="font-semibold text-white flex items-center gap-2"><Info className="w-4 h-4 text-blue-400" /> ML Models</h2>
        <div className="space-y-3">
          {MODELS.map(m => (
            <div key={m.name} className="card p-4 flex items-start gap-4">
              <div className="flex-1">
                <p className="font-medium text-slate-200">{m.name}</p>
                <p className="text-sm text-slate-400 mt-0.5">{m.desc}</p>
              </div>
              <span className="badge bg-blue-500/10 text-blue-400 whitespace-nowrap">{m.use}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section className="card p-6 space-y-3">
        <h2 className="font-semibold text-white">Tech Stack</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm text-slate-400">
          {[
            'FastAPI + Python 3.10',
            'TensorFlow 2.15',
            'MediaPipe Holistic',
            'React 18 + Vite',
            'TailwindCSS',
            'WebSocket (live)',
            'SQLite + SQLAlchemy',
            'Celery + Redis',
            'Docker Compose',
          ].map(t => (
            <div key={t} className="flex items-center gap-1.5">
              <div className="w-1 h-1 rounded-full bg-blue-400 flex-shrink-0" />
              {t}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
