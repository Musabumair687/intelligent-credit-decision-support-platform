import { useApp } from './context/AppContext'
import Login from './pages/Login/Login'
import Dashboard from './pages/Dashboard/Dashboard'
import LoanPrediction from './pages/LoanPrediction/LoanPrediction'
import KnowledgeAssistant from './pages/KnowledgeAssistant/KnowledgeAssistant'
import History from './pages/History/History'
import Settings from './pages/Settings/Settings'
import Sidebar from './components/Sidebar/Sidebar'
import FloatingAI from './components/FloatingAI/FloatingAI'

const PAGES = {
  'Dashboard': Dashboard,
  'Loan Prediction': LoanPrediction,
  'Knowledge Assistant': KnowledgeAssistant,
  'History': History,
  'Settings': Settings,
}

export default function App() {
  const { state } = useApp()

  if (!state.authenticated) return <Login />

  const PageComponent = PAGES[state.currentPage] || Dashboard

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content" key={state.currentPage}>
        <PageComponent />
      </main>
      <FloatingAI />
    </div>
  )
}
