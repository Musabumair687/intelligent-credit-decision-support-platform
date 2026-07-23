import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { CREDS } from '../utils/constants'
import { Shield, Eye, EyeOff, AlertCircle, Sun, Moon, TrendingUp, Shield as ShieldIcon } from 'lucide-react'

export default function Login() {
  const { state, dispatch } = useApp()
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [show, setShow] = useState(false)
  const [err, setErr] = useState('')
  const [shk, setShk] = useState(false)
  const dark = state.theme === 'dark'

  const sub = e => {
    e.preventDefault()
    if (u === CREDS.user && p === CREDS.pass) {
      dispatch({ type: 'LOGIN' })
    } else {
      setErr('Invalid username or password.')
      setShk(true)
      setTimeout(() => setShk(false), 500)
    }
  }

  return (
    <div className="login-bg" style={{ display:'flex', minHeight:'100vh' }}>
      {/* Theme toggle */}
      <button className="login-theme-btn" onClick={() => dispatch({ type:'TOGGLE_THEME' })}>
        {dark ? <Sun size={16}/> : <Moon size={16}/>}
      </button>

      {/* Left branding panel */}
      <div className="login-left">
        <div className="login-left-badge">
          <span className="login-left-badge-dot"/>
          Intelligent Credit Platform
        </div>
        <h1>
          Smarter Credit<br/>
          <span>Decisions.</span>
        </h1>
        <p>
          Stratum Capital Bank uses ML-powered analysis and
          explainable AI to help loan officers make data-driven
          credit decisions — faster and more accurately than ever.
        </p>
        <div className="login-stats">
          {[['< 2s', 'Decision Time'], ['17 Chpts', 'Policy Coverage']].map(([v, l]) => (
            <div key={l}>
              <div className="login-stat-val">{v}</div>
              <div className="login-stat-label">{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right glass card */}
      <div className="login-right">
        <form className={`login-card ${shk ? 'shake' : ''}`} onSubmit={sub}>
          <div className="login-logo"><Shield size={22}/></div>
          <div className="login-title">Welcome back</div>
          <div className="login-sub">Sign in to your Stratum Capital account</div>

          {err && (
            <div className="login-err">
              <AlertCircle size={14}/>{err}
            </div>
          )}

          <div style={{ marginBottom:14 }}>
            <label className="login-field-label">Username</label>
            <input
              className="login-input"
              type="text"
              placeholder="Enter username"
              value={u}
              onChange={e => { setU(e.target.value); setErr('') }}
              autoFocus
              style={{ marginBottom:0 }}
            />
          </div>

          <div style={{ marginBottom:20 }}>
            <label className="login-field-label">Password</label>
            <div className="login-pw-wrap">
              <input
                className="login-input"
                type={show ? 'text' : 'password'}
                placeholder="Enter password"
                value={p}
                onChange={e => { setP(e.target.value); setErr('') }}
                style={{ marginBottom:0 }}
              />
              <button type="button" className="login-pw-toggle" onClick={() => setShow(!show)}>
                {show ? <EyeOff size={15}/> : <Eye size={15}/>}
              </button>
            </div>
          </div>

          <button type="submit" className="login-btn">Sign In</button>

          <div className="login-footer">
            Protected · Stratum Capital Bank © 2025
          </div>
        </form>
      </div>
    </div>
  )
}
