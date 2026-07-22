import { createContext, useContext, useReducer } from 'react'

const genSessionId = () => 'sess-' + Math.random().toString(36).substring(2, 10)

const initialState = {
  authenticated: false,
  apiBase: 'http://127.0.0.1:8000',
  sessionId: genSessionId(),
  currentPage: 'Dashboard',
  navGroupOpen: 'workspace',
  history: [],
  lastApplicant: null,
  lastPrediction: null,
  probTrend: [],
  decisionChat: [],
  kbChat: [],
  pendingQuestion: null,
}

function reducer(state, action) {
  switch (action.type) {
    case 'LOGIN':
      return { ...state, authenticated: true }
    case 'LOGOUT':
      return { ...initialState, authenticated: false, sessionId: genSessionId() }
    case 'SET_PAGE':
      return { ...state, currentPage: action.payload }
    case 'SET_NAV_GROUP':
      return { ...state, navGroupOpen: action.payload }
    case 'SET_PREDICTION':
      return {
        ...state,
        lastApplicant: action.payload.applicant,
        lastPrediction: action.payload.prediction,
        decisionChat: [],
        probTrend: [...state.probTrend, action.payload.prediction.repayment_probability],
      }
    case 'ADD_HISTORY':
      return { ...state, history: [action.payload, ...state.history] }
    case 'CLEAR_HISTORY':
      return { ...state, history: [] }
    case 'ADD_DECISION_CHAT':
      return { ...state, decisionChat: [...state.decisionChat, action.payload] }
    case 'CLEAR_DECISION_CHAT':
      return { ...state, decisionChat: [] }
    case 'ADD_KB_CHAT':
      return { ...state, kbChat: [...state.kbChat, action.payload] }
    case 'SET_PENDING_QUESTION':
      return { ...state, pendingQuestion: action.payload }
    case 'UPDATE_SETTINGS':
      return { ...state, apiBase: action.payload.apiBase, sessionId: action.payload.sessionId }
    case 'ADD_PROB_TREND':
      return { ...state, probTrend: [...state.probTrend, action.payload] }
    default:
      return state
  }
}

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used within AppProvider')
  return context
}
