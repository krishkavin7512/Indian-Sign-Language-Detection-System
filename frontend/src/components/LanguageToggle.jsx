import { useRecognitionStore } from '../store/recognitionStore'

export default function LanguageToggle() {
  const { language, toggleLanguage } = useRecognitionStore()

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors text-sm font-medium"
      title="Toggle language"
    >
      <span className={language === 'en' ? 'text-blue-400' : 'text-slate-400'}>EN</span>
      <span className="text-slate-500">/</span>
      <span className={language === 'hi' ? 'text-blue-400 font-hindi' : 'text-slate-400 font-hindi'}>हि</span>
    </button>
  )
}
