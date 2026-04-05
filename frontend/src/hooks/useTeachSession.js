import { useRef, useCallback, useState } from 'react'
import { useCamera } from './useCamera'
import { useRecognitionStore } from '../store/recognitionStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const FRAME_MS = 100  // 10 fps during recording

/**
 * Phases:
 *  idle → connecting → ready → (recording → captured)×N → complete | error
 * On failure of a sample: back to ready (retry that sample)
 */
export function useTeachSession() {
  const camera = useCamera()
  const wsRef = useRef(null)
  const timerRef = useRef(null)
  const setLandmarks = useRecognitionStore(s => s.setLandmarks)

  const [phase, setPhase] = useState('idle')
  const [currentSample, setCurrentSample] = useState(0)
  const [totalSamples, setTotalSamples] = useState(4)
  const [landmarkFrames, setLandmarkFrames] = useState(0)
  const [result, setResult] = useState(null)   // {label, labelHindi, samplesRecorded}
  const [error, setError] = useState(null)
  const [failReason, setFailReason] = useState(null)

  const stopFrames = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }, [])

  const startFrames = useCallback(() => {
    stopFrames()
    timerRef.current = setInterval(async () => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) return
      const buf = await camera.captureFrameAsArrayBuffer()
      if (buf) wsRef.current.send(buf)
    }, FRAME_MS)
  }, [camera, stopFrames])

  const connect = useCallback(async ({ label, labelHindi, samples = 4 }) => {
    setError(null); setResult(null); setFailReason(null)
    setPhase('connecting')
    await camera.start()

    const ws = new WebSocket(`${WS_URL}/ws/teach`)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ label, label_hindi: labelHindi, samples }))
    }

    ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data)
      switch (msg.type) {
        case 'teach_ready':
          setTotalSamples(msg.total_samples)
          setCurrentSample(0)
          setPhase('ready')
          break
        case 'recording':
          setCurrentSample(msg.current)
          setFailReason(null)
          setPhase('recording')
          startFrames()
          break
        case 'sample_captured':
          stopFrames()
          setCurrentSample(msg.count)
          setLandmarkFrames(msg.landmark_frames)
          setPhase(msg.count < msg.total ? 'captured' : 'captured')
          break
        case 'sample_failed':
          stopFrames()
          setFailReason(msg.reason)
          setPhase('ready')   // let user retry
          break
        case 'teaching_complete':
          stopFrames()
          setResult({ label: msg.label, labelHindi: msg.label_hindi, samplesRecorded: msg.samples_recorded })
          setPhase('complete')
          break
        case 'landmark':
          setLandmarks(msg.data)
          break
        case 'error':
          stopFrames()
          setError(msg.message)
          setPhase('error')
          break
        default: break
      }
    }

    ws.onerror = () => { stopFrames(); setError('WebSocket error'); setPhase('error') }
    ws.onclose = () => stopFrames()
  }, [camera, startFrames, stopFrames])

  const beginSample = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'begin_sample' }))
    }
  }, [])

  const reset = useCallback(() => {
    stopFrames()
    wsRef.current?.close()
    wsRef.current = null
    camera.stop()
    setPhase('idle')
    setCurrentSample(0)
    setResult(null)
    setError(null)
    setFailReason(null)
  }, [camera, stopFrames])

  return {
    videoRef: camera.videoRef,
    canvasRef: camera.canvasRef,
    isActive: camera.isActive,
    phase,
    currentSample,
    totalSamples,
    landmarkFrames,
    result,
    error,
    failReason,
    connect,
    beginSample,
    reset,
  }
}
