import { useState, useRef } from 'react'
import { useApp } from '../../context/AppContext'
import { apiPost } from '../../api/client'
import { APPLICANT_FIELDS } from '../../utils/constants'
import LightCard from '../../components/LightCard'
import GlassCard from '../../components/GlassCard'
import DonutGauge from '../../components/DonutGauge'
import ShapBars from '../../components/ShapBars'
import { Loader2, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'
import './LoanPrediction.css'

export default function LoanPrediction() {
  const { state, dispatch } = useApp()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const resultRef = useRef(null)

  // Initialize form values from defaults
  const [formValues, setFormValues] = useState(() => {
    const vals = {}
    APPLICANT_FIELDS.forEach(f => {
      vals[f.k] = f.default
    })
    return vals
  })

  const updateField = (key, value) => {
    setFormValues(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const applicant = { ...formValues }
    if (applicant.term) applicant.term = parseInt(applicant.term)

    try {
      const data = await apiPost(state.apiBase, '/api/v1/decision', {
        applicant,
        question: 'Summarize this applicant\'s decision.',
        session_id: state.sessionId,
      })

      dispatch({
        type: 'SET_PREDICTION',
        payload: { applicant, prediction: data.prediction },
      })

      dispatch({
        type: 'ADD_HISTORY',
        payload: {
          type: 'decision',
          applicant_label: `Applicant · ${applicant.sub_grade}`,
          sub_grade: applicant.sub_grade,
          loan_amnt: applicant.loan_amnt,
          prediction: data.prediction.prediction,
          repayment: data.prediction.repayment_probability,
          default: data.prediction.default_probability,
          ts: Date.now() / 1000,
        },
      })

      // Scroll to result
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 200)
    } catch (err) {
      setError(err.message || 'Prediction failed.')
    } finally {
      setLoading(false)
    }
  }

  const prediction = state.lastPrediction
  const isApproved = prediction?.prediction === 'Approved'
  const badgeColor = isApproved ? '#34D399' : '#F87171'
  const confidence = prediction
    ? Math.max(prediction.repayment_probability, prediction.default_probability) * 100
    : 0

  return (
    <div className="animate-fade-in">
      <h1 className="hero-title">Loan prediction</h1>
      <p className="hero-sub">
        Applicant information — runs the ML model only. No AI explanation is generated here.
      </p>

      {/* Form */}
      <LightCard>
        <form onSubmit={handleSubmit}>
          <div className="predict-form-grid">
            {APPLICANT_FIELDS.map(field => (
              <div key={field.k} className="form-group">
                <label className="form-label">{field.label}</label>
                {field.type === 'select' ? (
                  <select
                    className="form-select"
                    value={formValues[field.k]}
                    onChange={(e) => {
                      const val = field.options.includes(Number(e.target.value))
                        ? Number(e.target.value)
                        : e.target.value
                      updateField(field.k, val)
                    }}
                  >
                    {field.options.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="form-input"
                    type="number"
                    step={field.step || 1}
                    value={formValues[field.k]}
                    onChange={(e) => updateField(field.k, parseFloat(e.target.value) || 0)}
                  />
                )}
              </div>
            ))}
          </div>

          {error && (
            <div className="predict-error">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary predict-submit"
            disabled={loading}
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Running prediction…</>
            ) : (
              <>Predict Loan <ArrowRight size={16} /></>
            )}
          </button>
        </form>
      </LightCard>

      {/* Prediction Result */}
      {prediction && (
        <div ref={resultRef} className="predict-result animate-fade-in mt-24">
          <div className="grid-2 mb-16" style={{ gridTemplateColumns: '1.4fr 1fr' }}>
            <GlassCard>
              <div className="stat-lbl mb-8">Decision</div>
              <div
                className="font-heavy mb-16"
                style={{ fontSize: 28, color: badgeColor }}
              >
                {prediction.prediction}
              </div>
              <div style={{ display: 'flex', gap: 32 }}>
                <div>
                  <div className="font-heavy" style={{ fontSize: 22 }}>
                    {(prediction.repayment_probability * 100).toFixed(1)}%
                  </div>
                  <div className="stat-lbl">Repayment</div>
                </div>
                <div>
                  <div className="font-heavy" style={{ fontSize: 22 }}>
                    {(prediction.default_probability * 100).toFixed(1)}%
                  </div>
                  <div className="stat-lbl">Default risk</div>
                </div>
              </div>
            </GlassCard>

            <GlassCard style={{ textAlign: 'center' }}>
              <div className="stat-lbl mb-12">Confidence</div>
              <DonutGauge pct={confidence} color={badgeColor} size={130} />
            </GlassCard>
          </div>

          <LightCard>
            <div className="font-bold mb-16" style={{ fontSize: 15 }}>Top risk drivers</div>
            <ShapBars features={prediction.top_features || []} onLight />
          </LightCard>

          <p className="predict-hint">
            This is the raw model output. Use the ✦ Ask AI button (bottom right) for
            an explanation, what-if analysis, or policy context.
          </p>
        </div>
      )}
    </div>
  )
}
