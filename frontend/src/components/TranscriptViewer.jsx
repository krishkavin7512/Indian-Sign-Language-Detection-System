import { Download } from 'lucide-react'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function TranscriptViewer({ result }) {
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  if (!result?.transcript?.length) return null

  const downloadCSV = () => {
    const header = 'Timestamp,Label,Label (Hindi),Confidence\n'
    const rows = result.transcript.map(r =>
      `${r.timestamp_str},${r.label},${r.label_hindi || ''},${(r.confidence * 100).toFixed(1)}%`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'isl_transcript.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-200">{t.upload.transcript}</h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-400">{result.total_signs} signs</span>
          <button
            onClick={downloadCSV}
            className="btn-secondary text-xs py-1 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" /> CSV
          </button>
        </div>
      </div>

      <div className="space-y-1 max-h-96 overflow-y-auto">
        {result.transcript.map((item, i) => (
          <div
            key={i}
            className="flex items-center justify-between text-sm py-2 border-b border-slate-700/50 last:border-0"
          >
            <div className="flex items-center gap-3">
              <span className="text-slate-500 font-mono text-xs w-12">{item.timestamp_str}</span>
              <span className="text-slate-200 font-medium">
                {language === 'hi' && item.label_hindi ? item.label_hindi : item.label}
              </span>
              {language === 'en' && item.label_hindi && (
                <span className="text-slate-500 font-hindi text-xs">{item.label_hindi}</span>
              )}
            </div>
            <span className={`text-xs font-medium ${
              item.confidence >= 0.85 ? 'text-green-400' :
              item.confidence >= 0.65 ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {Math.round(item.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
