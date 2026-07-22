import { INTENT_META } from '../utils/constants'

export default function IntentChip({ intent }) {
  const meta = INTENT_META[intent] || INTENT_META.GENERAL
  return (
    <span
      className="intent-chip"
      style={{ background: `${meta.color}22`, color: meta.color }}
    >
      {meta.label}
    </span>
  )
}
