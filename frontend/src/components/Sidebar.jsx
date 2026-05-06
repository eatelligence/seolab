import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Search as SearchIcon, LineChart, Stethoscope,
  Link2, Users, FileText, Sparkles, FolderKanban, Tags, Settings,
  UserCircle2, LogOut, Globe2, ScanLine, Building2,
} from 'lucide-react';
import { useProject } from '@/context/ProjectContext';
import { useAuth } from '@/context/AuthContext';
import { ProjectSwitcher } from './ProjectSwitcher';
import { cn } from '@/lib/utils';

const sections = [
  {
    eyebrow: '01 / OVERVIEW',
    items: [
      { to: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', code: 'OV' },
    ],
  },
  {
    eyebrow: '02 / SEARCH',
    items: [
      { to: 'keywords', icon: SearchIcon, label: 'Keyword Research', code: 'KW' },
      { to: 'rank-tracker', icon: LineChart, label: 'Rank Tracker', code: 'RT' },
      { to: 'serp', icon: Globe2, label: 'SERP Overview', code: 'SP' },
    ],
  },
  {
    eyebrow: '03 / SITE',
    items: [
      { to: 'audit', icon: Stethoscope, label: 'Site Audit', code: 'SA' },
      { to: 'onpage', icon: ScanLine, label: 'On-page Checker', code: 'OP' },
      { to: 'backlinks', icon: Link2, label: 'Backlinks', code: 'BL' },
    ],
  },
  {
    eyebrow: '04 / INTELLIGENCE',
    items: [
      { to: 'domain', icon: Building2, label: 'Domain Overview', code: 'DO' },
      { to: 'competitors', icon: Users, label: 'Competitors', code: 'CP' },
      { to: 'content', icon: FileText, label: 'Content / AI', code: 'CO' },
      { to: 'ai-visibility', icon: Sparkles, label: 'AI Visibility', code: 'AV' },
    ],
  },
];

export function Sidebar() {
  const { active } = useProject();
  const { user, logout } = useAuth();

  return (
    <aside className="w-[260px] shrink-0 border-r border-line bg-ink-300 flex flex-col h-full">
      <div className="px-4 pt-5 pb-4 border-b border-line">
        <NavLink to="/" className="flex items-baseline gap-2 mb-5 group">
          <span className="font-display text-2xl text-bone tracking-tight" style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
            SEOLAB
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest2 text-signal">// 01</span>
        </NavLink>
        <ProjectSwitcher />
      </div>

      <nav className="flex-1 overflow-y-auto py-4 space-y-6">
        {sections.map((sec) => (
          <div key={sec.eyebrow} className="px-4">
            <p className="font-mono text-[10px] uppercase tracking-widest2 text-dim mb-2 pl-1">
              {sec.eyebrow}
            </p>
            <div className="space-y-px">
              {sec.items.map((item) => (
                <NavItem key={item.to} {...item} project={active} />
              ))}
            </div>
          </div>
        ))}

        <div className="px-4 pt-2 border-t border-line space-y-px">
          <p className="font-mono text-[10px] uppercase tracking-widest2 text-dim mt-4 mb-2 pl-1">
            05 / WORKSPACE
          </p>
          <NavLink to="/projects" className={navClass}>
            <FolderKanban className="w-3.5 h-3.5 text-signal/70" />
            <span className="text-sm">Projects</span>
            <span className="ml-auto font-mono text-[10px] text-dim">PR</span>
          </NavLink>
          <NavLink to="/tags" className={navClass}>
            <Tags className="w-3.5 h-3.5 text-signal/70" />
            <span className="text-sm">Tags</span>
            <span className="ml-auto font-mono text-[10px] text-dim">TG</span>
          </NavLink>
          {active && (
            <NavLink to={`/p/${active.id}/settings`} className={navClass}>
              <Settings className="w-3.5 h-3.5 text-signal/70" />
              <span className="text-sm">Settings</span>
              <span className="ml-auto font-mono text-[10px] text-dim">ST</span>
            </NavLink>
          )}
          <NavLink to="/account" className={navClass}>
            <UserCircle2 className="w-3.5 h-3.5 text-signal/70" />
            <span className="text-sm">Account</span>
            <span className="ml-auto font-mono text-[10px] text-dim">AC</span>
          </NavLink>
        </div>
      </nav>

      <div className="border-t border-line">
        {user && (
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-ink-200 transition-colors group"
          >
            <span className="w-7 h-7 shrink-0 grid place-items-center bg-ink-100 border border-line2">
              <span className="font-display text-sm text-signal" style={{ fontVariationSettings: "'WONK' 1" }}>
                {user.email?.[0]?.toUpperCase() || '·'}
              </span>
            </span>
            <span className="flex flex-col items-start min-w-0 flex-1">
              <span className="text-2xs font-mono uppercase tracking-widest2 text-dim">Signed in</span>
              <span className="text-xs text-bone font-mono truncate max-w-[150px]">{user.email}</span>
            </span>
            <LogOut className="w-3.5 h-3.5 text-dim group-hover:text-minus transition-colors" />
          </button>
        )}
        <p className="px-4 pb-3 text-2xs font-mono uppercase tracking-widest2 text-dim leading-relaxed">
          REC // <span className="text-signal animate-pulse-dot">●</span>
          <span className="text-dim/50 ml-2">v0.1.0 · 2026</span>
        </p>
      </div>
    </aside>
  );
}

function navClass({ isActive }) {
  return cn(
    'group flex items-center gap-3 pl-3 pr-2 py-2 transition-colors',
    'text-muted hover:text-bone hover:bg-ink-200',
    isActive && 'text-bone bg-ink-200 relative',
  );
}

function NavItem({ to, icon: Icon, label, code, project }) {
  if (!project) {
    return (
      <span className={cn(navClass({ isActive: false }), 'cursor-not-allowed opacity-30 hover:bg-transparent hover:text-muted')}>
        <Icon className="w-3.5 h-3.5 text-signal/70" />
        <span className="text-sm">{label}</span>
        <span className="ml-auto font-mono text-[10px] text-dim">{code}</span>
      </span>
    );
  }
  return (
    <NavLink to={`/p/${project.id}/${to}`} className={navClass}>
      {({ isActive }) => (
        <>
          {isActive && <span className="absolute left-0 top-2 bottom-2 w-px bg-signal" />}
          <Icon className={cn('w-3.5 h-3.5', isActive ? 'text-signal' : 'text-signal/70')} />
          <span className="text-sm">{label}</span>
          <span className="ml-auto font-mono text-[10px] text-dim">{code}</span>
        </>
      )}
    </NavLink>
  );
}
