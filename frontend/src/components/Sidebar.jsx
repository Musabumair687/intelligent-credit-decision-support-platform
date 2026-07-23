import {useApp} from '../context/AppContext'
import {NAV_ITEMS} from '../utils/constants'
import {Home,BarChart2,FileText,BookOpen,PieChart,Download} from 'lucide-react'

const IC={Home,BarChart2,FileText,BookOpen,PieChart,Download}

export default function Sidebar() {
  const {state,dispatch}=useApp()
  const hist=state.history
  const cnt={'Dashboard':hist.length||null,'Reports':hist.filter(h=>h.type==='decision').length||null,'Data':hist.filter(h=>h.type==='decision').length||null}
  return (
    <aside className="sidebar">
      <div className="sb-group">
        <div className="sb-label">Navigation</div>
        {NAV_ITEMS.map(it=>{
          const Icon=IC[it.icon]||Home
          const active=state.page===it.id
          const c=cnt[it.id]
          return (
            <button key={it.id} className={`sb-item ${active?'active':''}`} onClick={()=>dispatch({type:'NAV',payload:it.id})}>
              <Icon size={14}/>
              <span style={{flex:1}}>{it.label}</span>
              {c&&<span className="sb-count">{c}</span>}
            </button>
          )
        })}
      </div>
      <div className="sb-divider"/>
      <div className="sb-group">
        <div className="sb-label">Session</div>
        <div style={{padding:'6px 8px'}}>
          <div style={{fontSize:11.5,color:'var(--text-3)',marginBottom:3}}>Predictions</div>
          <div style={{fontSize:18,fontWeight:700,color:'var(--text)'}}>{hist.filter(h=>h.type==='decision').length}</div>
        </div>
        <div style={{padding:'4px 8px'}}>
          <div style={{fontSize:11.5,color:'var(--text-3)',marginBottom:3}}>AI Queries</div>
          <div style={{fontSize:18,fontWeight:700,color:'var(--text)'}}>{hist.filter(h=>h.type==='ai_turn').length}</div>
        </div>
      </div>
    </aside>
  )
}
