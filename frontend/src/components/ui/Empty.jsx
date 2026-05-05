import { cn } from '@/lib/utils';

export function Empty({ title, description, action, icon: Icon, className }) {
  return (
    <div className={cn('panel py-16 px-8 flex flex-col items-center text-center', className)}>
      <div className="w-12 h-12 mb-5 flex items-center justify-center border border-line2 stripes">
        {Icon && <Icon className="w-5 h-5 text-signal" />}
      </div>
      <p className="eyebrow mb-3">No data yet</p>
      <h3 className="font-display text-2xl text-bone mb-2" style={{ fontVariationSettings: "'opsz' 72, 'WONK' 1" }}>
        {title}
      </h3>
      {description && <p className="text-sm text-muted max-w-md">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
