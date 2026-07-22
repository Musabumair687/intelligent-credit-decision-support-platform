import { useState } from 'react'
import { useApp } from '../../context/AppContext'
import { checkHealth } from '../../api/client'
import LightCard from '../../components/LightCard'
import { Save, CheckCircle2, Loader2, Server } from 'lucide-react'
import './Settings.css'

export default function Settings() {
  const { state, dispatch } = useApp()
  const [apiBase, setApiBase] = useState(state.apiBase)
  const [sessionId, setSessionId] = useState(state.sessionId)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    dispatch({
      type: 'UPDATE_SETTINGS',
      payload: { apiBase: apiBase.replace(/\/+$/, ''), sessionId },
    })

    // Check health of new URL
    await checkHealth(apiBase)

    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="animate-fade-in">
      <h1 className="hero-title">Settings</h1>
      <p className="hero-sub">Configuration for this session.</p>

      <LightCard className="settings-card">
        <div className="form-group">
          <label className="form-label">Backend API base URL</label>
          <input
            className="form-input"
            type="text"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Session ID</label>
          <input
            className="form-input"
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? (
            <><Loader2 size={14} className="animate-spin" /> Reconnecting…</>
          ) : saved ? (
            <><CheckCircle2 size={14} /> Saved!</>
          ) : (
            <><Save size={14} /> Save & reconnect</>
          )}
        </button>

        <div className="settings-help">
          <Server size={13} />
          <span>
            Start the backend from the project root with:
            <code>uvicorn backend.main:app --reload --port 8000</code>
          </span>
        </div>
      </LightCard>
    </div>
  )
}
