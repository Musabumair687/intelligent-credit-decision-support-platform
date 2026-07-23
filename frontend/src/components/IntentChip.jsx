import {INTENT_META} from '../utils/constants'
export default function IntentChip({intent}) {
  const m=INTENT_META[intent]||INTENT_META.GENERAL
  return <span className="intent-chip" style={{background:m.bg,color:m.color,borderColor:m.border}}>{m.label}</span>
}
