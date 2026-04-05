import { useRef, useState, useCallback, useEffect } from 'react'

export function useCamera() {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const canvasRef = useRef(null)
  const [isActive, setIsActive] = useState(false)
  const [error, setError] = useState(null)

  const start = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setIsActive(true)
    } catch (err) {
      setError(err.message || 'Camera access denied')
      setIsActive(false)
    }
  }, [])

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsActive(false)
  }, [])

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || video.readyState < 2) return null
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    return canvas
  }, [])

  const captureFrameAsBlob = useCallback(() => {
    return new Promise((resolve) => {
      const canvas = captureFrame()
      if (!canvas) { resolve(null); return }
      canvas.toBlob(resolve, 'image/jpeg', 0.85)
    })
  }, [captureFrame])

  const captureFrameAsArrayBuffer = useCallback(async () => {
    const blob = await captureFrameAsBlob()
    if (!blob) return null
    return await blob.arrayBuffer()
  }, [captureFrameAsBlob])

  // If the video element mounts after the stream is already captured (phase timing),
  // attach the stream retroactively so the feed is never black.
  useEffect(() => {
    if (videoRef.current && streamRef.current && !videoRef.current.srcObject) {
      videoRef.current.srcObject = streamRef.current
      videoRef.current.play().catch(() => {})
    }
  })

  useEffect(() => {
    return () => stop()
  }, [stop])

  return {
    videoRef,
    canvasRef,
    isActive,
    error,
    start,
    stop,
    captureFrame,
    captureFrameAsBlob,
    captureFrameAsArrayBuffer,
  }
}
