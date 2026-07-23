import {useApp} from '../context/AppContext'
import DonutGauge from '../components/DonutGauge'
import {fmt$,timeAgo,gradeColor,gradeBg,downloadCSV} from '../utils/helpers'
import {Download} from 'lucide-react'

export default function Reports() {
  const {state}=useApp()
  const d=state.history.filter(h=>h.type==='decision')
  const app=d.filter(x=>x.prediction==='Approved')
  const rate=d.length?app.length/d.length*100:0
  const avgLoan=d.length?d.reduce((a,x)=>a+(x.loan_amnt||0),0)/d.length:0
  const avgDef=d.length?d.reduce((a,x)=>a+(x.default||0),0)/d.length*100:0
  const exp=()=>downloadCSV(d.map((x,i)=>({id:i+1,applicant:x.applicant_label,sub_grade:x.sub_grade,loan_amount:x.loan_amnt,prediction:x.prediction,repayment_pct:((x.repayment||0)*100).toFixed(2),default_pct:((x.default||0)*100).toFixed(2),timestamp:new Date(x.ts*1000).toISOString()})),'stratum_report.csv')
  return (
    <div>
      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',marginBottom:20}}>
        <div className="ph" style={{marginBottom:0}}>
          <h1 className="ph-title">Reports</h1>
          <p className="ph-sub">Session performance summary and grade analytics</p>
        </div>
        <button className="btn btn-primary" onClick={exp} disabled={!d.length}><Download size={13}/>Export CSV</button>
      </div>
      <div className="g4 mb16">
        {[['Total',d.length,'var(--blue)'],['Approved',app.length,'var(--em)'],['Rejected',d.length-app.length,'var(--red)'],['Avg Loan',fmt$(avgLoan),'var(--purple)']].map(([l,v,c])=>(
          <div key={l} className="card" style={{textAlign:'center',padding:'16px 20px'}}>
            <div style={{fontSize:24,fontWeight:700,color:c,letterSpacing:'-0.02em',lineHeight:1,marginBottom:4}}>{v}</div>
            <div style={{fontSize:10.5,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.06em',color:'var(--text-3)'}}>{l}</div>
          </div>
        ))}
      </div>
      <div className="g3 mb16">
        <div className="card" style={{textAlign:'center'}}>
          <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)',marginBottom:10}}>Approval Rate</div>
          <div style={{display:'inline-block'}}><DonutGauge pct={rate} color={rate>50?'#10B981':'#EF4444'}/></div>
        </div>
        <div className="card">
          <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)',marginBottom:12}}>Key Metrics</div>
          {[['Approval Rate',rate.toFixed(1)+'%',rate>50?'var(--em)':'var(--red)'],['Avg Default Risk',avgDef.toFixed(1)+'%',avgDef>30?'var(--red)':'var(--em)'],['Avg Loan Amount',fmt$(avgLoan),'var(--blue)']].map(([l,v,c])=>(
            <div key={l} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'9px 0',borderBottom:'1px solid var(--border)'}}>
              <span style={{fontSize:12.5,color:'var(--text-3)'}}>{l}</span>
              <span style={{fontWeight:700,color:c,fontSize:13}}>{v}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div style={{fontWeight:600,fontSize:13,color:'var(--text-2)',marginBottom:12}}>Grade Distribution</div>
          {'ABCDEFG'.split('').map(g=>{
            const cnt=d.filter(x=>x.sub_grade?.startsWith(g)).length
            if(!cnt)return null
            return (
              <div key={g} style={{display:'flex',alignItems:'center',gap:8,marginBottom:7}}>
                <span style={{width:20,fontWeight:700,color:gradeColor(g),fontSize:12,fontFamily:'monospace'}}>{g}</span>
                <div className="prog" style={{flex:1}}><div className="prog-fill" style={{width:`${cnt/d.length*100}%`,background:gradeColor(g)}}/></div>
                <span style={{fontSize:11.5,color:'var(--text-3)',width:18,textAlign:'right'}}>{cnt}</span>
              </div>
            )
          })}
        </div>
      </div>
      <div className="card">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:14}}>
          <div style={{fontWeight:700,fontSize:14,color:'var(--text)'}}>All Predictions</div>
          <span style={{fontSize:12,color:'var(--text-3)'}}>{d.length} records</span>
        </div>
        {d.length===0?<div className="empty">No predictions yet.</div>
          :<table className="tbl"><thead><tr><th>#</th><th>Applicant</th><th>Loan</th><th>Grade</th><th>Decision</th><th>Repayment</th><th>Default</th><th>Date</th></tr></thead>
            <tbody>{d.map((r,i)=>(
              <tr key={i}>
                <td style={{color:'var(--text-3)'}}>{d.length-i}</td>
                <td style={{fontWeight:600,color:'var(--text)'}}>{r.applicant_label}</td>
                <td>{fmt$(r.loan_amnt||0)}</td>
                <td><span className="grade-badge" style={{background:gradeBg(r.sub_grade),color:gradeColor(r.sub_grade)}}>{r.sub_grade}</span></td>
                <td><span className={`badge badge-${r.prediction==='Approved'?'em':'red'}`}>{r.prediction}</span></td>
                <td style={{color:'var(--em)'}}>{((r.repayment||0)*100).toFixed(1)}%</td>
                <td style={{color:r.default>0.4?'var(--red)':'var(--text-3)'}}>{((r.default||0)*100).toFixed(1)}%</td>
                <td style={{fontSize:11.5,color:'var(--text-3)'}}>{new Date(r.ts*1000).toLocaleDateString()}</td>
              </tr>
            ))}</tbody></table>
        }
      </div>
    </div>
  )
}
