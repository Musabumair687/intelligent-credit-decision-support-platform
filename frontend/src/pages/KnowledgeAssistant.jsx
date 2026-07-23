import { useState, useRef, useEffect, useCallback } from 'react'
import { useApp } from '../context/AppContext'
import { apiPost } from '../api/client'
import { BookOpen, Send, Loader2 } from 'lucide-react'

const CHIPS = [
  'What is the maximum allowed DTI ratio?',
  'What does Sub-Grade B3 mean for interest rates?',
  'What are the conditions for a policy exception?',
  'What FICO score range does Grade A require?',
  'How are bankruptcies handled in credit assessment?',
]

// Typewriter streaming hook
function useTypewriter(text, speed = 12) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const idxRef = useRef(0)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    idxRef.current = 0
    if (!text) { setDone(true); return }
    const tick = setInterval(() => {
      idxRef.current += 1
      setDisplayed(text.slice(0, idxRef.current))
      if (idxRef.current >= text.length) {
        clearInterval(tick)
        setDone(true)
      }
    }, speed)
    return () => clearInterval(tick)
  }, [text, speed])

  return { displayed, done }
}

// Streaming message bubble
function StreamBubble({ content, sources, isLatest }) {
  const { displayed, done } = useTypewriter(isLatest ? content : null, 10)
  const text = isLatest ? displayed : content
  return (
    <div className="bubble bubble-em">
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>
        {text}
        {isLatest && !done && <span style={{ opacity: 0.5, animation: 'pulse 1s ease infinite', display: 'inline-block', marginLeft: 2 }}>▋</span>}
      </div>
      {(done || !isLatest) && sources?.length > 0 && (
        <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--em-border)' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--em)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Sources</div>
          {sources.map((s, j) => <span key={j} className="source-chip">{s}</span>)}
        </div>
      )}
    </div>
  )
}

export default function KnowledgeAssistant() {
  const { state, dispatch } = useApp()
  const [inp, setInp] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.kbChat])

  const ask = useCallback(async q => {
    if (!q.trim() || loading) return
    dispatch({ type: 'ADD_KB', payload: { role: 'user', content: q } })
    setLoading(true)
    try {
      const data = await apiPost(state.apiBase, '/api/v1/knowledge', { question: q, session_id: state.sessionId })
      const sources = (data.retrieved_documents || []).map(d => {
        const m = d.document?.metadata || {}
        return `${String(m.source || '').replace(/\\/g, '/').split('/').pop()} · p.${m.page_label || m.page || '?'}`
      })
      dispatch({ type: 'ADD_KB', payload: { role: 'assistant', content: data.answer || 'No answer found.', sources } })
    } catch(e) {
      dispatch({ type: 'ADD_KB', payload: { role: 'assistant', content: `Error: ${e.message}`, sources: [] } })
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [loading, state.apiBase, state.sessionId, dispatch])

  const msgs = state.kbChat
  const lastAiIdx = msgs.reduce((acc, m, i) => m.role === 'assistant' ? i : acc, -1)

  return (
    <div>
      <div className="ph">
        <div className="ph-eyebrow">Policy Intelligence</div>
        <h1 className="ph-title">Knowledge Assistant</h1>
        <p className="ph-sub">Query Stratum Capital Bank policy documents — 17 chapters of lending policy and compliance guidelines. Answers stream in real-time with cited sources.</p>
      </div>

      <div style={{ maxWidth: 860 }}>
        {/* Suggested chips */}
        {msgs.length === 0 && (
          <>
            <div className="chip-row">
              {CHIPS.map((c, i) => (
                <button key={i} className="chip" onClick={() => ask(c)} disabled={loading}>{c}</button>
              ))}
            </div>
            <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--em-dim)', border: '1px solid var(--em-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
                <BookOpen size={24} color="var(--em)"/>
              </div>
              <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text)', marginBottom: 6 }}>Policy Knowledge Base</div>
              <div style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1.65, maxWidth: 400, margin: '0 auto' }}>
                Ask any question about Stratum Capital Bank lending policies, compliance requirements, or credit guidelines. Answers include page-level citations.
              </div>
            </div>
          </>
        )}

        {/* Chat messages */}
        {msgs.length > 0 && (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="chat-wrap" style={{ padding: '20px 20px 0', maxHeight: 480 }}>
              {msgs.map((m, i) => (
                <div key={i} className={`chat-row ${m.role === 'user' ? 'user' : ''}`}>
                  {m.role === 'assistant' && (
                    <div className="chat-av" style={{ background: 'var(--em)', flexShrink: 0 }}>
                      <BookOpen size={12}/>
                    </div>
                  )}
                  {m.role === 'user' ? (
                    <div className="bubble bubble-user">{m.content}</div>
                  ) : (
                    <StreamBubble
                      content={m.content}
                      sources={m.sources}
                      isLatest={i === lastAiIdx}
                    />
                  )}
                </div>
              ))}
              {loading && (
                <div className="chat-row">
                  <div className="chat-av" style={{ background: 'var(--em)' }}><BookOpen size={12}/></div>
                  <div className="bubble bubble-em" style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--text-3)' }}>
                    <Loader2 size={13} className="spin"/>
                    Searching policy database…
                  </div>
                </div>
              )}
              <div ref={endRef}/>
            </div>

            {/* Chips after conversation */}
            {msgs.length > 0 && !loading && (
              <div style={{ padding: '12px 20px 0' }}>
                <div className="chip-row" style={{ marginBottom: 0 }}>
                  {CHIPS.slice(0, 3).map((c, i) => (
                    <button key={i} className="chip" onClick={() => ask(c)} style={{ fontSize: 11.5 }}>{c}</button>
                  ))}
                </div>
              </div>
            )}

            <div className="chat-bar" style={{ padding: '12px 20px 16px' }}>
              <input
                ref={inputRef}
                className="chat-inp"
                placeholder="e.g. What DTI limit applies to Grade C loans?"
                value={inp}
                onChange={e => setInp(e.target.value)}
                disabled={loading}
                onKeyDown={e => {
                  if (e.key === 'Enter' && inp.trim() && !loading) {
                    const q = inp; setInp(''); ask(q)
                  }
                }}
              />
              <button
                className="chat-send"
                disabled={loading || !inp.trim()}
                onClick={() => { const q = inp; setInp(''); ask(q) }}
              >
                <Send size={14}/>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
