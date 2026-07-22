export const LOGIN_USERNAME = 'Musab'
export const LOGIN_PASSWORD = 'musab123'

export const APPLICANT_FIELDS = [
  { k: 'loan_amnt', label: 'Loan amount ($)', type: 'number', default: 12000 },
  { k: 'term', label: 'Term (months)', type: 'select', options: [36, 60], default: 36 },
  { k: 'int_rate', label: 'Interest rate (%)', type: 'number', default: 13.33, step: 0.01 },
  {
    k: 'sub_grade', label: 'Sub-grade', type: 'select',
    options: ['A', 'B', 'C', 'D', 'E', 'F', 'G'].flatMap(l => [1, 2, 3, 4, 5].map(n => `${l}${n}`)),
    default: 'B3',
  },
  { k: 'emp_length', label: 'Employment length (yrs)', type: 'number', default: 7 },
  {
    k: 'home_ownership', label: 'Home ownership', type: 'select',
    options: ['MORTGAGE', 'RENT', 'OWN', 'OTHER'], default: 'MORTGAGE',
  },
  {
    k: 'verification_status', label: 'Verification status', type: 'select',
    options: ['Verified', 'Source Verified', 'Not Verified'], default: 'Verified',
  },
  { k: 'annual_inc', label: 'Annual income ($)', type: 'number', default: 71000 },
  {
    k: 'purpose', label: 'Loan purpose', type: 'select',
    options: ['debt_consolidation', 'credit_card', 'home_improvement', 'major_purchase', 'medical', 'car', 'other'],
    default: 'debt_consolidation',
  },
  { k: 'dti', label: 'DTI (%)', type: 'number', default: 12.0, step: 0.1 },
  { k: 'open_acc', label: 'Open accounts', type: 'number', default: 10 },
  { k: 'pub_rec', label: 'Public records', type: 'number', default: 0 },
  { k: 'revol_bal', label: 'Revolving balance ($)', type: 'number', default: 6000 },
  { k: 'revol_util', label: 'Revolving utilization (%)', type: 'number', default: 41.0, step: 0.1 },
  { k: 'total_acc', label: 'Total accounts', type: 'number', default: 28 },
  { k: 'initial_list_status', label: 'Initial list status', type: 'select', options: ['w', 'f'], default: 'w' },
  {
    k: 'application_type', label: 'Application type', type: 'select',
    options: ['INDIVIDUAL', 'JOINT'], default: 'INDIVIDUAL',
  },
  { k: 'mort_acc', label: 'Mortgage accounts', type: 'number', default: 2 },
  { k: 'pub_rec_bankruptcies', label: 'Bankruptcies on record', type: 'number', default: 0 },
]

export const GRADE_COLORS = {
  A: '#34D399', B: '#5B8DEF', C: '#FBBF24',
  D: '#FB923C', E: '#F87171', F: '#EF4444', G: '#B91C1C',
}

export const INTENT_META = {
  DECISION:   { label: 'Decision question',        color: '#5B8DEF', icon: '⚖' },
  SIMULATION: { label: 'Simulation question',       color: '#A78BFA', icon: '🔄' },
  KNOWLEDGE:  { label: 'Policy knowledge question', color: '#34D399', icon: '📚' },
  GENERAL:    { label: 'General question',          color: '#9CA3AF', icon: '💬' },
}

export const NAV_GROUPS = {
  workspace: {
    label: 'Workspace',
    items: [
      { id: 'Dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
      { id: 'Loan Prediction', label: 'Loan Prediction', icon: 'FileText' },
      { id: 'Knowledge Assistant', label: 'Knowledge Assistant', icon: 'BookOpen' },
    ],
  },
  records: {
    label: 'Records',
    items: [
      { id: 'History', label: 'History', icon: 'Clock' },
    ],
  },
  account: {
    label: 'Account',
    items: [
      { id: 'Settings', label: 'Settings', icon: 'Settings' },
    ],
  },
}
