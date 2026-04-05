import { useRef, useEffect } from 'react'
import { useRecognitionStore } from '../store/recognitionStore'

const HAND_CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12],
  [0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20],
  [5,9],[9,13],[13,17],
]

const FINGERTIPS = [4, 8, 12, 16, 20]

export default function LandmarkOverlay() {
  const canvasRef = useRef(null)
  const landmarks = useRecognitionStore(s => s.landmarks)
  const isStreaming = useRecognitionStore(s => s.isStreaming)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    if (!landmarks || !isStreaming) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      return
    }

    const parent = canvas.parentElement
    canvas.width = parent.offsetWidth
    canvas.height = parent.offsetHeight
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const drawHand = (points, lineColor, glowColor, tipColor) => {
      if (!points?.length) return
      const W = canvas.width
      const H = canvas.height
      const px = p => [(1 - p.x) * W, p.y * H]

      // Connections with glow
      ctx.save()
      ctx.shadowBlur = 14
      ctx.shadowColor = glowColor
      ctx.strokeStyle = lineColor
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      HAND_CONNECTIONS.forEach(([a, b]) => {
        if (!points[a] || !points[b]) return
        const [ax, ay] = px(points[a])
        const [bx, by] = px(points[b])
        ctx.beginPath()
        ctx.moveTo(ax, ay)
        ctx.lineTo(bx, by)
        ctx.stroke()
      })
      ctx.restore()

      // Joints
      points.forEach((p, i) => {
        const [x, y] = px(p)
        const isTip = FINGERTIPS.includes(i)
        const r = isTip ? 5 : 3

        ctx.save()
        ctx.shadowBlur = isTip ? 22 : 10
        ctx.shadowColor = glowColor
        ctx.fillStyle = isTip ? tipColor : lineColor
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()

        if (isTip) {
          ctx.save()
          ctx.fillStyle = 'rgba(255,255,255,0.9)'
          ctx.beginPath()
          ctx.arc(x, y, 2, 0, Math.PI * 2)
          ctx.fill()
          ctx.restore()
        }
      })
    }

    drawHand(
      landmarks.left_hand,
      'rgba(0,212,255,0.85)',
      'rgba(0,212,255,0.55)',
      '#00d4ff'
    )
    drawHand(
      landmarks.right_hand,
      'rgba(167,139,250,0.85)',
      'rgba(167,139,250,0.55)',
      '#a78bfa'
    )
  }, [landmarks, isStreaming])

  return (
    <canvas
      ref={canvasRef}
      className="landmark-overlay absolute inset-0 w-full h-full"
      style={{ pointerEvents: 'none' }}
    />
  )
}
