import { useApp } from '../../context/AppContext'
import GlassCard from '../../components/GlassCard'
import StatCard from '../../components/StatCard'
import Sparkline from '../../components/Sparkline'
import { gradeColor, timeAgo, formatCurrency } from '../../utils/helpers'
import { FileText, BookOpen, ArrowRight, AlertTriangle } from 'lucide-react'
import './Dashboard.css'

export default function Dashboard() {
  const { state, dispatch } = useApp()

  const decisions = state.history.filter(h => h.type === 'decision')
  const aiTurns = state.history.filter(h => h.type === 'ai_turn')
  const approved = decisions.filter(d => d.prediction === 'Approved').length
  const rejected = decisions.filter(d => d.prediction === 'Rejected').length
  const simulations = aiTurns.filter(a => a.intent === 'SIMULATION').length

  const goTo = (page) => {
    dispatch({ type: 'SET_PAGE', payload: page })
    dispatch({ type: 'SET_NAV_GROUP', payload: 'workspace' })
  }

  const recentDecisions = decisions.slice(0, 6)
  const reviewItems = decisions.filter(
    d => d.prediction === 'Rejected' || (d.default > 0.35 && d.default < 0.6)
  ).slice(0, 5)

  return (
    <div className="animate-fade-in">
      <h1 className="hero-title">Welcome back, Loan Officer 👋</h1>
      <p className="hero-sub">How can we help you today?</p>

      {/* CTA Cards */}
      <div className="grid-2 mb-20">
        <GlassCard className="cta-card" onClick={() => goTo('Loan Prediction')}>
          <div className="cta-icon" style={{ background: 'var(--blue-bg)', color: 'var(--blue)' }}>
            <FileText size={22} />
          </div>
          <h3>Loan Prediction</h3>
          <p>Predict a loan outcome using the trained credit risk model.</p>
          <div className="cta-arrow">
            <ArrowRight size={16} />
          </div>
        </GlassCard>

        <GlassCard className="cta-card" onClick={() => goTo('Knowledge Assistant')}>
          <div className="cta-icon" style={{ background: 'var(--green-bg)', color: 'var(--green)' }}>
            <BookOpen size={22} />
          </div>
          <h3>Knowledge Assistant</h3>
          <p>Ask about bank policy, lending guidelines, or credit grading rules.</p>
          <div className="cta-arrow">
            <ArrowRight size={16} />
          </div>
        </GlassCard>
      </div>

      {/* Stats */}
      <div className="grid-5 mb-20">
        <StatCard label="Applications" value={decisions.length} color="#5B8DEF" sparkData={state.probTrend} />
        <StatCard label="Approved" value={approved} color="#34D399" />
        <StatCard label="Rejected" value={rejected} color="#F87171" />
        <StatCard label="AI Conversations" value={aiTurns.length} color="#A78BFA" />
        <StatCard label="Simulations" value={simulations} color="#FBBF24" />
      </div>

      {/* Lower Grid */}
      <div className="grid-split">
        {/* Recent Applications */}
        <GlassCard>
          <div className="font-bold mb-16" style={{ fontSize: 15 }}>Recent applications</div>
          {recentDecisions.length === 0 ? (
            <div className="empty-state">No applications yet this session.</div>
          ) : (
            <div className="dashboard-list">
              {recentDecisions.map((r, i) => (
                <div key={i} className="dashboard-list-item">
                  <div
                    className="dashboard-grade-badge"
                    style={{ background: gradeColor(r.sub_grade) }}
                  >
                    {(r.sub_grade || '—').slice(0, 2)}
                  </div>
                  <div className="dashboard-list-info">
                    <div className="dashboard-list-name">{r.applicant_label}</div>
                    <div className="dashboard-list-meta">
                      {formatCurrency(r.loan_amnt || 0)} · {timeAgo(r.ts)}
                    </div>
                  </div>
                  <span
                    className="pill"
                    style={{
                      background: r.prediction === 'Approved' ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
                      color: r.prediction === 'Approved' ? '#34D399' : '#F87171',
                    }}
                  >
                    {r.prediction}
                  </span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Needs Review */}
        <GlassCard>
          <div className="font-bold mb-16" style={{ fontSize: 15 }}>
            <AlertTriangle size={14} style={{ marginRight: 6, verticalAlign: '-2px' }} />
            Needs manual review
          </div>
          {reviewItems.length === 0 ? (
            <div className="empty-state">Nothing flagged right now.</div>
          ) : (
            <div className="dashboard-list">
              {reviewItems.map((r, i) => (
                <div key={i} className="dashboard-review-item">
                  <div className="font-bold" style={{ fontSize: 13 }}>{r.applicant_label}</div>
                  <div className="text-sm" style={{ color: 'rgba(255,255,255,0.45)' }}>
                    Default risk {(r.default * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
