import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const Input = forwardRef(function Input(
  { className, label, hint, error, ...props },
  ref,
) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && (
        <span className="eyebrow !text-2xs">{label}</span>
      )}
      <input
        ref={ref}
        className={cn(
          'h-9 px-3 bg-ink-100 border border-line text-bone text-sm font-mono',
          'placeholder:text-dim placeholder:font-sans placeholder:text-sm',
          'focus:border-signal/60 focus:bg-ink-200 transition-colors focus-ring',
          error && 'border-minus/60',
          className,
        )}
        {...props}
      />
      {hint && !error && <span className="text-xs text-dim font-sans">{hint}</span>}
      {error && <span className="text-xs text-minus font-mono">{error}</span>}
    </label>
  );
});

export const Textarea = forwardRef(function Textarea(
  { className, label, hint, error, ...props },
  ref,
) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="eyebrow !text-2xs">{label}</span>}
      <textarea
        ref={ref}
        className={cn(
          'min-h-[120px] p-3 bg-ink-100 border border-line text-bone text-sm font-mono',
          'placeholder:text-dim placeholder:font-sans focus:border-signal/60 focus:bg-ink-200',
          'transition-colors focus-ring resize-y',
          error && 'border-minus/60',
          className,
        )}
        {...props}
      />
      {hint && !error && <span className="text-xs text-dim font-sans">{hint}</span>}
      {error && <span className="text-xs text-minus font-mono">{error}</span>}
    </label>
  );
});
