import './ShapBars.css'

export default function ShapBars({ features = [], onLight = false }) {
  if (!features || features.length === 0) return null

  return (
    <div className="shap-bars">
      {features.map((f, i) => {
        const isPos = f.shap >= 0
        const magnitude = Math.min(Math.abs(f.shap) * 220, 50)
        const fillStyle = isPos
          ? { right: '50%', width: `${magnitude}%`, background: '#F87171' }
          : { left: '50%', width: `${magnitude}%`, background: '#34D399' }

        return (
          <div key={i} className={`shap-row ${onLight ? 'on-light' : ''}`}>
            <div className="shap-name">{f.feature}</div>
            <div className="shap-track">
              <div className="shap-mid" />
              <div className="shap-fill" style={fillStyle} />
            </div>
            <div className="shap-val">{f.value}</div>
          </div>
        )
      })}
    </div>
  )
}
