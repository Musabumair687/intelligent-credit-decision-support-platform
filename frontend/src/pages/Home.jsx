import {useApp} from '../context/AppContext'
import {fmt$,timeAgo,gradeColor,gradeBg} from '../utils/helpers'
import {FileText,BookOpen,ArrowRight} from 'lucide-react'

export default function Home() {
  const {state,dispatch}=useApp()
  const go=p=>dispatch({type:'NAV',payload:p})
  const decisions=state.history.filter(h=>h.type==='decision')
  return (
    <div>
      <div className="ph">
        <div className="ph-eyebrow">Credit Decision Console</div>
        <h1 className="ph-title">Welcome back, Loan Officer</h1>
        <p className="ph-sub">ML-powered credit assessments with SHAP explainability and AI-assisted policy lookup.</p>
      </div>

      <div className="g2 mb20">
        {[['Loan Prediction','Run ML credit assessments across 4 structured sections. Get instant decisions with SHAP analysis.',FileText,'var(--blue)','var(--blue-dim)','var(--blue-border)'],
          ['Knowledge Assistant','Query Stratum Capital Bank lending policy. Get cited answers from 17 chapters of compliance docs.',BookOpen,'var(--em)','var(--em-dim)','var(--em-border)']]
          .map(([title,desc,Icon,c,bg,border])=>(
          <button key={title} className="card" style={{textAlign:'left',cursor:'pointer',border:`1px solid ${border}`,background:bg,padding:28,transition:'box-shadow 0.2s,transform 0.2s'}}
            onClick={()=>go(title)}
            onMouseEnter={e=>{e.currentTarget.style.boxShadow='var(--shadow-md)';e.currentTarget.style.transform='translateY(-2px)'}}
            onMouseLeave={e=>{e.currentTarget.style.boxShadow='';e.currentTarget.style.transform=''}}>
            <div style={{width:42,height:42,borderRadius:10,background:'var(--surface)',border:`1px solid ${border}`,display:'flex',alignItems:'center',justifyContent:'center',marginBottom:16}}>
              <Icon size={20} color={c}/>
            </div>
            <div style={{fontSize:16,fontWeight:700,color:'var(--text)',marginBottom:6,letterSpacing:'-0.01em'}}>{title}</div>
            <div style={{fontSize:13,color:'var(--text-3)',lineHeight:1.65,marginBottom:18}}>{desc}</div>
            <div style={{display:'flex',alignItems:'center',gap:5,fontSize:13,fontWeight:600,color:c}}>Get started <ArrowRight size={13}/></div>
          </button>
        ))}
      </div>

      {decisions.length>0&&(
        <div className="card">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:14}}>
            <div>
              <div style={{fontWeight:700,fontSize:14,color:'var(--text)'}}>Recent Predictions</div>
              <div style={{fontSize:12,color:'var(--text-3)',marginTop:2}}>{decisions.length} this session</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={()=>go('Reports')}>View all →</button>
          </div>
          <table className="tbl">
            <thead><tr><th>Applicant</th><th>Loan</th><th>Grade</th><th>Decision</th><th>Default Risk</th><th>When</th></tr></thead>
            <tbody>{decisions.slice(0,5).map((r,i)=>(
              <tr key={i}>
                <td style={{fontWeight:600,color:'var(--text)'}}>{r.applicant_label}</td>
                <td>{fmt$(r.loan_amnt||0)}</td>
                <td><span className="grade-badge" style={{background:gradeBg(r.sub_grade),color:gradeColor(r.sub_grade)}}>{r.sub_grade}</span></td>
                <td><span className={`badge badge-${r.prediction==='Approved'?'em':'red'}`}>{r.prediction}</span></td>
                <td style={{color:r.default>0.4?'var(--red)':'var(--text-2)'}}>{((r.default||0)*100).toFixed(1)}%</td>
                <td style={{color:'var(--text-3)'}}>{timeAgo(r.ts)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
