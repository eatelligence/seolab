import { cn } from '@/lib/utils';

export function Tabs({ tabs, value, onChange, className }) {
  return (
    <div className={cn('flex items-end gap-6 border-b border-line', className)}>
      {tabs.map((t) => {
        const active = t.value === value;
        return (
          <button
            key={t.value}
            onClick={() => onChange(t.value)}
            className={cn(
              'relative pb-3 -mb-px font-mono text-2xs uppercase tracking-widest2 transition-colors',
              active ? 'text-bone' : 'text-dim hover:text-muted',
            )}
          >
            <span className="flex items-center gap-2">
              {active && <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse-dot" />}
              {t.label}
              {t.count !== undefined && (
                <span className="text-dim num-mono">[{t.count}]</span>
              )}
            </span>
            {active && <span className="absolute -bottom-px left-0 right-0 h-px bg-signal" />}
          </button>
        );
      })}
    </div>
  );
}
