export default function DonutGauge({pct,color='#10B981',size=100,stroke=8}) {
  const c=Math.max(0,Math.min(100,pct)),r=(size-stroke)/2
  const circ=2*Math.PI*r,offset=circ*(1-c/100)
  const cx=cy=size/2
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" className="donut-bg" strokeWidth={stroke}/>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={stroke}
        strokeLinecap="round" strokeDasharray={circ.toFixed(2)} strokeDashoffset={offset.toFixed(2)}
        transform={`rotate(-90 ${cx} ${cy})`} className="donut-fill"/>
      <text x={cx} y={cy+7} textAnchor="middle" fontSize="19" fontWeight="700" fill="currentColor" fontFamily="Inter,sans-serif">{c.toFixed(0)}%</text>
    </svg>
  )
}
