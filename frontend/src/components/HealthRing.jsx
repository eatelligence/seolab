/**
 * Circular ring gauge with serif Fraunces number in the center. Distinctive
 * scientific-instrument feel — chartreuse glow when healthy.
 */
export function HealthRing({ score = 0, size = 180, strokeWidth = 8, label = 'HEALTH' }) {
  const safe = Math.max(0, Math.min(100, score || 0));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (safe / 100) * circumference;

  const tone =
    safe >= 80 ? '#4ADE80' :
    safe >= 60 ? '#D4F542' :
    safe >= 40 ? '#FACC15' :
    '#F87171';

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Tick marks around the ring */}
      <svg width={size} height={size} className="absolute inset-0">
        {Array.from({ length: 60 }).map((_, i) => {
          const angle = (i / 60) * Math.PI * 2 - Math.PI / 2;
          const inner = radius - 14;
          const outer = radius - (i % 5 === 0 ? 6 : 10);
          const x1 = size / 2 + Math.cos(angle) * inner;
          const y1 = size / 2 + Math.sin(angle) * inner;
          const x2 = size / 2 + Math.cos(angle) * outer;
          const y2 = size / 2 + Math.sin(angle) * outer;
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#1F2632" strokeWidth={1} />;
        })}
      </svg>

      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1F2632" strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={tone}
          strokeWidth={strokeWidth}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="butt"
          style={{ filter: `drop-shadow(0 0 6px ${tone}55)`, transition: 'stroke-dasharray 0.8s ease' }}
        />
      </svg>

      <div className="relative flex flex-col items-center">
        <span className="eyebrow !text-[9px] mb-1 text-dim before:!bg-dim">{label}</span>
        <span
          className="num-display text-[56px] leading-none"
          style={{ color: tone, fontVariationSettings: "'opsz' 144, 'WONK' 1" }}
        >
          {Math.round(safe)}
        </span>
        <span className="text-2xs font-mono uppercase tracking-widest2 text-dim mt-1">/ 100</span>
      </div>
    </div>
  );
}
