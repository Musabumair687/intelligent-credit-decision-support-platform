import { createContext, useContext, useReducer } from 'react'

const genId = () => 'sess-' + Math.random().toString(36).slice(2,10)

const init = {
  authenticated: false,
  theme: 'dark',        // 'dark' | 'light'
  apiBase: 'http://127.0.0.1:8000',
  sessionId: genId(),
  page: 'Home',
  history: [],
  lastPrediction: null,
  lastApplicant: null,
  probTrend: [],
  decisionChat: [],
  kbChat: [],
}

function reducer(s, a) {
  switch(a.type) {
    case 'LOGIN':       return { ...s, authenticated: true }
    case 'LOGOUT':      return { ...init, authenticated: false, theme: s.theme, sessionId: genId() }
    case 'NAV':         return { ...s, page: a.payload }
    case 'TOGGLE_THEME':return { ...s, theme: s.theme === 'dark' ? 'light' : 'dark' }
    case 'PREDICT':     return { ...s, lastApplicant: a.payload.applicant, lastPrediction: a.payload.prediction, decisionChat: [], probTrend: [...s.probTrend, a.payload.prediction.repayment_probability] }
    case 'ADD_HIST':    return { ...s, history: [a.payload, ...s.history] }
    case 'CLR_HIST':    return { ...s, history: [] }
    case 'ADD_DC':      return { ...s, decisionChat: [...s.decisionChat, a.payload] }
    case 'CLR_DC':      return { ...s, decisionChat: [] }
    case 'ADD_KB':      return { ...s, kbChat: [...s.kbChat, a.payload] }
    default: return s
  }
}

const Ctx = createContext(null)

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, init)
  // Apply theme to document
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', state.theme)
  }
  return <Ctx.Provider value={{ state, dispatch }}>{children}</Ctx.Provider>
}

export function useApp() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useApp outside AppProvider')
  return c
}
