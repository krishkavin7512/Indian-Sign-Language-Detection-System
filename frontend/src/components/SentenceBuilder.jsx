import { Copy, Trash2 } from 'lucide-react'
import { useRecognitionStore } from '../store/recognitionStore'
import toast from 'react-hot-toast'
import en from '../translations/en'
import hi from '../translations/hi'

export default function SentenceBuilder() {
  const { sentence, clearSentence, language } = useRecognitionStore()
  const t = language === 'hi' ? hi : en

  if (sentence.length === 0) return null

  const text = sentence.join(' ')

  const copy = () => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  return (
    <div className="bg-slate-900/50 rounded-lg p-3 space-y-2 border border-slate-700">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{t.output.sentence}</p>
      <p className="text-slate-200 font-medium leading-relaxed">{text}</p>
      <div className="flex gap-2">
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <Copy className="w-3.5 h-3.5" /> {t.output.copySentence}
        </button>
        <button
          onClick={clearSentence}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" /> {t.output.clearSentence}
        </button>
      </div>
    </div>
  )
}
