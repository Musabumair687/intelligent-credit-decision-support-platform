export default function DonutGauge({ pct, color, size = 120, stroke = 10 }) {
  const clamped = Math.max(0, Math.min(100, pct))
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c * (1 - clamped / 100)
  const cx = size / 2
  const cy = size / 2

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none"
        stroke="rgba(255,255,255,0.10)" strokeWidth={stroke} />
      <circle cx={cx} cy={cy} r={r} fill="none"
        stroke={color} strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={c.toFixed(2)}
        strokeDashoffset={offset.toFixed(2)}
        transform={`rotate(-90 ${cx} ${cy})`}
        className="donut-fill" />
      <text x={cx} y={cy + 8} textAnchor="middle"
        fontSize="24" fontWeight="800" fill="white"
        fontFamily="Inter, sans-serif">
        {clamped.toFixed(0)}%
      </text>
    </svg>
  )
}
