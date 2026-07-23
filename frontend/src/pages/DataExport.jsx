import {useApp} from '../context/AppContext'
import {downloadCSV,fmt$,gradeColor,gradeBg} from '../utils/helpers'
import {Download,FileText,MessageSquare,Database} from 'lucide-react'

export default function DataExport() {
  const {state}=useApp()
  const decisions=state.history.filter(h=>h.type==='decision')
  const ai=state.history.filter(h=>h.type==='ai_turn')
  const exports=[
    {title:'Predictions',count:decisions.length,desc:'All loan prediction results with repayment and default probabilities.',icon:<FileText size={20} color="var(--blue)"/>,color:'var(--blue)',border:'var(--blue-border)',bg:'var(--blue-dim)',file:'stratum_predictions.csv',
      fn:()=>downloadCSV(decisions.map((d,i)=>({id:i+1,applicant:d.applicant_label,sub_grade:d.sub_grade,loan_amount:d.loan_amnt,prediction:d.prediction,repayment_pct:((d.repayment||0)*100).toFixed(2),default_pct:((d.default||0)*100).toFixed(2),timestamp:new Date(d.ts*1000).toISOString()})),'stratum_predictions.csv')},
    {title:'AI Sessions',count:ai.length,desc:'All AI queries with detected intents and timestamps.',icon:<MessageSquare size={20} color="var(--purple)"/>,color:'var(--purple)',border:'var(--purple-border)',bg:'var(--purple-dim)',file:'stratum_ai_sessions.csv',
      fn:()=>downloadCSV(ai.map((a,i)=>({id:i+1,intent:a.intent||'GENERAL',question:a.summary||'',timestamp:new Date(a.ts*1000).toISOString()})),'stratum_ai_sessions.csv')},
    {title:'Full Session',count:state.history.length,desc:'Complete session history including all events and interactions.',icon:<Database size={20} color="var(--em)"/>,color:'var(--em)',border:'var(--em-border)',bg:'var(--em-dim)',file:'stratum_full_session.csv',
      fn:()=>downloadCSV(state.history.map((h,i)=>({id:i+1,type:h.type,summary:h.type==='decision'?h.applicant_label:(h.summary||''),result:h.type==='decision'?h.prediction:(h.intent||''),timestamp:new Date(h.ts*1000).toISOString()})),'stratum_full_session.csv')},
  ]
  return (
    <div>
      <div className="ph">
        <h1 className="ph-title">Data Export</h1>
        <p className="ph-sub">Download session data as CSV for analysis in Excel, Python, or any data tool.</p>
      </div>
      <div className="g3 mb20">
        {exports.map(e=>(
          <div key={e.title} className="card" style={{display:'flex',flexDirection:'column'}}>
            <div style={{width:44,height:44,borderRadius:10,background:e.bg,border:`1px solid ${e.border}`,display:'flex',alignItems:'center',justifyContent:'center',marginBottom:14}}>{e.icon}</div>
            <div style={{fontWeight:700,fontSize:15,letterSpacing:'-0.01em',marginBottom:3,color:'var(--text)'}}>{e.title}</div>
            <div style={{fontSize:11.5,color:'var(--text-3)',fontWeight:600,marginBottom:8}}>{e.count} records</div>
            <div style={{fontSize:13,color:'var(--text-3)',lineHeight:1.65,flex:1,marginBottom:14}}>{e.desc}</div>
            <div style={{fontFamily:'monospace',fontSize:11,color:'var(--text-3)',background:'var(--surface-2)',padding:'4px 9px',borderRadius:5,border:'1px solid var(--border)',marginBottom:12}}>{e.file}</div>
            <button className="btn btn-primary" onClick={e.fn} disabled={!e.count}><Download size={13}/>Download CSV</button>
          </div>
        ))}
      </div>
      {decisions.length>0&&(
        <div className="card">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:14}}>
            <div style={{fontWeight:700,fontSize:14,color:'var(--text)'}}>Preview — Predictions</div>
            <span style={{fontSize:12,color:'var(--text-3)'}}>First {Math.min(decisions.length,10)} records</span>
          </div>
          <table className="tbl"><thead><tr><th>#</th><th>Applicant</th><th>Loan</th><th>Grade</th><th>Decision</th><th>Repayment%</th><th>Default%</th><th>Timestamp</th></tr></thead>
            <tbody>{decisions.slice(0,10).map((r,i)=>(
              <tr key={i}>
                <td style={{color:'var(--text-3)'}}>{i+1}</td>
                <td style={{fontWeight:600,color:'var(--text)'}}>{r.applicant_label}</td>
                <td>{fmt$(r.loan_amnt||0)}</td>
                <td><span className="grade-badge" style={{background:gradeBg(r.sub_grade),color:gradeColor(r.sub_grade)}}>{r.sub_grade}</span></td>
                <td><span className={`badge badge-${r.prediction==='Approved'?'em':'red'}`}>{r.prediction}</span></td>
                <td style={{color:'var(--em)'}}>{((r.repayment||0)*100).toFixed(2)}%</td>
                <td style={{color:r.default>0.4?'var(--red)':'var(--text-3)'}}>{((r.default||0)*100).toFixed(2)}%</td>
                <td style={{fontSize:11,color:'var(--text-3)'}}>{new Date(r.ts*1000).toLocaleString()}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
