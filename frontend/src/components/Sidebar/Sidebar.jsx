import { useState, useEffect } from 'react'
import { useApp } from '../../context/AppContext'
import { checkHealth } from '../../api/client'
import { NAV_GROUPS } from '../../utils/constants'
import { LayoutDashboard, FileText, BookOpen, Clock, Settings, Building2, FolderOpen, LogOut, ChevronDown, Shield } from 'lucide-react'
import './Sidebar.css'

const ICON_MAP = {
  LayoutDashboard, FileText, BookOpen, Clock, Settings,
}

const GROUP_ICONS = {
  workspace: Building2,
  records: FolderOpen,
  account: Settings,
}

export default function Sidebar() {
  const { state, dispatch } = useApp()
  const [healthy, setHealthy] = useState(false)

  useEffect(() => {
    let mounted = true
    const check = async () => {
      const ok = await checkHealth(state.apiBase)
      if (mounted) setHealthy(ok)
    }
    check()
    const interval = setInterval(check, 15000)
    return () => { mounted = false; clearInterval(interval) }
  }, [state.apiBase])

  const navigateTo = (pageId, groupKey) => {
    dispatch({ type: 'SET_PAGE', payload: pageId })
    dispatch({ type: 'SET_NAV_GROUP', payload: groupKey })
  }

  const setGroup = (key) => {
    dispatch({ type: 'SET_NAV_GROUP', payload: key })
  }

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Shield size={18} />
        </div>
        <div>
          <div className="sidebar-brand-name">STRATUM</div>
          <div className="sidebar-brand-sub">CAPITAL BANK</div>
        </div>
      </div>

      {/* User card */}
      <div className="sidebar-user">
        <div className="sidebar-user-avatar">LO</div>
        <div className="sidebar-user-info">
          <div className="sidebar-user-name">Loan Officer</div>
          <div className="sidebar-user-role">Underwriting Desk</div>
        </div>
        <ChevronDown size={14} className="sidebar-user-chevron" />
      </div>

      {/* Navigation */}
      <div className="sidebar-nav">
        <div className="sidebar-rail">
          {Object.entries(NAV_GROUPS).map(([key, group]) => {
            const Icon = GROUP_ICONS[key] || Building2
            const isActive = state.navGroupOpen === key
            return (
              <button
                key={key}
                className={`sidebar-rail-btn ${isActive ? 'active' : ''}`}
                onClick={() => setGroup(key)}
                title={group.label}
              >
                <Icon size={18} />
              </button>
            )
          })}
        </div>

        <div className="sidebar-panel">
          {Object.entries(NAV_GROUPS).map(([key, group]) => {
            if (state.navGroupOpen !== key) return null
            return (
              <div key={key} className="sidebar-group">
                <div className="sidebar-group-label">{group.label}</div>
                {group.items.map(item => {
                  const Icon = ICON_MAP[item.icon] || LayoutDashboard
                  const isActive = state.currentPage === item.id
                  return (
                    <button
                      key={item.id}
                      className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                      onClick={() => navigateTo(item.id, key)}
                    >
                      <Icon size={16} />
                      <span>{item.label}</span>
                    </button>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-health">
          <span className={`sidebar-health-dot ${healthy ? 'online' : 'offline'}`} />
          <span>{healthy ? 'Connected · model ready' : 'Offline · backend unreachable'}</span>
        </div>
        <button className="sidebar-logout" onClick={() => dispatch({ type: 'LOGOUT' })}>
          <LogOut size={14} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}
