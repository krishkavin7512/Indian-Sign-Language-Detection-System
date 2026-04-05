import { Camera, CameraOff, WifiOff, Loader2, Zap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import LandmarkOverlay from './LandmarkOverlay'
import ModeSelector from './ModeSelector'
import { useRecognition } from '../hooks/useRecognition'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function CameraPanel() {
  const { videoRef, canvasRef, isActive, error, wsStatus, startStreaming, stopStreaming } = useRecognition()
  const landmarks = useRecognitionStore(s => s.landmarks)
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  const isDetecting = landmarks && (landmarks.left_hand?.length > 0 || landmarks.right_hand?.length > 0)

  const wsColor = wsStatus === 'connected' ? '#34d399'
    : wsStatus === 'connecting' ? '#fbbf24' : '#475569'

  return (
    <div className="card p-4 space-y-4">
      {/* Viewport */}
      <div
        className="relative rounded-xl overflow-hidden"
        style={{
          aspectRatio: '4/3',
          background: '#020811',
          border: isDetecting
            ? '1px solid rgba(0,212,255,0.5)'
            : isActive
            ? '1px solid rgba(255,255,255,0.07)'
            : '1px solid rgba(255,255,255,0.03)',
          boxShadow: isDetecting
            ? '0 0 35px rgba(0,212,255,0.18), inset 0 0 35px rgba(0,212,255,0.03)'
            : 'none',
          transition: 'border-color 0.4s ease, box-shadow 0.4s ease',
        }}
      >
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          style={{ transform: 'scaleX(-1)' }}
          muted
          playsInline
        />
        <canvas ref={canvasRef} className="hidden" />
        <LandmarkOverlay />

        {/* Camera off placeholder */}
        {!isActive && (
          <div className="absolute inset-0 flex flex-col items-center justify-center"
            style={{ background: 'rgba(2,8,17,0.96)' }}>
            <div className="animate-float mb-4">
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: 'rgba(99,102,241,0.1)',
                border: '1px solid rgba(99,102,241,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Camera className="w-7 h-7" style={{ color: 'rgba(99,102,241,0.5)' }} />
              </div>
            </div>
            <p className="text-slate-500 text-sm">{t.home.startCamera}</p>
          </div>
        )}

        {/* WS status pill */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full px-2.5 py-1"
          style={{
            background: 'rgba(5,13,26,0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
          <div className="w-1.5 h-1.5 rounded-full"
            style={{ background: wsColor, boxShadow: `0 0 6px ${wsColor}` }} />
          <span className="text-xs" style={{ color: '#64748b' }}>{wsStatus}</span>
        </div>

        {/* Detecting badge */}
        <AnimatePresence>
          {isDetecting && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="absolute top-3 left-3 flex items-center gap-1.5 rounded-full px-2.5 py-1"
              style={{
                background: 'rgba(0,212,255,0.09)',
                border: '1px solid rgba(0,212,255,0.28)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <Zap className="w-3 h-3" style={{ color: '#00d4ff' }} />
              <span className="text-xs font-semibold" style={{ color: '#00d4ff' }}>detecting</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <div className="absolute bottom-2 left-2 right-2 rounded-lg px-3 py-2 text-xs text-red-300"
            style={{ background: 'rgba(127,29,29,0.85)', backdropFilter: 'blur(8px)' }}>
            {error}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between gap-3">
        <ModeSelector />
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={isActive ? stopStreaming : startStreaming}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap"
          style={isActive ? {
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.28)',
            color: '#f87171',
          } : {
            background: 'linear-gradient(135deg, #00d4ff, #6366f1)',
            border: 'none',
            color: 'white',
            boxShadow: '0 4px 16px rgba(99,102,241,0.35)',
          }}
        >
          {isActive
            ? <><CameraOff className="w-4 h-4" />{t.home.stopCamera}</>
            : <><Camera className="w-4 h-4" />{t.home.startCamera}</>
          }
        </motion.button>
      </div>
    </div>
  )
}
