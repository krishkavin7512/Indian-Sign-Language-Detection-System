import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GraduationCap, Camera, CheckCircle, AlertCircle, ChevronRight, Trash2, RefreshCw, Zap } from 'lucide-react'
import { useTeachSession } from '../hooks/useTeachSession'
import LandmarkOverlay from '../components/LandmarkOverlay'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const fetchCustomSigns = () => axios.get(`${API}/api/teach/signs`).then(r => r.data)
const deleteSign = label => axios.delete(`${API}/api/teach/signs/${label}`)

// ── Step 0 — word form ────────────────────────────────────────────────────────
function WordForm({ onStart }) {
  const [label, setLabel] = useState('')
  const [labelHindi, setLabelHindi] = useState('')
  const [samples, setSamples] = useState(4)

  return (
    <div className="space-y-5">
      <div className="space-y-1.5">
        <label className="text-xs uppercase tracking-wider text-slate-400">Sign Word (English) *</label>
        <input
          value={label}
          onChange={e => setLabel(e.target.value.toUpperCase())}
          placeholder="e.g. NAMASTE"
          className="w-full px-4 py-3 rounded-xl text-white placeholder-slate-500 text-sm font-medium"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
        />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs uppercase tracking-wider text-slate-400">Hindi Label (optional)</label>
        <input
          value={labelHindi}
          onChange={e => setLabelHindi(e.target.value)}
          placeholder="e.g. नमस्ते"
          className="w-full px-4 py-3 rounded-xl text-white placeholder-slate-500 text-sm font-hindi"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
        />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs uppercase tracking-wider text-slate-400">Recordings: {samples}</label>
        <input
          type="range" min={2} max={6} value={samples}
          onChange={e => setSamples(Number(e.target.value))}
          className="w-full accent-cyan-400"
        />
        <p className="text-xs text-slate-500">More recordings = higher accuracy. Recommended: 4</p>
      </div>
      <button
        disabled={!label.trim()}
        onClick={() => onStart({ label: label.trim(), labelHindi, samples })}
        className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
        style={{
          background: 'linear-gradient(135deg, #00d4ff, #6366f1)',
          boxShadow: '0 4px 20px rgba(99,102,241,0.35)',
          color: 'white',
        }}
      >
        <Camera className="w-4 h-4" />
        Start Teaching Session
      </button>
    </div>
  )
}

// ── Sample progress dots ──────────────────────────────────────────────────────
function SampleDots({ current, total }) {
  return (
    <div className="flex items-center gap-2 justify-center">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className="rounded-full transition-all duration-300"
          style={{
            width: i < current ? 10 : 8,
            height: i < current ? 10 : 8,
            background: i < current
              ? 'linear-gradient(135deg, #00d4ff, #6366f1)'
              : 'rgba(255,255,255,0.12)',
            boxShadow: i < current ? '0 0 8px rgba(0,212,255,0.5)' : 'none',
          }}
        />
      ))}
    </div>
  )
}

// ── Main Teach page ───────────────────────────────────────────────────────────
export default function Teach() {
  const session = useTeachSession()
  const qc = useQueryClient()
  const [sessionConfig, setSessionConfig] = useState(null)

  const { data: customSigns } = useQuery({
    queryKey: ['customSigns'],
    queryFn: fetchCustomSigns,
    refetchInterval: 5000,
  })

  const deleteMut = useMutation({
    mutationFn: deleteSign,
    onSuccess: () => qc.invalidateQueries(['customSigns']),
  })

  const handleStart = config => {
    setSessionConfig(config)
    session.connect(config)
  }

  const isRecording = session.phase === 'recording'
  // Show camera for all active phases including connecting
  const showCamera = ['connecting', 'ready', 'captured', 'recording'].includes(session.phase)

  const borderStyle = isRecording
    ? { border: '2px solid rgba(0,212,255,0.7)', boxShadow: '0 0 30px rgba(0,212,255,0.25)', animation: 'detecting-border 1.8s ease-in-out infinite' }
    : { border: '1px solid rgba(255,255,255,0.07)' }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1.5">
          <div style={{ background: 'linear-gradient(135deg, #00d4ff, #6366f1)', borderRadius: 10, padding: 6, boxShadow: '0 0 14px rgba(99,102,241,0.4)' }}>
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Teach a Sign</h1>
        </div>
        <p className="text-slate-400 text-sm">Record a sign 4 times — the AI learns it immediately and recognizes it on the Home page.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left — session */}
        <div className="space-y-4">
          <div className="card p-6">
            <AnimatePresence mode="wait">

              {/* IDLE — show form */}
              {session.phase === 'idle' && (
                <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">New Sign</h2>
                  <WordForm onStart={handleStart} />
                </motion.div>
              )}

              {/* CONNECTING / READY / CAPTURED / RECORDING — camera block */}
              {showCamera && (
                <motion.div key="camera" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                  <div className="flex items-center justify-between">
                    {session.phase === 'recording' ? (
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-sm font-semibold text-white">Recording {session.currentSample}/{session.totalSamples}</span>
                      </div>
                    ) : session.phase === 'connecting' ? (
                      <div className="flex items-center gap-2">
                        <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                        <span className="text-sm text-slate-400">Starting camera…</span>
                      </div>
                    ) : (
                      <h2 className="font-bold text-white">{sessionConfig?.label}</h2>
                    )}
                    {session.phase !== 'connecting' && (
                      <SampleDots current={session.phase === 'recording' ? session.currentSample - 1 : session.currentSample} total={session.totalSamples} />
                    )}
                  </div>

                  {/* Camera viewport */}
                  <div className="relative rounded-xl overflow-hidden" style={{ aspectRatio: '4/3', background: '#020811', ...borderStyle }}>
                    <video
                      ref={session.videoRef}
                      className="w-full h-full object-cover"
                      style={{ transform: 'scaleX(-1)' }}
                      muted playsInline autoPlay
                    />
                    <canvas ref={session.canvasRef} className="hidden" />
                    <LandmarkOverlay />
                    {session.phase === 'connecting' && (
                      <div className="absolute inset-0 flex items-center justify-center" style={{ background: 'rgba(2,8,17,0.6)', backdropFilter: 'blur(4px)' }}>
                        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
                      </div>
                    )}
                    {session.phase === 'recording' && (
                      <div className="absolute inset-0 flex items-end justify-center pb-4">
                        <span className="text-white text-sm font-bold px-4 py-2 rounded-full"
                          style={{ background: 'rgba(239,68,68,0.8)', backdropFilter: 'blur(6px)' }}>
                          Hold sign steady…
                        </span>
                      </div>
                    )}
                  </div>

                  {session.failReason && (
                    <div className="flex items-start gap-2 px-3 py-2 rounded-lg text-xs text-red-300"
                      style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                      <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      {session.failReason}
                    </div>
                  )}

                  {session.phase === 'captured' && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-emerald-400"
                      style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)' }}>
                      <CheckCircle className="w-3.5 h-3.5" />
                      Sample {session.currentSample} captured ({session.landmarkFrames}/45 frames with hands). Relax, then record next.
                    </div>
                  )}

                  {(session.phase === 'ready' || session.phase === 'captured') && (
                    <motion.button whileTap={{ scale: 0.96 }} onClick={session.beginSample}
                      className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2"
                      style={{ background: 'linear-gradient(135deg, #00d4ff, #6366f1)', color: 'white', boxShadow: '0 4px 18px rgba(99,102,241,0.35)' }}>
                      <Zap className="w-4 h-4" />
                      {session.phase === 'captured'
                        ? `Record Sample ${session.currentSample + 1} of ${session.totalSamples}`
                        : `Record Sample 1 of ${session.totalSamples}`}
                    </motion.button>
                  )}

                  <button onClick={session.reset} className="w-full py-2 rounded-xl text-xs text-slate-500 hover:text-slate-300 transition-colors">Cancel</button>
                </motion.div>
              )}

              {/* COMPLETE */}
              {session.phase === 'complete' && (
                <motion.div key="done" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center py-8 gap-4 text-center">
                  <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 30px rgba(16,185,129,0.15)' }}>
                    <CheckCircle className="w-9 h-9 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-extrabold text-gradient">{session.result?.label}</p>
                    {session.result?.labelHindi && <p className="text-slate-400 font-hindi text-lg">{session.result.labelHindi}</p>}
                    <p className="text-slate-400 text-sm mt-2">Learned with {session.result?.samplesRecorded} samples. Go to Home to test it!</p>
                  </div>
                  <div className="flex gap-3 w-full">
                    <button onClick={session.reset} className="flex-1 py-2.5 rounded-xl text-sm font-semibold"
                      style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
                      Teach Another
                    </button>
                    <a href="/" className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-center flex items-center justify-center gap-1"
                      style={{ background: 'linear-gradient(135deg, #00d4ff, #6366f1)', color: 'white' }}>
                      Test it <ChevronRight className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </motion.div>
              )}

              {/* ERROR */}
              {session.phase === 'error' && (
                <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center py-8 gap-4 text-center">
                  <AlertCircle className="w-10 h-10 text-red-400" />
                  <p className="text-red-400 text-sm">{session.error}</p>
                  <button onClick={session.reset} className="btn-primary px-6 py-2 text-sm">Try Again</button>
                </motion.div>
              )}

            </AnimatePresence>
          </div>
        </div>

        {/* Right — custom signs library */}
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Taught Signs{' '}
              {customSigns?.count > 0 && (
                <span style={{ color: 'rgba(0,212,255,0.7)', fontWeight: 700 }}>({customSigns.count})</span>
              )}
            </h2>

            {!customSigns?.signs?.length ? (
              <div className="flex flex-col items-center py-8 gap-2 text-center">
                <GraduationCap className="w-8 h-8" style={{ color: 'rgba(99,102,241,0.3)' }} />
                <p className="text-slate-500 text-sm">No custom signs yet.</p>
                <p className="text-slate-600 text-xs">Taught signs appear here and are recognized instantly.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {customSigns.signs.map(sign => (
                  <motion.div
                    key={sign.label}
                    layout
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="flex items-center justify-between px-4 py-3 rounded-xl"
                    style={{ background: 'rgba(0,212,255,0.05)', border: '1px solid rgba(0,212,255,0.12)' }}
                  >
                    <div>
                      <p className="font-semibold text-sm text-white">{sign.label}</p>
                      {sign.label_hindi && <p className="text-xs text-slate-400 font-hindi">{sign.label_hindi}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                        style={{ background: 'rgba(0,212,255,0.1)', color: '#00d4ff' }}>
                        custom
                      </span>
                      <button
                        onClick={() => deleteMut.mutate(sign.label)}
                        className="p-1.5 rounded-lg transition-all hover:bg-red-500/10"
                        style={{ color: '#475569' }}
                        onMouseEnter={e => e.currentTarget.style.color = '#f87171'}
                        onMouseLeave={e => e.currentTarget.style.color = '#475569'}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* How it works */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">How it works</h2>
            <div className="space-y-3">
              {[
                { n: 1, text: 'Enter the word and optional Hindi label' },
                { n: 2, text: 'Record the sign 4 times — each ~4.5 seconds' },
                { n: 3, text: 'The system averages all 4 recordings as a template' },
                { n: 4, text: 'Custom signs take priority over the 296-word BiLSTM model' },
                { n: 5, text: 'Go to Home → Word mode and perform the sign to test it' },
              ].map(({ n, text }) => (
                <div key={n} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold"
                    style={{ background: 'linear-gradient(135deg, #00d4ff, #6366f1)', color: 'white' }}>
                    {n}
                  </div>
                  <p className="text-slate-400 text-sm">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
