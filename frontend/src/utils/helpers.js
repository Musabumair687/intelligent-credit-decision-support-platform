import {GRADE_COLORS,GRADE_BG} from './constants'
export const gradeColor=sg=>GRADE_COLORS[String(sg||'')[0]?.toUpperCase()]||'#71717A'
export const gradeBg=sg=>GRADE_BG[String(sg||'')[0]?.toUpperCase()]||'rgba(113,113,122,0.12)'
export const timeAgo=ts=>{const s=Math.floor(Date.now()/1000-ts);if(s<60)return`${s}s ago`;if(s<3600)return`${Math.floor(s/60)}m ago`;if(s<86400)return`${Math.floor(s/3600)}h ago`;return`${Math.floor(s/86400)}d ago`}
export const fmt$=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v)
export const downloadCSV=(rows,filename)=>{
  if(!rows.length)return
  const h=Object.keys(rows[0])
  const csv=[h.join(','),...rows.map(r=>h.map(k=>JSON.stringify(r[k]??'')).join(','))].join('\n')
  const a=Object.assign(document.createElement('a'),{href:URL.createObjectURL(new Blob([csv],{type:'text/csv'})),download:filename})
  a.click();URL.revokeObjectURL(a.href)
}
