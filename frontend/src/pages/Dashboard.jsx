import {useApp} from '../context/AppContext'
import StatCard from '../components/StatCard'
import DonutGauge from '../components/DonutGauge'
import {fmt$,timeAgo,gradeColor,gradeBg} from '../utils/helpers'
import {FileText,CheckCircle,XCircle,MessageSquare,TrendingUp,AlertTriangle,Trash2} from 'lucide-react'

export default function Dashboard() {
  const {state,dispatch}=useApp()
  const d=state.history.filter(h=>h.type==='decision')
  const ai=state.history.filter(h=>h.type==='ai_turn')
  const app=d.filter(x=>x.prediction==='Approved')
  const rate=d.length?app.length/d.length*100:0
  const avgLoan=d.length?d.reduce((a,x)=>a+(x.loan_amnt||0),0)/d.length:0
  const avgDef=d.length?d.reduce((a,x)=>a+(x.default||0),0)/d.length*100:0
  const flagged=d.filter(x=>x.default>0.35&&x.default<0.65)
  return (
    <div>
      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',marginBottom:20}}>
        <div className="ph" style={{marginBottom:0}}>
          <h1 className="ph-title">Dashboard</h1>
          <p className="ph-sub">Real-time session analytics</p>
        </div>
        <button className="btn btn-danger btn-sm" onClick={()=>dispatch({type:'CLR_HIST'})}><Trash2 size={12}/> Clear session</button>
      </div>
      <div className="g5 mb16">
        <StatCard label="Predictions" value={d.length} color="#3B82F6" bg="rgba(59,130,246,0.12)" icon={<FileText size={15} color="#3B82F6"/>} spark={state.probTrend}/>
        <StatCard label="Approved" value={app.length} color="#10B981" bg="rgba(16,185,129,0.12)" icon={<CheckCircle size={15} color="#10B981"/>}/>
        <StatCard label="Rejected" value={d.length-app.length} color="#EF4444" bg="rgba(239,68,68,0.12)" icon={<XCircle size={15} color="#EF4444"/>}/>
        <StatCard label="AI Queries" value={ai.length} color="#8B5CF6" bg="rgba(139,92,246,0.12)" icon={<MessageSquare size={15} color="#8B5CF6"/>}/>
        <StatCard label="Approval %" value={`${rate.toFixed(0)}%`} color="#10B981" bg="rgba(16,185,129,0.12)" icon={<TrendingUp size={15} color="#10B981"/>}/>
      </div>
      <div className="g3 mb16">
        <div className="card" style={{textAlign:'center'}}>
          <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)',marginBottom:10}}>Approval Rate</div>
          <div style={{display:'inline-block'}}><DonutGauge pct={rate} color={rate>50?'#10B981':'#EF4444'}/></div>
          <div style={{fontSize:12,color:'var(--text-3)',marginTop:8}}>{app.length} of {d.length} approved</div>
        </div>
        <div className="card">
          <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)',marginBottom:12}}>Session Averages</div>
          {[['Loan Amount',fmt$(avgLoan),'var(--blue)'],['Default Risk',avgDef.toFixed(1)+'%',avgDef>30?'var(--red)':'var(--em)'],['AI Sessions',ai.length,'var(--purple)']].map(([l,v,c])=>(
            <div key={l} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'9px 0',borderBottom:'1px solid var(--border)'}}>
              <span style={{fontSize:12.5,color:'var(--text-3)'}}>{l}</span>
              <span style={{fontWeight:700,color:c,fontSize:13}}>{v}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:12}}>
            <AlertTriangle size={13} color="var(--amber)"/>
            <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)'}}>Needs Review</div>
          </div>
          {flagged.length===0
            ?<div className="empty" style={{padding:'12px 0',fontSize:12}}>No flagged applicants</div>
            :flagged.slice(0,4).map((r,i)=>(
              <div key={i} style={{padding:'7px 0',borderBottom:'1px solid var(--border)'}}>
                <div style={{fontWeight:600,fontSize:12.5,color:'var(--text)'}}>{r.applicant_label}</div>
                <div style={{fontSize:11.5,color:'var(--text-3)',marginTop:1}}>Risk: {((r.default||0)*100).toFixed(1)}%</div>
              </div>
            ))
          }
        </div>
      </div>
      <div className="card">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:14}}>
          <div style={{fontWeight:700,fontSize:14,color:'var(--text)'}}>All Predictions</div>
          <span style={{fontSize:12,color:'var(--text-3)'}}>{d.length} records</span>
        </div>
        {d.length===0?<div className="empty">No predictions yet. Use <b>Loan Prediction</b> to get started.</div>
          :<table className="tbl"><thead><tr><th>#</th><th>Applicant</th><th>Loan</th><th>Grade</th><th>Decision</th><th>Repayment</th><th>Default</th><th>When</th></tr></thead>
            <tbody>{d.map((r,i)=>(
              <tr key={i}>
                <td style={{color:'var(--text-3)'}}>{d.length-i}</td>
                <td style={{fontWeight:600,color:'var(--text)'}}>{r.applicant_label}</td>
                <td>{fmt$(r.loan_amnt||0)}</td>
                <td><span className="grade-badge" style={{background:gradeBg(r.sub_grade),color:gradeColor(r.sub_grade)}}>{r.sub_grade}</span></td>
                <td><span className={`badge badge-${r.prediction==='Approved'?'em':'red'}`}>{r.prediction}</span></td>
                <td style={{color:'var(--em)'}}>{((r.repayment||0)*100).toFixed(1)}%</td>
                <td style={{color:r.default>0.4?'var(--red)':'var(--text-3)'}}>{((r.default||0)*100).toFixed(1)}%</td>
                <td style={{color:'var(--text-3)'}}>{timeAgo(r.ts)}</td>
              </tr>
            ))}</tbody></table>
        }
      </div>
    </div>
  )
}
