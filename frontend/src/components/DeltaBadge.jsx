import { cn } from '@/lib/utils';

export function DeltaBadge({ value, suffix = '%', invert = false, size = 'sm' }) {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  const positive = invert ? value < 0 : value > 0;
  const negative = invert ? value > 0 : value < 0;
  const symbol = value > 0 ? '▲' : value < 0 ? '▼' : '–';
  const color = positive ? 'text-plus' : negative ? 'text-minus' : 'text-dim';
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-mono uppercase tracking-widest2',
        size === 'sm' ? 'text-2xs' : 'text-xs',
        color,
      )}
    >
      <span className="text-[10px]">{symbol}</span>
      <span className="num-mono">
        {Math.abs(value).toFixed(1)}{suffix}
      </span>
    </span>
  );
}

export function PositionDelta({ delta }) {
  if (delta === null || delta === undefined || delta === 0) {
    return <span className="text-dim text-xs font-mono">—</span>;
  }
  const up = delta > 0; // moved up
  return (
    <span className={cn('inline-flex items-center gap-1 font-mono num-mono text-xs', up ? 'text-plus' : 'text-minus')}>
      <span className="text-[10px]">{up ? '▲' : '▼'}</span>
      {Math.abs(delta)}
    </span>
  );
}
