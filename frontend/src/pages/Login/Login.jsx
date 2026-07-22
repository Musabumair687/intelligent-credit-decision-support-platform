import { useState } from 'react'
import { useApp } from '../../context/AppContext'
import { LOGIN_USERNAME, LOGIN_PASSWORD } from '../../utils/constants'
import { Shield, Eye, EyeOff } from 'lucide-react'
import './Login.css'

export default function Login() {
  const { dispatch } = useApp()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [shaking, setShaking] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (username === LOGIN_USERNAME && password === LOGIN_PASSWORD) {
      dispatch({ type: 'LOGIN' })
    } else {
      setError('Invalid username or password.')
      setShaking(true)
      setTimeout(() => setShaking(false), 500)
    }
  }

  return (
    <div className="login-page">
      <div className="login-bg-orb login-bg-orb-1" />
      <div className="login-bg-orb login-bg-orb-2" />
      <div className="login-bg-orb login-bg-orb-3" />

      <form
        className={`login-card glass-card ${shaking ? 'animate-shake' : ''}`}
        onSubmit={handleSubmit}
      >
        <div className="login-logo">
          <Shield size={26} />
        </div>
        <h1 className="login-title">STRATUM CAPITAL BANK</h1>
        <p className="login-subtitle">Intelligent Credit Decision Support Platform</p>

        <div className="login-fields">
          <div className="form-group">
            <label className="form-label" style={{ color: 'rgba(255,255,255,0.55)' }}>Username</label>
            <input
              className="form-input-dark"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError('') }}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label" style={{ color: 'rgba(255,255,255,0.55)' }}>Password</label>
            <div className="login-pw-wrap">
              <input
                className="form-input-dark"
                type={showPw ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError('') }}
              />
              <button
                type="button"
                className="login-pw-toggle"
                onClick={() => setShowPw(!showPw)}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="login-error">{error}</div>}

        <button type="submit" className="btn btn-primary btn-block login-submit">
          Sign In
        </button>

        <p className="login-footer">Protected by enterprise-grade security</p>
      </form>
    </div>
  )
}
