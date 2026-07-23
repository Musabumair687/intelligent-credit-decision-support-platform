import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { NAV_ITEMS } from '../utils/constants'
import { checkHealth } from '../api/client'
import { Home, BarChart2, FileText, BookOpen, PieChart, Download, Shield, LogOut, Sun, Moon } from 'lucide-react'

const ICONS = { Home, BarChart2, FileText, BookOpen, PieChart, Download }

export default function Nav() {
  const { state, dispatch } = useApp()
  const [ok, setOk] = useState(false)
  const dark = state.theme === 'dark'

  useEffect(() => {
    let live = true
    const chk = async () => { const h = await checkHealth(state.apiBase); if(live) setOk(h) }
    chk(); const t = setInterval(chk, 15000)
    return () => { live=false; clearInterval(t) }
  }, [state.apiBase])

  return (
    <nav className="nav">
      <div className="nav-brand">
        <div className="nav-logo"><Shield size={16}/></div>
        <div>
          <div className="nav-brand-name">Stratum Capital</div>
          <div className="nav-brand-sub">Credit Decision Platform</div>
        </div>
      </div>
      <div className="nav-sep"/>

      <div className="nav-tabs">
        {NAV_ITEMS.map(it => {
          const Icon = ICONS[it.icon] || Home
          const active = state.page === it.id
          return (
            <button key={it.id} className={`nav-tab ${active ? 'active' : ''}`}
              onClick={() => dispatch({ type:'NAV', payload:it.id })}>
              <Icon size={14}/><span>{it.label}</span>
            </button>
          )
        })}
      </div>

      <div className="nav-right">
        <div className="status-badge">
          <span className={`dot ${ok ? 'on' : 'off'}`}/>
          {ok ? 'API Online' : 'Offline'}
        </div>
        <div className="user-pill">
          <div className="user-av">LO</div>
          <span className="user-name">Loan Officer</span>
        </div>
        <button className="theme-btn" onClick={() => dispatch({ type:'TOGGLE_THEME' })} title={dark ? 'Light mode' : 'Dark mode'}>
          {dark ? <Sun size={15}/> : <Moon size={15}/>}
        </button>
        <button className="btn-logout" onClick={() => dispatch({ type:'LOGOUT' })}>
          <LogOut size={13}/> Logout
        </button>
      </div>
    </nav>
  )
}
