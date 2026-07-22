import { GRADE_COLORS } from './constants'

export function gradeColor(subGrade) {
  if (!subGrade) return '#9CA3AF'
  const letter = String(subGrade)[0].toUpperCase()
  return GRADE_COLORS[letter] || '#6B7280'
}

export function timeAgo(ts) {
  const s = Math.floor(Date.now() / 1000 - ts)
  if (s < 0) return 'just now'
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

export function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(val)
}
