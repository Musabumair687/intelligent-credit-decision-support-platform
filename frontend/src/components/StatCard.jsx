import Sparkline from './Sparkline'
export default function StatCard({label,value,color='#10B981',bg='rgba(16,185,129,0.12)',icon,spark=[]}) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{background:bg}}>{icon}</div>
      <div className="stat-value">{value}</div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:6}}>
        <div className="stat-label">{label}</div>
        <Sparkline values={spark.slice(-8)} color={color} w={56} h={18}/>
      </div>
    </div>
  )
}
