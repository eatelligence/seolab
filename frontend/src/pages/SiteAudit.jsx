import { useParams, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Activity, RefreshCcw } from 'lucide-react';
import { toast } from 'sonner';

import { auditApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { HealthRing } from '@/components/HealthRing';
import { StatusDot } from '@/components/ui/Badge';
import { fmtDateTime, fmtRelative } from '@/lib/format';
import { Empty } from '@/components/ui/Empty';

export default function SiteAudit() {
  const { projectId } = useParams();
  const qc = useQueryClient();

  const runsQ = useQuery({ queryKey: ['audit', 'runs', projectId], queryFn: () => auditApi.list(projectId, 30), refetchInterval: 8000 });
  const latest = runsQ.data?.[0];

  const start = useMutation({
    mutationFn: () => auditApi.start(projectId),
    onSuccess: () => {
      toast.success('Audit started');
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });

  const inFlight = runsQ.data?.some((r) => r.status === 'pending' || r.status === 'running');

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 04"
        title={<>Site <em className="text-signal not-italic">Audit</em></>}
        kicker="Async crawler · 14 SEO checks · Core Web Vitals sample · health score 0-100. Re-runs cascade through Celery beat (Mon 04:00 UTC)."
        action={
          <Button variant="primary" onClick={() => start.mutate()} loading={start.isPending} disabled={inFlight}>
            <RefreshCcw className="w-3.5 h-3.5" /> {inFlight ? 'running...' : 'run audit'}
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-px bg-line">
        <div className="bg-ink-200 p-6 flex flex-col items-center justify-center">
          {latest?.status === 'completed' && latest.health_score != null ? (
            <HealthRing score={latest.health_score} size={200} />
          ) : (
            <div className="text-center space-y-3">
              <Activity className="w-8 h-8 text-signal mx-auto opacity-60" />
              <p className="font-display text-5xl text-dim" style={{ fontVariationSettings: "'WONK' 1" }}>—</p>
              <p className="text-2xs font-mono uppercase tracking-widest2 text-dim">Awaiting audit</p>
            </div>
          )}
        </div>
        <div className="bg-ink-200 p-6">
          <SectionHeading eyebrow="● HISTORY / RUNS" title="Recent runs" kicker="Status updates every 8 seconds" />
          <div className="mt-6">
            {runsQ.isLoading ? (
              <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-12" />)}</div>
            ) : (runsQ.data || []).length === 0 ? (
              <Empty title="No runs yet" description="Trigger your first audit to start scoring." />
            ) : (
              <div className="space-y-px bg-line">
                {(runsQ.data || []).map((r, i) => (
                  <Link
                    key={r.id}
                    to={`/p/${projectId}/audit/runs/${r.id}`}
                    className="bg-ink-200 hover:bg-ink-100 px-4 py-4 flex items-center gap-4 transition-colors group"
                  >
                    <span className="font-mono text-2xs uppercase tracking-widest2 text-dim w-10">
                      {String((runsQ.data || []).length - i).padStart(3, '0')}
                    </span>
                    <StatusDot status={r.status} />
                    <span className="text-sm text-bone uppercase tracking-widest2 font-mono text-2xs w-24">{r.status}</span>
                    <div className="flex-1 grid grid-cols-3 gap-4 text-2xs font-mono uppercase tracking-widest2 text-dim">
                      <span>started <span className="text-bone num-mono">{fmtRelative(r.started_at || r.created_at)}</span></span>
                      <span>pages <span className="text-bone num-mono">{r.pages_crawled}</span></span>
                      <span>issues <span className="text-bone num-mono">{r.summary?.total ?? 0}</span></span>
                    </div>
                    <span className="num-display text-2xl text-bone group-hover:text-signal transition-colors"
                          style={{ fontVariationSettings: "'opsz' 72" }}>
                      {r.health_score ?? '—'}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
