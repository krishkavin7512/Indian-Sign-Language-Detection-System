import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Film, X } from 'lucide-react'
import { motion } from 'framer-motion'
import { uploadVideo, getJobStatus } from '../services/api'
import toast from 'react-hot-toast'
import en from '../translations/en'
import hi from '../translations/hi'
import { useRecognitionStore } from '../store/recognitionStore'

export default function VideoUpload({ onComplete }) {
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle') // idle | uploading | processing | done | error
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.webm'] },
    maxSize: 200 * 1024 * 1024,
    multiple: false,
  })

  const submit = async () => {
    if (!file) return
    try {
      setStatus('uploading')
      const res = await uploadVideo(file, 'auto')
      setJobId(res.job_id)
      setStatus('processing')
      // Poll for job completion
      const poll = setInterval(async () => {
        const job = await getJobStatus(res.job_id)
        setProgress(job.progress)
        if (job.status === 'completed') {
          clearInterval(poll)
          setStatus('done')
          onComplete?.(job.result)
          toast.success('Video processed successfully')
        } else if (job.status === 'failed') {
          clearInterval(poll)
          setStatus('error')
          toast.error(job.error || 'Processing failed')
        }
      }, 1500)
    } catch (err) {
      setStatus('error')
      toast.error(err.message || 'Upload failed')
    }
  }

  const reset = () => {
    setFile(null)
    setJobId(null)
    setProgress(0)
    setStatus('idle')
  }

  return (
    <div className="space-y-4">
      {status === 'idle' && (
        <>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-blue-500 bg-blue-500/5' : 'border-slate-600 hover:border-slate-500'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
            <p className="text-slate-300 font-medium">{t.upload.dropHere}</p>
            <p className="text-slate-500 text-sm mt-1">{t.upload.maxSize}</p>
          </div>

          {file && (
            <div className="flex items-center justify-between bg-slate-800 rounded-lg px-4 py-3">
              <div className="flex items-center gap-3">
                <Film className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={reset} className="text-slate-500 hover:text-red-400"><X className="w-4 h-4" /></button>
                <button onClick={submit} className="btn-primary text-sm py-1">Analyze</button>
              </div>
            </div>
          )}
        </>
      )}

      {(status === 'uploading' || status === 'processing') && (
        <div className="card p-6 space-y-4 text-center">
          <Film className="w-10 h-10 text-blue-400 mx-auto animate-pulse" />
          <p className="text-slate-300">{t.upload.processing}</p>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-blue-500 rounded-full"
              animate={{ width: `${Math.round(progress * 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <p className="text-slate-500 text-sm">{Math.round(progress * 100)}%</p>
        </div>
      )}

      {status === 'done' && (
        <div className="flex items-center gap-3">
          <span className="text-green-400 font-medium">{t.upload.complete}</span>
          <button onClick={reset} className="btn-secondary text-sm py-1">Upload Another</button>
        </div>
      )}
    </div>
  )
}
