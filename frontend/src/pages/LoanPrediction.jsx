import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { apiPost } from '../api/client'
import { FIELD_SECTIONS, ALL_FIELDS, SLIDER_FIELDS } from '../utils/constants'
import { gradeColor, gradeBg, fmt$ } from '../utils/helpers'
import DonutGauge from '../components/DonutGauge'
import ShapBars from '../components/ShapBars'
import IntentChip from '../components/IntentChip'
import { Loader2, Sparkles, Send, ChevronRight, AlertCircle } from 'lucide-react'

// Typewriter streaming
function useTypewriter(text, speed = 10) {
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
      if (idxRef.current >= text.length) { clearInterval(tick); setDone(true) }
    }, speed)
    return () => clearInterval(tick)
  }, [text, speed])
  return { displayed, done }
}

function AiStreamBubble({ content, intent, isLatest }) {
  const { displayed, done } = useTypewriter(isLatest ? content : null, 10)
  const text = isLatest ? displayed : content
  return (
    <div className="bubble bubble-ai">
      {intent && <IntentChip intent={intent}/>}
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>
        {text}
        {isLatest && !done && <span style={{ opacity: 0.5, animation: 'pulse 1s ease infinite', display: 'inline-block', marginLeft: 2 }}>▋</span>}
      </div>
    </div>
  )
}

function SliderInput({ field, value, onChange }) {
  const s = SLIDER_FIELDS[field.k]
  const formatted = s?.fmt ? s.fmt(value) : value
  return (
    <div className="slider-group">
      <div className="slider-header">
        <label className="slider-label">{field.label}</label>
        <span className="slider-val">{formatted}</span>
      </div>
      <input
        type="range" className="slider"
        min={s.min} max={s.max} step={s.step || field.step || 1}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
      />
      <div className="slider-range">
        <span>{s.minLabel || s.min}</span>
        <span>{s.maxLabel || s.max}</span>
      </div>
    </div>
  )
}

const SECT_HINT = {
  personal: 'Employment & ownership info',
  loan: 'Amount, term, rate & purpose',
  financial: 'Income, DTI & utilization',
  credit: 'Grade, records & bankruptcies',
}

export default function LoanPrediction() {
  const { state, dispatch } = useApp()
  const [active, setActive] = useState('personal')
  const [vals, setVals] = useState(() => {
    const v = {}; ALL_FIELDS.forEach(f => v[f.k] = f.default); return v
  })
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [aiOpen, setAiOpen] = useState(false)
  const [aiInp, setAiInp] = useState('')
  const [aiLoad, setAiLoad] = useState(false)
  const resRef = useRef(null)

  const set = (k, v) => setVals(p => ({ ...p, [k]: v }))

  const run = async () => {
    setLoading(true); setErr('')
    const applicant = { ...vals }
    if (applicant.term) applicant.term = parseInt(applicant.term)
    try {
      const data = await apiPost(state.apiBase, '/api/v1/decision', {
        applicant, question: 'Summarize decision.', session_id: state.sessionId
      })
      dispatch({ type: 'PREDICT', payload: { applicant, prediction: data.prediction } })
      dispatch({ type: 'ADD_HIST', payload: {
        type: 'decision',
        applicant_label: `Applicant · ${applicant.sub_grade}`,
        sub_grade: applicant.sub_grade,
        loan_amnt: applicant.loan_amnt,
        prediction: data.prediction.prediction,
        repayment: data.prediction.repayment_probability,
        default: data.prediction.default_probability,
        ts: Date.now() / 1000
      }})
      setTimeout(() => resRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200)
    } catch(e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const askAI = async q => {
    if (!q.trim()) return
    dispatch({ type: 'ADD_DC', payload: { role: 'user', content: q } })
    setAiLoad(true)
    try {
      const data = await apiPost(state.apiBase, '/api/v1/query', { question: q, session_id: state.sessionId })
      const intent = data.intent || 'GENERAL'
      dispatch({ type: 'ADD_DC', payload: { role: 'assistant', content: data.answer || 'No response.', intent } })
      dispatch({ type: 'ADD_HIST', payload: { type: 'ai_turn', intent, summary: q, ts: Date.now() / 1000 } })
    } catch(e) {
      dispatch({ type: 'ADD_DC', payload: { role: 'assistant', content: `Error: ${e.message}` } })
    } finally { setAiLoad(false) }
  }

  const pred = state.lastPrediction
  const approved = pred?.prediction === 'Approved'
  const sect = FIELD_SECTIONS.find(s => s.id === active)
  const dcMsgs = state.decisionChat
  const lastAiIdx = dcMsgs.reduce((acc, m, i) => m.role === 'assistant' ? i : acc, -1)

  return (
    <div>
      <div className="ph">
        <div className="ph-eyebrow">ML Credit Assessment</div>
        <h1 className="ph-title">Loan Prediction</h1>
        <p className="ph-sub">Fill all 4 sections and run the model for an instant AI-powered credit decision with SHAP explainability.</p>
      </div>

      <div className="pred-wrap">
        {/* Sticky section nav */}
        <div className="pred-nav">
          <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-3)', padding: '2px 10px 10px' }}>Sections</div>
          {FIELD_SECTIONS.map((s, i) => (
            <button key={s.id} className={`pred-item ${active === s.id ? 'active' : ''}`} onClick={() => setActive(s.id)}>
              <div className="pred-step">{i + 1}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13 }}>{s.label}</div>
                <div style={{ fontSize: 10.5, color: 'var(--text-3)', fontWeight: 400, marginTop: 1 }}>{SECT_HINT[s.id]}</div>
              </div>
              {active === s.id && <ChevronRight size={12} style={{ color: 'var(--blue)', flexShrink: 0 }}/>}
            </button>
          ))}
          <div className="pred-divider"/>
          {err && (
            <div style={{ background: 'var(--red-dim)', border: '1px solid var(--red-border)', color: 'var(--red)', borderRadius: 8, padding: '8px 11px', fontSize: 12, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertCircle size={12}/>{err}
            </div>
          )}
          <button className="btn btn-primary btn-block" onClick={run} disabled={loading}>
            {loading ? <><Loader2 size={14} className="spin"/>Running…</> : <><Sparkles size={14}/>Run Prediction</>}
          </button>
          {pred && (
            <button className="btn btn-block" style={{ marginTop: 8, background: 'var(--purple-dim)', borderColor: 'var(--purple-border)', color: 'var(--purple)' }}
              onClick={() => setAiOpen(o => !o)}>
              <Sparkles size={13}/>{aiOpen ? 'Hide AI' : 'Ask AI'}
            </button>
          )}
        </div>

        {/* Main form + results */}
        <div>
          <div className="card mb16">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 16, color: 'var(--text)', letterSpacing: '-0.01em' }}>{sect.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 3 }}>{SECT_HINT[sect.id]}</div>
              </div>
              <div style={{ display: 'flex', gap: 5 }}>
                {FIELD_SECTIONS.map((s, i) => (
                  <button key={s.id} className={`btn btn-sm ${active === s.id ? 'btn-primary' : ''}`} onClick={() => setActive(s.id)}>{i + 1}</button>
                ))}
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 20px' }}>
              {sect.fields.map(f => (
                SLIDER_FIELDS[f.k]
                  ? <SliderInput key={f.k} field={f} value={vals[f.k]} onChange={v => set(f.k, v)}/>
                  : (
                    <div key={f.k} className="form-group" style={{ marginBottom: 10 }}>
                      <label className="form-label">{f.label}</label>
                      {f.type === 'select'
                        ? <select className="form-select" value={vals[f.k]} onChange={e => set(f.k, f.options.includes(Number(e.target.value)) ? Number(e.target.value) : e.target.value)}>
                            {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                          </select>
                        : <input className="form-input" type="number" step={f.step || 1} value={vals[f.k]} onChange={e => set(f.k, parseFloat(e.target.value) || 0)}/>
                      }
                    </div>
                  )
              ))}
            </div>
          </div>

          {/* Results */}
          {pred && (
            <div ref={resRef}>
              <div className="g2 mb16">
                <div className={approved ? 'result-approved' : 'result-rejected'}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: approved ? 'var(--em)' : 'var(--red)', marginBottom: 8 }}>ML Decision</div>
                  <div style={{ fontSize: 32, fontWeight: 800, color: approved ? 'var(--em)' : 'var(--red)', marginBottom: 18, letterSpacing: '-0.03em' }}>{pred.prediction}</div>
                  <div style={{ display: 'flex', gap: 28 }}>
                    <div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text)' }}>{(pred.repayment_probability * 100).toFixed(1)}%</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 }}>Repayment Prob.</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: pred.default_probability > 0.4 ? 'var(--red)' : 'var(--text)' }}>{(pred.default_probability * 100).toFixed(1)}%</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 }}>Default Risk</div>
                    </div>
                  </div>
                </div>
                <div className="card" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--text-3)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence Score</div>
                  <DonutGauge pct={Math.max(pred.repayment_probability, pred.default_probability) * 100} color={approved ? '#10B981' : '#F25757'} size={100}/>
                </div>
              </div>

              <div className="card mb16">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div style={{ fontWeight: 800, fontSize: 14, color: 'var(--text)' }}>Top Risk Drivers</div>
                  <span style={{ fontSize: 11, color: 'var(--text-3)', background: 'var(--surface-2)', padding: '3px 9px', borderRadius: 999, border: '1px solid var(--border-2)' }}>SHAP values</span>
                </div>
                <ShapBars features={pred.top_features || []}/>
              </div>

              {aiOpen && (
                <div className="ai-panel">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--blue-dim)', border: '1px solid var(--blue-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Sparkles size={14} color="var(--blue)"/>
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>AI Decision Assistant</div>
                        <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Context-aware · Streams responses</div>
                      </div>
                    </div>
                  </div>
                  {dcMsgs.length === 0 && (
                    <div className="chip-row">
                      {[`Why was this ${pred.prediction.toLowerCase()}?`, 'What would improve approval odds?', 'Simulate +30% income']
                        .map((c, i) => <button key={i} className="chip" onClick={() => askAI(c)}>{c}</button>)}
                    </div>
                  )}
                  <div className="chat-wrap">
                    {dcMsgs.map((m, i) => (
                      <div key={i} className={`chat-row ${m.role === 'user' ? 'user' : ''}`}>
                        {m.role === 'assistant' && (
                          <div className="chat-av" style={{ background: 'var(--blue)' }}><Sparkles size={11}/></div>
                        )}
                        {m.role === 'user'
                          ? <div className="bubble bubble-user">{m.content}</div>
                          : <AiStreamBubble content={m.content} intent={m.intent} isLatest={i === lastAiIdx}/>
                        }
                      </div>
                    ))}
                    {aiLoad && (
                      <div className="chat-row">
                        <div className="chat-av" style={{ background: 'var(--blue)' }}><Sparkles size={11}/></div>
                        <div className="bubble bubble-ai" style={{ color: 'var(--text-3)', display: 'flex', gap: 8, alignItems: 'center' }}>
                          <Loader2 size={13} className="spin"/>Analyzing decision…
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="chat-bar">
                    <input className="chat-inp" placeholder="Ask about this decision…" value={aiInp}
                      onChange={e => setAiInp(e.target.value)} disabled={aiLoad}
                      onKeyDown={e => { if(e.key==='Enter'&&aiInp.trim()&&!aiLoad){const q=aiInp;setAiInp('');askAI(q)} }}/>
                    <button className="chat-send" disabled={aiLoad||!aiInp.trim()} onClick={() => {const q=aiInp;setAiInp('');askAI(q)}}>
                      <Send size={14}/>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
