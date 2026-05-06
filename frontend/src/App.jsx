import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout';
import { useAuth } from './context/AuthContext';
import { useProject } from './context/ProjectContext';

import Login from './pages/Login';
import Account from './pages/Account';
import Projects from './pages/Projects';
import Tags from './pages/Tags';
import ProjectSettings from './pages/ProjectSettings';
import Dashboard from './pages/Dashboard';
import Keywords from './pages/Keywords';
import RankTracker from './pages/RankTracker';
import SerpOverview from './pages/SerpOverview';
import SiteAudit from './pages/SiteAudit';
import AuditRunDetail from './pages/AuditRunDetail';
import Backlinks from './pages/Backlinks';
import Competitors from './pages/Competitors';
import ContentTools from './pages/ContentTools';
import AIVisibility from './pages/AIVisibility';

function HomeRedirect() {
  const { active, isLoading } = useProject();
  if (isLoading) return null;
  if (active) return <Navigate to={`/p/${active.id}/dashboard`} replace />;
  return <Navigate to="/projects" replace />;
}

function RequireAuth({ children }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-400">
        <div className="font-mono text-2xs uppercase tracking-widest2 text-dim flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse-dot" />
          authenticating...
        </div>
      </div>
    );
  }
  if (status !== 'authed') {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return children;
}

function PublicOnly({ children }) {
  const { status } = useAuth();
  if (status === 'authed') return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />

      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/tags" element={<Tags />} />
        <Route path="/account" element={<Account />} />

        <Route path="/p/:projectId/dashboard" element={<Dashboard />} />
        <Route path="/p/:projectId/keywords" element={<Keywords />} />
        <Route path="/p/:projectId/rank-tracker" element={<RankTracker />} />
        <Route path="/p/:projectId/serp" element={<SerpOverview />} />
        <Route path="/p/:projectId/audit" element={<SiteAudit />} />
        <Route path="/p/:projectId/audit/runs/:runId" element={<AuditRunDetail />} />
        <Route path="/p/:projectId/backlinks" element={<Backlinks />} />
        <Route path="/p/:projectId/competitors" element={<Competitors />} />
        <Route path="/p/:projectId/content" element={<ContentTools />} />
        <Route path="/p/:projectId/ai-visibility" element={<AIVisibility />} />
        <Route path="/p/:projectId/settings" element={<ProjectSettings />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
