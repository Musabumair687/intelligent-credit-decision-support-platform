export default function ShapBars({features=[]}) {
  if(!features?.length) return null
  return (
    <div style={{display:'flex',flexDirection:'column',gap:7}}>
      {features.map((f,i)=>{
        const isPos=f.shap>=0,mag=Math.min(Math.abs(f.shap)*220,50)
        return (
          <div key={i} className="shap-row">
            <div className="shap-name">{f.feature}</div>
            <div className="shap-track">
              <div className="shap-mid"/>
              <div className="shap-fill" style={isPos?{right:'50%',width:`${mag}%`,background:'#EF4444'}:{left:'50%',width:`${mag}%`,background:'#10B981'}}/>
            </div>
            <div className="shap-val">{f.value}</div>
          </div>
        )
      })}
    </div>
  )
}
