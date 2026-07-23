import { useEffect } from 'react'
import { useApp } from './context/AppContext'
import Login from './pages/Login'
import Nav from './components/Nav'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import LoanPrediction from './pages/LoanPrediction'
import KnowledgeAssistant from './pages/KnowledgeAssistant'
import Reports from './pages/Reports'
import DataExport from './pages/DataExport'

const PAGES = {
  'Home': Home,
  'Dashboard': Dashboard,
  'Loan Prediction': LoanPrediction,
  'Knowledge Assistant': KnowledgeAssistant,
  'Reports': Reports,
  'Data': DataExport,
}

export default function App() {
  const { state } = useApp()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', state.theme)
  }, [state.theme])

  if (!state.authenticated) return <Login />

  const Page = PAGES[state.page] || Home
  return (
    <div>
      <Nav />
      <div className="page-wrap">
        <div className="main">
          <Page />
        </div>
      </div>
    </div>
  )
}
