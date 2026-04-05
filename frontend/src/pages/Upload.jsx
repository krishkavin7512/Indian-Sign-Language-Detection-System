import { useState } from 'react'
import VideoUpload from '../components/VideoUpload'
import TranscriptViewer from '../components/TranscriptViewer'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function Upload() {
  const [result, setResult] = useState(null)
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">{t.upload.title}</h1>
        <p className="text-slate-400 text-sm mt-1">{t.upload.subtitle}</p>
      </div>
      <div className="space-y-6">
        <div className="card p-6">
          <VideoUpload onComplete={setResult} />
        </div>
        {result && <TranscriptViewer result={result} />}
      </div>
    </div>
  )
}
