import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { useProject } from './context/ProjectContext';

import Projects from './pages/Projects';
import Tags from './pages/Tags';
import ProjectSettings from './pages/ProjectSettings';
import Dashboard from './pages/Dashboard';
import Keywords from './pages/Keywords';
import RankTracker from './pages/RankTracker';
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

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/tags" element={<Tags />} />

        <Route path="/p/:projectId/dashboard" element={<Dashboard />} />
        <Route path="/p/:projectId/keywords" element={<Keywords />} />
        <Route path="/p/:projectId/rank-tracker" element={<RankTracker />} />
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
