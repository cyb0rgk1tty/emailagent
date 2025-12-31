import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Inbox from './pages/Inbox';
import Analytics from './pages/Analytics';
import Leads from './pages/Leads';
import Knowledge from './pages/Knowledge';
import ErrorBoundary, { PageErrorBoundary } from './components/ErrorBoundary';

function App(): JSX.Element {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route
            index
            element={
              <PageErrorBoundary pageName="Dashboard">
                <Dashboard />
              </PageErrorBoundary>
            }
          />
          <Route
            path="inbox"
            element={
              <PageErrorBoundary pageName="Inbox">
                <Inbox />
              </PageErrorBoundary>
            }
          />
          <Route
            path="analytics"
            element={
              <PageErrorBoundary pageName="Analytics">
                <Analytics />
              </PageErrorBoundary>
            }
          />
          <Route
            path="leads"
            element={
              <PageErrorBoundary pageName="Leads">
                <Leads />
              </PageErrorBoundary>
            }
          />
          <Route
            path="knowledge"
            element={
              <PageErrorBoundary pageName="Knowledge Base">
                <Knowledge />
              </PageErrorBoundary>
            }
          />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
