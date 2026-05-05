import { useState, useRef, useEffect } from 'react';
import { Check, ChevronsUpDown, Plus, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '@/context/ProjectContext';
import { cn } from '@/lib/utils';

export function ProjectSwitcher() {
  const { projects, active, setActiveId } = useProject();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onClick = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const filtered = projects.filter((p) =>
    !query || p.name.toLowerCase().includes(query.toLowerCase()) ||
    p.domain.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-3 py-2.5 border border-line bg-ink-200 hover:border-line2 transition-colors group"
      >
        <span className="flex items-center gap-3 min-w-0">
          <span className="w-7 h-7 shrink-0 grid place-items-center bg-ink-100 border border-line2">
            <span className="font-display text-sm text-signal" style={{ fontVariationSettings: "'WONK' 1" }}>
              {active?.name?.[0]?.toUpperCase() || '·'}
            </span>
          </span>
          <span className="flex flex-col items-start min-w-0">
            <span className="text-2xs font-mono uppercase tracking-widest2 text-dim">Project</span>
            <span className="text-sm text-bone font-sans truncate max-w-[160px]">
              {active?.name || 'No project'}
            </span>
          </span>
        </span>
        <ChevronsUpDown className="w-3.5 h-3.5 text-dim group-hover:text-bone shrink-0" />
      </button>

      {open && (
        <div className="absolute z-30 left-0 right-0 mt-1 panel max-h-[420px] overflow-hidden flex flex-col">
          <div className="relative border-b border-line">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-dim" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="search projects..."
              className="w-full h-9 pl-9 pr-3 bg-transparent text-sm font-mono text-bone placeholder:text-dim focus:outline-none"
            />
          </div>
          <div className="overflow-y-auto flex-1">
            {filtered.length === 0 ? (
              <div className="p-6 text-center text-2xs font-mono uppercase tracking-widest2 text-dim">
                No projects match
              </div>
            ) : (
              filtered.map((p) => {
                const active_ = p.id === active?.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => { setActiveId(p.id); setOpen(false); }}
                    className={cn(
                      'w-full flex items-center justify-between gap-3 px-3 py-2 text-left hover:bg-ink-100 transition-colors',
                      active_ && 'bg-ink-100',
                    )}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="w-1 h-6 bg-signal/60" style={{ opacity: active_ ? 1 : 0 }} />
                      <span className="flex flex-col min-w-0">
                        <span className="text-sm text-bone truncate">{p.name}</span>
                        <span className="text-2xs font-mono text-dim truncate">{p.domain}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {p.tags?.slice(0, 2).map((t) => (
                        <span key={t.id} className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-line2"
                          style={{ color: t.color, borderColor: t.color + '40' }}>
                          {t.name}
                        </span>
                      ))}
                      {active_ && <Check className="w-3.5 h-3.5 text-signal" />}
                    </div>
                  </button>
                );
              })
            )}
          </div>
          <button
            onClick={() => { setOpen(false); navigate('/projects'); }}
            className="flex items-center gap-2 px-3 py-2.5 border-t border-line text-2xs font-mono uppercase tracking-widest2 text-signal hover:bg-ink-100"
          >
            <Plus className="w-3.5 h-3.5" />
            new project
          </button>
        </div>
      )}
    </div>
  );
}
