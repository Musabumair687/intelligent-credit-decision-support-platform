export const CREDS = { user:'Musab', pass:'musab123' }

export const SLIDER_FIELDS = {
  emp_length: { min:0, max:40, step:1, fmt: v=>`${v} yrs`, minLabel:'0 yrs', maxLabel:'40 yrs' },
  loan_amnt:  { min:1000, max:40000, step:500, fmt: v=>`$${Number(v).toLocaleString()}`, minLabel:'$1K', maxLabel:'$40K' },
  int_rate:   { min:5, max:30, step:0.5, fmt: v=>`${Number(v).toFixed(1)}%`, minLabel:'5%', maxLabel:'30%' },
  annual_inc: { min:20000, max:300000, step:5000, fmt: v=>`$${(v/1000).toFixed(0)}K`, minLabel:'$20K', maxLabel:'$300K' },
  dti:        { min:0, max:50, step:0.5, fmt: v=>`${Number(v).toFixed(1)}%`, minLabel:'0%', maxLabel:'50%' },
  revol_util: { min:0, max:100, step:1, fmt: v=>`${Number(v).toFixed(0)}%`, minLabel:'0%', maxLabel:'100%' },
  revol_bal:  { min:0, max:50000, step:500, fmt: v=>`$${Number(v).toLocaleString()}`, minLabel:'$0', maxLabel:'$50K' },
}

export const PERSONAL_FIELDS = [
  { k:'emp_length', label:'Employment Length', type:'number', default:7, step:1 },
  { k:'home_ownership', label:'Home Ownership', type:'select', default:'MORTGAGE', options:['MORTGAGE','RENT','OWN','OTHER'] },
  { k:'application_type', label:'Application Type', type:'select', default:'INDIVIDUAL', options:['INDIVIDUAL','JOINT'] },
  { k:'verification_status', label:'Verification Status', type:'select', default:'Verified', options:['Verified','Source Verified','Not Verified'] },
]
export const LOAN_FIELDS = [
  { k:'loan_amnt', label:'Loan Amount', type:'number', default:12000, step:500 },
  { k:'term', label:'Term (months)', type:'select', default:36, options:[36,60] },
  { k:'int_rate', label:'Interest Rate', type:'number', default:13.33, step:0.5 },
  { k:'purpose', label:'Loan Purpose', type:'select', default:'debt_consolidation', options:['debt_consolidation','credit_card','home_improvement','major_purchase','medical','car','other'] },
  { k:'initial_list_status', label:'Initial List Status', type:'select', default:'w', options:['w','f'] },
]
export const FINANCIAL_FIELDS = [
  { k:'annual_inc', label:'Annual Income', type:'number', default:71000, step:5000 },
  { k:'dti', label:'Debt-to-Income', type:'number', default:12.0, step:0.5 },
  { k:'revol_bal', label:'Revolving Balance', type:'number', default:6000, step:500 },
  { k:'revol_util', label:'Revolving Utilization', type:'number', default:41.0, step:1 },
  { k:'open_acc', label:'Open Accounts', type:'number', default:10, step:1 },
  { k:'total_acc', label:'Total Accounts', type:'number', default:28, step:1 },
]
export const CREDIT_FIELDS = [
  { k:'sub_grade', label:'Sub-Grade', type:'select', default:'B3', options:['A','B','C','D','E','F','G'].flatMap(l=>[1,2,3,4,5].map(n=>`${l}${n}`)) },
  { k:'pub_rec', label:'Public Records', type:'number', default:0, step:1 },
  { k:'mort_acc', label:'Mortgage Accounts', type:'number', default:2, step:1 },
  { k:'pub_rec_bankruptcies', label:'Bankruptcies on Record', type:'number', default:0, step:1 },
]

export const ALL_FIELDS = [...PERSONAL_FIELDS, ...LOAN_FIELDS, ...FINANCIAL_FIELDS, ...CREDIT_FIELDS]

export const FIELD_SECTIONS = [
  { id:'personal', label:'Personal Details', hint:'Employment & ownership', fields:PERSONAL_FIELDS },
  { id:'loan', label:'Loan Details', hint:'Amount, term & rate', fields:LOAN_FIELDS },
  { id:'financial', label:'Financial Profile', hint:'Income, DTI & utilization', fields:FINANCIAL_FIELDS },
  { id:'credit', label:'Credit History', hint:'Grade & records', fields:CREDIT_FIELDS },
]

export const GRADE_COLORS = { A:'#10B981', B:'#4F8EF7', C:'#F5A623', D:'#F97316', E:'#F25757', F:'#DC2626', G:'#991B1B' }
export const GRADE_BG     = { A:'rgba(16,185,129,0.12)', B:'rgba(79,142,247,0.12)', C:'rgba(245,166,35,0.12)', D:'rgba(249,115,22,0.12)', E:'rgba(242,87,87,0.12)', F:'rgba(220,38,38,0.12)', G:'rgba(153,27,27,0.12)' }

export const INTENT_META = {
  DECISION:  { label:'Decision',   color:'#4F8EF7', bg:'rgba(79,142,247,0.10)',  border:'rgba(79,142,247,0.25)' },
  SIMULATION:{ label:'Simulation', color:'#A78BFA', bg:'rgba(167,139,250,0.10)', border:'rgba(167,139,250,0.25)' },
  KNOWLEDGE: { label:'Policy',     color:'#10B981', bg:'rgba(16,185,129,0.10)',  border:'rgba(16,185,129,0.25)' },
  GENERAL:   { label:'General',    color:'#6B7280', bg:'rgba(107,114,128,0.10)', border:'rgba(107,114,128,0.25)' },
}

export const NAV_ITEMS = [
  { id:'Home',                 label:'Home',            icon:'Home' },
  { id:'Dashboard',            label:'Dashboard',       icon:'BarChart2' },
  { id:'Loan Prediction',      label:'Loan Prediction', icon:'FileText' },
  { id:'Knowledge Assistant',  label:'Knowledge',       icon:'BookOpen' },
  { id:'Reports',              label:'Reports',         icon:'PieChart' },
  { id:'Data',                 label:'Export',          icon:'Download' },
]
