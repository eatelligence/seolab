import { forwardRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export const Select = forwardRef(function Select(
  { className, label, options = [], children, ...props },
  ref,
) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="eyebrow !text-2xs">{label}</span>}
      <div className="relative">
        <select
          ref={ref}
          className={cn(
            'h-9 pl-3 pr-9 w-full bg-ink-100 border border-line text-bone text-sm font-mono appearance-none',
            'focus:border-signal/60 focus:bg-ink-200 transition-colors focus-ring',
            className,
          )}
          {...props}
        >
          {children
            ? children
            : options.map((o) =>
                typeof o === 'string' ? (
                  <option key={o} value={o}>{o}</option>
                ) : (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ),
              )}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dim pointer-events-none" />
      </div>
    </label>
  );
});
