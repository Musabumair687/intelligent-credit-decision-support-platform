export default function Sparkline({values=[],color='#10B981',w=64,h=22}) {
  if(!values||values.length<2) return <svg width={w} height={h}><line x1="3" y1={h/2} x2={w-3} y2={h/2} stroke={color} strokeWidth="1.5" strokeDasharray="3,3" opacity="0.3"/></svg>
  const lo=Math.min(...values),hi=Math.max(...values),rng=(hi-lo)||1,n=values.length
  const pts=values.map((v,i)=>`${(3+(w-6)*(i/(n-1))).toFixed(1)},${(h-3-(h-6)*((v-lo)/rng)).toFixed(1)}`).join(' ')
  return <svg width={w} height={h}><polyline points={pts} fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
}
