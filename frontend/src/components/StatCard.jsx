import GlassCard from './GlassCard'
import Sparkline from './Sparkline'
import './StatCard.css'

export default function StatCard({ label, value, color, sparkData = [] }) {
  return (
    <GlassCard className="stat-card">
      <div className="stat-lbl">{label}</div>
      <div className="stat-row">
        <div className="stat-num" style={{ color: color || 'white' }}>{value}</div>
        <Sparkline values={sparkData.slice(-8)} color={color} />
      </div>
    </GlassCard>
  )
}
