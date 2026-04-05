import { useEffect, useRef, useCallback, useState } from 'react'
import { useRecognitionStore } from '../store/recognitionStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket() {
  const wsRef = useRef(null)
  const [status, setStatus] = useState('disconnected') // disconnected | connecting | connected | error
  const { setPrediction, addToHistory, addToSentence, setLandmarks, setConnected, mode } = useRecognitionStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    setStatus('connecting')
    const ws = new WebSocket(`${WS_URL}/ws/recognize/live`)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      setConnected(true)
      ws.send(JSON.stringify({ mode }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        switch (msg.type) {
          case 'prediction':
            if (msg.confidence >= 0.15 || msg.label === '—') setPrediction(msg)
            if (msg.confidence > 0.2 && msg.label !== '—') {
              addToHistory({
                label: msg.label,
                labelHindi: msg.label_hindi,
                confidence: msg.confidence,
                mode: msg.mode,
                modelUsed: msg.model_used,
                timestamp: new Date().toISOString(),
              })
              addToSentence(msg.label)
            }
            break
          case 'landmark':
            setLandmarks(msg.data)
            break
          case 'sentence':
            // handled separately if needed
            break
          case 'error':
            console.error('WS error from server:', msg.message)
            break
          default:
            break
        }
      } catch (e) {
        console.error('Failed to parse WS message', e)
      }
    }

    ws.onerror = () => {
      setStatus('error')
      setConnected(false)
    }

    ws.onclose = () => {
      setStatus('disconnected')
      setConnected(false)
    }
  }, [mode, setPrediction, addToHistory, addToSentence, setLandmarks, setConnected])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const sendFrame = useCallback((frameData) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(frameData)
    }
  }, [])

  useEffect(() => {
    return () => wsRef.current?.close()
  }, [])

  return { connect, disconnect, sendFrame, status }
}
