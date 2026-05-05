import { cn } from '@/lib/utils';

export function SectionHeading({ eyebrow, title, kicker, action, className }) {
  return (
    <div className={cn('flex items-end justify-between gap-6 pb-4 border-b border-line', className)}>
      <div>
        {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
        <h2
          className="font-display text-bone text-3xl leading-none"
          style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1", letterSpacing: '-0.02em' }}
        >
          {title}
        </h2>
        {kicker && <p className="text-sm text-muted mt-2 font-sans">{kicker}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function PageHeader({ eyebrow, title, kicker, action, meta }) {
  return (
    <header className="pb-8 border-b border-line">
      <div className="flex items-end justify-between gap-6 flex-wrap">
        <div>
          {eyebrow && <p className="eyebrow mb-4">{eyebrow}</p>}
          <h1
            className="page-title"
            style={{ fontVariationSettings: "'opsz' 144, 'WONK' 1", letterSpacing: '-0.025em' }}
          >
            {title}
          </h1>
          {kicker && <p className="text-base text-muted mt-3 max-w-2xl">{kicker}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {meta && (
        <div className="mt-6 flex flex-wrap items-center gap-x-8 gap-y-2 font-mono text-2xs uppercase tracking-widest2 text-dim">
          {meta}
        </div>
      )}
    </header>
  );
}
