import { cn } from '@/lib/utils';

const variants = {
  primary:
    'bg-signal text-ink-400 hover:bg-signal-glow border-signal hover:shadow-glow',
  ghost:
    'bg-transparent text-bone hover:bg-ink-100 border-line hover:border-line2',
  outline:
    'bg-transparent text-bone hover:bg-ink-100 border-line2',
  danger:
    'bg-transparent text-minus hover:bg-minus/10 border-minus/30',
  subtle:
    'bg-ink-100 text-bone hover:bg-ink-50 border-transparent',
};

const sizes = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
  icon: 'h-9 w-9',
};

export function Button({
  variant = 'ghost',
  size = 'md',
  className,
  loading = false,
  children,
  ...props
}) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 border font-mono uppercase tracking-widest2 text-2xs select-none transition-colors focus-ring disabled:opacity-40 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && (
        <span className="w-3 h-3 border border-current border-r-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
}
