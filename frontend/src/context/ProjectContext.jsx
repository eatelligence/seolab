import { createContext, useContext, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';

const ProjectCtx = createContext(null);
const STORAGE_KEY = 'seolab.activeProjectId';

export function ProjectProvider({ children }) {
  const [activeId, setActiveId] = useState(() => localStorage.getItem(STORAGE_KEY) || null);

  const projectsQ = useQuery({
    queryKey: ['projects', 'list'],
    queryFn: () => projectsApi.list(),
  });

  useEffect(() => {
    if (!projectsQ.data) return;
    if (activeId && projectsQ.data.find((p) => p.id === activeId)) return;
    const fallback = projectsQ.data[0]?.id || null;
    setActiveId(fallback);
  }, [projectsQ.data, activeId]);

  useEffect(() => {
    if (activeId) localStorage.setItem(STORAGE_KEY, activeId);
    else localStorage.removeItem(STORAGE_KEY);
  }, [activeId]);

  const active = projectsQ.data?.find((p) => p.id === activeId) || null;

  return (
    <ProjectCtx.Provider value={{
      projects: projectsQ.data || [],
      active,
      activeId,
      setActiveId,
      isLoading: projectsQ.isLoading,
      refetch: projectsQ.refetch,
    }}>
      {children}
    </ProjectCtx.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectCtx);
  if (!ctx) throw new Error('useProject must be used within ProjectProvider');
  return ctx;
}
