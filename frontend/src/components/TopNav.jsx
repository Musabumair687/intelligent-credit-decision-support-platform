import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { NAV_ITEMS } from '../utils/constants'
import { checkHealth } from '../api/client'
import { Home, BarChart2, FileText, BookOpen, PieChart, Database, Shield, LogOut } from 'lucide-react'

const ICONS = { Home, BarChart2, FileText, BookOpen, PieChart, Database }

export default function TopNav() {
  const { state, dispatch } = useApp()
  const [healthy, setHealthy] = useState(false)

  useEffect(() => {
    let ok = true
    const check = async () => { const h = await checkHealth(state.apiBase); if(ok) setHealthy(h) }
    check()
    const t = setInterval(check, 15000)
    return () => { ok = false; clearInterval(t) }
  }, [state.apiBase])

  return (
    <nav className="topnav">
      <div className="topnav-brand">
        <div className="topnav-brand-icon"><Shield size={17}/></div>
        <div>
          <div className="topnav-brand-name">STRATUM</div>
          <div className="topnav-brand-sub">CAPITAL BANK</div>
        </div>
      </div>

      <div className="topnav-tabs">
        {NAV_ITEMS.map(item => {
          const Icon = ICONS[item.icon] || Home
          const active = state.page === item.id
          return (
            <button
              key={item.id}
              className={`topnav-tab ${active ? 'active' : ''}`}
              onClick={() => dispatch({ type: 'NAV', payload: item.id })}
            >
              <Icon size={15}/>
              <span>{item.label}</span>
            </button>
          )
        })}
      </div>

      <div className="topnav-right">
        <div className="health-dot">
          <span className={`health-dot-circle ${healthy ? 'online' : 'offline'}`}/>
          {healthy ? 'API Online' : 'Offline'}
        </div>
        <div className="user-chip">
          <div className="user-avatar">LO</div>
          <span className="user-chip-name">Loan Officer</span>
        </div>
        <button className="btn-logout" onClick={() => dispatch({ type: 'LOGOUT' })}>
          <LogOut size={13}/> Logout
        </button>
      </div>
    </nav>
  )
}
