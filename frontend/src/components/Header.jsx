import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useProject } from '@/context/ProjectContext';

const PAGE_LABELS = {
  dashboard: 'Dashboard',
  keywords: 'Keyword Research',
  'rank-tracker': 'Rank Tracker',
  audit: 'Site Audit',
  backlinks: 'Backlinks',
  competitors: 'Competitors',
  content: 'Content & AI',
  'ai-visibility': 'AI Visibility',
  settings: 'Project Settings',
  projects: 'Projects',
  tags: 'Tags',
};

export function Header() {
  const location = useLocation();
  const { active } = useProject();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(t);
  }, []);

  const last = location.pathname.split('/').filter(Boolean).pop();
  const pageLabel = PAGE_LABELS[last] || (active ? active.name : 'SEOLAB');

  return (
    <header className="h-12 border-b border-line bg-ink-300/80 backdrop-blur sticky top-0 z-20">
      <div className="h-full px-6 flex items-center justify-between text-2xs font-mono uppercase tracking-widest2">
        <div className="flex items-center gap-6 text-dim">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse-dot" />
            <span className="text-bone">{pageLabel}</span>
          </span>
          {active && (
            <>
              <span className="text-line2">/</span>
              <span>{active.domain}</span>
              <span className="text-line2">/</span>
              <span>{active.country}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-6 text-dim">
          <span className="num-mono">{now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} UTC</span>
          <span className="text-line2">/</span>
          <span>SYS · OK</span>
        </div>
      </div>
    </header>
  );
}
