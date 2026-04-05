import { useEffect, useRef, useCallback } from 'react'
import { useCamera } from './useCamera'
import { useWebSocket } from './useWebSocket'
import { useRecognitionStore } from '../store/recognitionStore'

const FRAME_INTERVAL_MS = 100  // Send ~10 fps to backend

export function useRecognition() {
  const camera = useCamera()
  const ws = useWebSocket()
  const intervalRef = useRef(null)
  const { isStreaming, setStreaming } = useRecognitionStore()

  const startStreaming = useCallback(async () => {
    await camera.start()
    ws.connect()
    // Give WS a moment to establish before sending frames
    setTimeout(() => {
      intervalRef.current = setInterval(async () => {
        const buf = await camera.captureFrameAsArrayBuffer()
        if (buf) ws.sendFrame(buf)
      }, FRAME_INTERVAL_MS)
      setStreaming(true)
    }, 500)
  }, [camera, ws, setStreaming])

  const stopStreaming = useCallback(() => {
    clearInterval(intervalRef.current)
    intervalRef.current = null
    camera.stop()
    ws.disconnect()
    setStreaming(false)
  }, [camera, ws, setStreaming])

  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current)
    }
  }, [])

  return {
    ...camera,
    wsStatus: ws.status,
    isStreaming,
    startStreaming,
    stopStreaming,
  }
}
