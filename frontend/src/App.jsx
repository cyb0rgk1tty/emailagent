import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Inbox from './pages/Inbox'
import Analytics from './pages/Analytics'
import Leads from './pages/Leads'
import Knowledge from './pages/Knowledge'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="inbox" element={<Inbox />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="leads" element={<Leads />} />
        <Route path="knowledge" element={<Knowledge />} />
      </Route>
    </Routes>
  )
}

export default App
