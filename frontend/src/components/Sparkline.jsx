export default function Sparkline({ values = [], color, width = 92, height = 30 }) {
  if (!values || values.length < 2) {
    return (
      <svg width={width} height={height}>
        <line x1="4" y1={height / 2} x2={width - 4} y2={height / 2}
          stroke={color} strokeWidth="2" strokeDasharray="3,3" opacity="0.35" />
      </svg>
    )
  }

  const lo = Math.min(...values)
  const hi = Math.max(...values)
  const rng = (hi - lo) || 1
  const n = values.length

  const points = values.map((v, i) => {
    const x = 4 + (width - 8) * (i / (n - 1))
    const y = height - 4 - (height - 8) * ((v - lo) / rng)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')

  return (
    <svg width={width} height={height}>
      <polyline points={points} fill="none" stroke={color}
        strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
