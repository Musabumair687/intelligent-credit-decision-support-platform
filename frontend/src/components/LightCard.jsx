export default function LightCard({ children, className = '', style = {} }) {
  return (
    <div className={`light-card ${className}`} style={style}>
      {children}
    </div>
  )
}
