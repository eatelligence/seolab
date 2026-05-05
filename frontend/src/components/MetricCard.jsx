import { cn } from '@/lib/utils';
import { Sparkline } from './Sparkline';
import { DeltaBadge } from './DeltaBadge';

/**
 * SEMrush-killer metric card. Anatomy:
 *   ┌──────────────────────────────────┐
 *   │ ●  ORG. CLICKS / 90D    ▲ 12.4% │   <- eyebrow + delta
 *   │                                  │
 *   │ 142,308                          │   <- giant Fraunces tabular display
 *   │ ··········                       │   <- inline sparkline
 *   │ vs prior period: 126,512         │
 *   └──────────────────────────────────┘
 */
export function MetricCard({
  label,
  value,
  unit,
  delta,
  deltaSuffix = '%',
  spark,
  sparkColor,
  hint,
  invert = false, // true -> down=positive (e.g. avg position)
  className,
  loading = false,
}) {
  return (
    <div className={cn('panel p-5 group relative overflow-hidden', className)}>
      <div className="flex items-start justify-between gap-3 mb-5">
        <p className="eyebrow">{label}</p>
        {delta !== undefined && delta !== null && (
          <DeltaBadge value={delta} suffix={deltaSuffix} invert={invert} />
        )}
      </div>

      <div className="flex items-end gap-2">
        {loading ? (
          <span className="shimmer h-10 w-32" />
        ) : (
          <>
            <span className="num-display text-[40px] leading-none text-bone">
              {value}
            </span>
            {unit && (
              <span className="text-muted text-xs font-mono uppercase pb-1">{unit}</span>
            )}
          </>
        )}
      </div>

      {spark && (
        <div className="mt-4 -mx-1">
          <Sparkline data={spark} color={sparkColor} />
        </div>
      )}

      {hint && (
        <p className="mt-3 text-xs text-muted font-mono">{hint}</p>
      )}

      {/* corner ticks */}
      <span className="absolute top-0 left-0 w-2 h-px bg-signal/40" />
      <span className="absolute top-0 left-0 w-px h-2 bg-signal/40" />
    </div>
  );
}
