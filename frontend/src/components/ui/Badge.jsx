import { cn } from '@/lib/utils';

const tones = {
  default: 'border-line text-muted',
  signal: 'border-signal/40 text-signal',
  plus: 'border-plus/40 text-plus',
  minus: 'border-minus/40 text-minus',
  warn: 'border-warn/40 text-warn',
  info: 'border-info/40 text-info',
};

export function Badge({ tone = 'default', className, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 border font-mono text-2xs uppercase tracking-widest2',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  const map = {
    high: { tone: 'minus', label: 'High' },
    medium: { tone: 'warn', label: 'Medium' },
    low: { tone: 'info', label: 'Low' },
  };
  const cfg = map[severity] || map.low;
  return (
    <Badge tone={cfg.tone}>
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full',
          cfg.tone === 'minus' && 'bg-minus',
          cfg.tone === 'warn' && 'bg-warn',
          cfg.tone === 'info' && 'bg-info',
        )}
      />
      {cfg.label}
    </Badge>
  );
}

export function StatusDot({ status }) {
  const map = {
    completed: 'bg-plus',
    running: 'bg-signal animate-pulse-dot',
    pending: 'bg-warn',
    failed: 'bg-minus',
  };
  return <span className={cn('inline-block w-2 h-2 rounded-full', map[status] || 'bg-dim')} />;
}
