import { useState, useEffect, useRef } from 'react'
import { useApp } from '../../context/AppContext'
import { apiPost } from '../../api/client'
import LightCard from '../../components/LightCard'
import { BookOpen, Send, Loader2 } from 'lucide-react'
import './KnowledgeAssistant.css'

const SUGGESTION_CHIPS = [
  'What is the maximum allowed DTI?',
  'What does Sub-Grade B3 mean?',
  'What are the conditions for a policy exception?',
]

export default function KnowledgeAssistant() {
  const { state, dispatch } = useApp()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.kbChat])

  const askKnowledge = async (question) => {
    dispatch({ type: 'ADD_KB_CHAT', payload: { role: 'user', content: question } })
    setLoading(true)

    try {
      const data = await apiPost(state.apiBase, '/api/v1/knowledge', {
        question,
        session_id: state.sessionId,
      })

      const sources = (data.retrieved_documents || []).map(d => {
        const meta = d.document?.metadata || {}
        const src = String(meta.source || '').replace(/\\/g, '/').split('/').pop()
        const page = meta.page_label || meta.page || '?'
        return `${src} · p.${page}`
      })

      dispatch({
        type: 'ADD_KB_CHAT',
        payload: {
          role: 'assistant',
          content: data.answer || 'No answer returned.',
          sources,
        },
      })
    } catch (err) {
      dispatch({
        type: 'ADD_KB_CHAT',
        payload: {
          role: 'assistant',
          content: `Sorry — that request failed: ${err.message}`,
          sources: [],
        },
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    askKnowledge(q)
  }

  return (
    <div className="animate-fade-in">
      <h1 className="hero-title">Knowledge assistant</h1>
      <p className="hero-sub">Standalone bank-policy Q&A — no connection to any prediction.</p>

      <LightCard className="kb-container">
        {/* Suggestion Chips */}
        {state.kbChat.length === 0 && (
          <div className="kb-chips">
            {SUGGESTION_CHIPS.map((chip, i) => (
              <button
                key={i}
                className="kb-chip"
                onClick={() => askKnowledge(chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Empty state */}
        {state.kbChat.length === 0 && !loading && (
          <div className="kb-empty">
            <BookOpen size={32} strokeWidth={1.5} />
            <p>Ask a question about Stratum Capital Bank's lending policy.</p>
          </div>
        )}

        {/* Chat Messages */}
        <div className="kb-messages">
          {state.kbChat.map((msg, i) => (
            <div key={i} className={`kb-message kb-message-${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="kb-avatar">
                  <BookOpen size={14} />
                </div>
              )}
              <div className={`kb-bubble kb-bubble-${msg.role}`}>
                <div className="kb-bubble-text">{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="kb-sources">
                    {msg.sources.map((s, j) => (
                      <span key={j} className="source-chip">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="kb-message kb-message-assistant">
              <div className="kb-avatar">
                <BookOpen size={14} />
              </div>
              <div className="kb-bubble kb-bubble-assistant">
                <div className="kb-loading">
                  <Loader2 size={14} className="animate-spin" />
                  <span>Searching knowledge base…</span>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <form className="kb-input-bar" onSubmit={handleSubmit}>
          <input
            type="text"
            className="kb-input"
            placeholder="e.g. What FICO range does Grade B require?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="kb-send" disabled={loading || !input.trim()}>
            <Send size={16} />
          </button>
        </form>
      </LightCard>
    </div>
  )
}
