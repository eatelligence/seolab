import { cn } from '@/lib/utils';

export function Skeleton({ className, ...props }) {
  return <div className={cn('shimmer h-4 w-full', className)} {...props} />;
}

export function SkeletonRows({ count = 5, className }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-9" />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }) {
  return (
    <div className={cn('panel p-5 space-y-3', className)}>
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-10 w-32" />
      <Skeleton className="h-2 w-full" />
    </div>
  );
}
