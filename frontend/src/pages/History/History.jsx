import { useApp } from '../../context/AppContext'
import { INTENT_META } from '../../utils/constants'
import { timeAgo } from '../../utils/helpers'
import LightCard from '../../components/LightCard'
import { Trash2, Clock } from 'lucide-react'
import './History.css'

export default function History() {
  const { state, dispatch } = useApp()

  return (
    <div className="animate-fade-in">
      <div className="history-header">
        <div>
          <h1 className="hero-title">History</h1>
          <p className="hero-sub">Every application and AI conversation this session.</p>
        </div>
        {state.history.length > 0 && (
          <button
            className="btn btn-sm"
            onClick={() => dispatch({ type: 'CLEAR_HISTORY' })}
          >
            <Trash2 size={13} />
            Clear session
          </button>
        )}
      </div>

      <LightCard>
        {state.history.length === 0 ? (
          <div className="history-empty">
            <Clock size={36} strokeWidth={1.5} />
            <p>Nothing recorded yet.</p>
            <p className="text-sm text-muted">Predictions and AI conversations will appear here.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Summary</th>
                <th>Result</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {state.history.map((h, i) => {
                let typeLabel, summary, result
                if (h.type === 'decision') {
                  typeLabel = 'Prediction'
                  summary = h.applicant_label
                  result = h.prediction
                } else {
                  const meta = INTENT_META[h.intent] || INTENT_META.GENERAL
                  typeLabel = meta.label
                  summary = h.summary || '—'
                  result = '—'
                }

                const pillClass = h.type === 'decision'
                  ? (h.prediction === 'Approved' ? 'pill-approved' : 'pill-rejected')
                  : 'pill-pending'

                return (
                  <tr key={i}>
                    <td>
                      <span className={`pill ${pillClass}`}>{typeLabel}</span>
                    </td>
                    <td>{summary}</td>
                    <td>
                      {result !== '—' ? (
                        <span className={`pill ${
                          result === 'Approved' ? 'pill-approved' : result === 'Rejected' ? 'pill-rejected' : 'pill-pending'
                        }`}>
                          {result}
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="text-muted">{timeAgo(h.ts)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </LightCard>
    </div>
  )
}
