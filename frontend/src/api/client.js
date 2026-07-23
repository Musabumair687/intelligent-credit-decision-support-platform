export class ApiError extends Error { constructor(msg){super(msg);this.name='ApiError'} }
export async function apiPost(base,path,body){
  const url=base.replace(/\/+$/,'')+path
  let resp
  try{resp=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
  catch(e){throw new ApiError(`Cannot reach ${url}: ${e.message}`)}
  let data={}
  try{data=await resp.json()}catch{}
  if(!resp.ok){throw new ApiError(typeof data?.detail==='string'?data.detail:`HTTP ${resp.status}`)}
  return data
}
export async function checkHealth(base){
  try{
    const ctrl=new AbortController(),t=setTimeout(()=>ctrl.abort(),4000)
    const r=await fetch(base.replace(/\/+$/,'')+'/health',{signal:ctrl.signal})
    clearTimeout(t);const d=await r.json()
    return !!(r.ok&&d.model_loaded)
  }catch{return false}
}
