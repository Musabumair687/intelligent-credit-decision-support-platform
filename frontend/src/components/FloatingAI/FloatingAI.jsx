import { useState, useEffect, useRef } from 'react'
import { useApp } from '../../context/AppContext'
import { apiPost } from '../../api/client'
import { INTENT_META } from '../../utils/constants'
import IntentChip from '../IntentChip'
import ShapBars from '../ShapBars'
import { Sparkles, X, Send, Loader2 } from 'lucide-react'
import './FloatingAI.css'

export default function FloatingAI() {
  const { state, dispatch } = useApp()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [intentStatus, setIntentStatus] = useState(null)
  const chatEndRef = useRef(null)

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [state.decisionChat, loading])

  const hasPrediction = state.lastPrediction !== null

  const defaultChips = hasPrediction
    ? [
        `Why was this applicant ${state.lastPrediction?.prediction?.toLowerCase()}?`,
        'What would improve this applicant\'s chances?',
        'What if annual income increases by 30%?',
      ]
    : [
        'What is the maximum allowed DTI?',
        'What does Sub-Grade B3 mean?',
        'What are the conditions for a policy exception?',
      ]

  const askQuestion = async (question) => {
    dispatch({ type: 'ADD_DECISION_CHAT', payload: { role: 'user', content: question } })
    setLoading(true)
    setIntentStatus('identifying')

    try {
      const data = await apiPost(state.apiBase, '/api/v1/query', {
        question,
        session_id: state.sessionId,
      })

      const intent = data.intent || 'GENERAL'
      setIntentStatus(intent)

      const answer = data.answer || 'No response returned.'
      const extra = extractExtra(intent, data)

      setTimeout(() => {
        dispatch({
          type: 'ADD_DECISION_CHAT',
          payload: { role: 'assistant', content: answer, intent, extra },
        })
        dispatch({
          type: 'ADD_HISTORY',
          payload: { type: 'ai_turn', intent, summary: question, ts: Date.now() / 1000 },
        })
        setLoading(false)
        setIntentStatus(null)
      }, 400)
    } catch (err) {
      dispatch({
        type: 'ADD_DECISION_CHAT',
        payload: { role: 'assistant', content: `Sorry — that request failed: ${err.message}` },
      })
      setLoading(false)
      setIntentStatus(null)
    }
  }

  const extractExtra = (intent, data) => {
    if (intent === 'SIMULATION' && data.simulation) {
      return { simulation: data.simulation }
    }
    if (intent === 'KNOWLEDGE' && data.retrieved_documents) {
      const sources = data.retrieved_documents.map(d => {
        const meta = d.document?.metadata || {}
        const src = String(meta.source || '').replace(/\\/g, '/').split('/').pop()
        const page = meta.page_label || meta.page || '?'
        return `${src} · p.${page}`
      })
      return { sources }
    }
    if (intent === 'DECISION' && data.prediction?.top_features) {
      return { top_features: data.prediction.top_features }
    }
    return null
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    askQuestion(q)
  }

  const handleChip = (chip) => {
    askQuestion(chip)
  }

  return (
    <>
      {/* Floating Action Button */}
      <button className="ai-fab" onClick={() => setOpen(true)} title="Ask AI">
        <Sparkles size={22} />
      </button>

      {/* Modal */}
      {open && (
        <div className="ai-overlay" onClick={(e) => { if (e.target === e.currentTarget) setOpen(false) }}>
          <div className="ai-modal animate-slide-up">
            {/* Header */}
            <div className="ai-modal-header">
              <div className="ai-modal-title">
                <Sparkles size={18} className="ai-modal-title-icon" />
                Ask AI — Decision Intelligence
              </div>
              <button className="ai-modal-close" onClick={() => setOpen(false)}>
                <X size={18} />
              </button>
            </div>

            {/* Chat Area */}
            <div className="ai-chat-area">
              {/* Greeting */}
              {state.decisionChat.length === 0 && (
                <div className="ai-greeting">
                  <div className="ai-avatar">
                    <Sparkles size={16} />
                  </div>
                  <div className="ai-greeting-bubble">
                    {hasPrediction ? (
                      <>
                        Hi — I'm your AI Decision Assistant.<br />
                        This applicant was <strong>{state.lastPrediction.prediction}</strong>.
                        Ask me why, what would change the outcome, or a policy question —
                        I'll figure out which one automatically.
                      </>
                    ) : (
                      <>
                        Hi — I'm your AI Decision Assistant.<br />
                        No prediction is on file yet, so I can answer general bank-policy
                        questions right now. Run a prediction from <strong>Loan Prediction</strong> to
                        ask about a specific decision.
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Suggestion chips */}
              {state.decisionChat.length === 0 && (
                <div className="ai-chips">
                  {defaultChips.map((chip, i) => (
                    <button key={i} className="ai-chip" onClick={() => handleChip(chip)}>
                      {chip}
                    </button>
                  ))}
                </div>
              )}

              {/* Messages */}
              {state.decisionChat.map((msg, i) => (
                <div key={i} className={`ai-message ai-message-${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="ai-avatar-sm">
                      <Sparkles size={12} />
                    </div>
                  )}
                  <div className={`ai-bubble ai-bubble-${msg.role}`}>
                    {msg.role === 'assistant' && msg.intent && (
                      <IntentChip intent={msg.intent} />
                    )}
                    <div className="ai-bubble-text">{msg.content}</div>
                    {msg.extra && renderExtra(msg.extra)}
                  </div>
                </div>
              ))}

              {/* Loading */}
              {loading && (
                <div className="ai-message ai-message-assistant">
                  <div className="ai-avatar-sm">
                    <Sparkles size={12} />
                  </div>
                  <div className="ai-bubble ai-bubble-assistant">
                    <div className="ai-loading">
                      <Loader2 size={14} className="animate-spin" />
                      <span>
                        {intentStatus === 'identifying'
                          ? 'Identifying intent…'
                          : `Identified: ${INTENT_META[intentStatus]?.label || 'Processing'}…`}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <form className="ai-input-bar" onSubmit={handleSubmit}>
              <input
                type="text"
                className="ai-input"
                placeholder="Ask a question…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button type="submit" className="ai-send" disabled={loading || !input.trim()}>
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

function renderExtra(extra) {
  if (extra.simulation) {
    const { original, simulation, comparison } = extra.simulation
    const diff = comparison?.default_probability_difference || 0
    const delta = diff === 0 ? ['No change', '#9CA3AF']
      : diff > 0 ? ['Higher risk', '#F87171']
      : ['Lower risk', '#34D399']

    return (
      <div className="ai-sim-compare">
        {[['Current', original], ['Simulated', simulation]].map(([label, res]) => {
          if (!res) return null
          return (
            <div key={label} className="ai-sim-card">
              <div className="ai-sim-label">{label}</div>
              <span className={`badge ${res.prediction === 'Approved' ? 'badge-approved' : 'badge-rejected'}`}
                style={{ fontSize: 11, padding: '4px 10px' }}>
                {res.prediction || '—'}
              </span>
              <div className="ai-sim-stats">
                <div>
                  <div className="font-bold">{((res.repayment_probability || 0) * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted">Repay</div>
                </div>
                <div>
                  <div className="font-bold">{((res.default_probability || 0) * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted">Default</div>
                </div>
              </div>
            </div>
          )
        })}
        <span className="ai-sim-delta" style={{ background: `${delta[1]}22`, color: delta[1] }}>
          {delta[0]}
        </span>
      </div>
    )
  }

  if (extra.sources) {
    return (
      <div className="ai-sources">
        {extra.sources.map((s, i) => (
          <span key={i} className="source-chip">{s}</span>
        ))}
      </div>
    )
  }

  if (extra.top_features) {
    return <ShapBars features={extra.top_features} onLight />
  }

  return null
}
