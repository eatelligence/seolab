import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { dashboardApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { MetricCard } from '@/components/MetricCard';
import { HealthRing } from '@/components/HealthRing';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { Empty } from '@/components/ui/Empty';
import { fmtCompact, fmtInt, fmtNum } from '@/lib/format';
import { Globe2 } from 'lucide-react';

export default function Dashboard() {
  const { projectId } = useParams();
  const dashQ = useQuery({
    queryKey: ['dashboard', projectId],
    queryFn: () => dashboardApi.get(projectId, 90),
    enabled: !!projectId,
  });

  const d = dashQ.data;
  const traffic = d?.gsc_traffic?.series || [];
  const trafficSpark = traffic.map((t) => ({ v: t.clicks }));
  const traffic_total = d?.gsc_traffic?.totals?.clicks;
  const impressions_total = d?.gsc_traffic?.totals?.impressions;

  return (
    <motion.div
      initial="hidden" animate="visible"
      variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}
      className="space-y-10"
    >
      <motion.div variants={fadeIn}>
        <PageHeader
          eyebrow={`● PROJECT / ${d?.project?.domain || '—'}`}
          title={
            <>
              <em className="text-signal not-italic">{d?.project?.name || '...'}</em>
              <span className="text-muted/40 mx-3">·</span>
              <span>Overview</span>
            </>
          }
          kicker="Last 90 days · Aggregated from Google Search Console, DataForSEO, Open PageRank, internal rank tracker."
          meta={
            <>
              <span>region · {d?.project?.country || '—'}</span>
              <span className="text-line2">/</span>
              <span>gsc · {d?.project?.gsc_connected ? <span className="text-plus">linked</span> : <span className="text-warn">offline</span>}</span>
              <span className="text-line2">/</span>
              <span>tracking · <span className="num-mono text-bone">{d?.rank_overview?.tracked_count ?? '—'}</span> kw</span>
            </>
          }
        />
      </motion.div>

      {/* Headline strip */}
      <motion.section variants={fadeIn} className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
        {dashQ.isLoading ? (
          <>
            <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
          </>
        ) : (
          <>
            <MetricCard
              label="● ORGANIC / 90D"
              value={fmtCompact(traffic_total ?? 0)}
              unit="clicks"
              spark={trafficSpark}
              hint={`Impressions ${fmtCompact(impressions_total ?? 0)}`}
            />
            <MetricCard
              label="● KEYWORDS / TOTAL"
              value={fmtInt(d?.metrics?.total_keywords ?? 0)}
              hint={`Tracked ${d?.rank_overview?.tracked_count ?? 0}`}
              sparkColor="#60A5FA"
            />
            <MetricCard
              label="● VISIBILITY / IDX"
              value={fmtNum(d?.rank_overview?.visibility ?? 0, 1)}
              unit="/100"
              hint={d?.rank_overview?.avg_position ? `Avg position ${fmtNum(d.rank_overview.avg_position, 1)}` : 'Add tracked keywords'}
            />
            <MetricCard
              label="● DOMAIN AUTH"
              value={fmtNum(d?.metrics?.domain_authority ?? 0, 1)}
              unit="/10"
              hint={`Open PageRank · ${d?.backlinks?.referring_domains ?? 0} ref. domains`}
              sparkColor="#FACC15"
            />
          </>
        )}
      </motion.section>

      {/* Traffic chart */}
      <motion.section variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-line">
        <div className="lg:col-span-2 bg-ink-200 p-6">
          <SectionHeading
            eyebrow="● TRAFFIC / 90D"
            title="Organic clicks"
            kicker={d?.project?.gsc_connected ? 'Source: Google Search Console' : 'Connect GSC in /settings to populate'}
          />
          {!d?.project?.gsc_connected ? (
            <Empty
              icon={Globe2}
              title="GSC not linked"
              description="Connect Search Console to chart real organic traffic and impressions."
              className="mt-6"
            />
          ) : traffic.length === 0 ? (
            <div className="h-[320px] mt-6 stripes" />
          ) : (
            <div className="mt-6 -ml-4">
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={traffic} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="signal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#D4F542" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#D4F542" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#1F2632" strokeDasharray="2 4" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} axisLine={{ stroke: '#1F2632' }} interval="preserveStartEnd" />
                  <YAxis tickLine={false} axisLine={false} tickFormatter={(v) => fmtCompact(v)} width={48} />
                  <Tooltip
                    contentStyle={{
                      background: '#11151E', border: '1px solid #1F2632', borderRadius: 0,
                      fontFamily: 'JetBrains Mono', fontSize: 11, color: '#E5E7EB',
                    }}
                    labelStyle={{ color: '#5A6377', textTransform: 'uppercase', letterSpacing: '0.18em' }}
                  />
                  <Area type="monotone" dataKey="clicks" stroke="#D4F542" strokeWidth={1.5} fill="url(#signal)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Health gauge */}
        <div className="bg-ink-200 p-6 flex flex-col">
          <SectionHeading eyebrow="● AUDIT / SCORE" title="Site health" />
          <div className="flex-1 flex items-center justify-center py-6">
            {d?.audit?.latest_score ? (
              <HealthRing score={d.audit.latest_score} size={200} />
            ) : (
              <div className="text-center space-y-3">
                <p className="font-display text-5xl text-dim" style={{ fontVariationSettings: "'WONK' 1" }}>—</p>
                <p className="text-2xs font-mono uppercase tracking-widest2 text-dim">Run audit to score</p>
              </div>
            )}
          </div>
          <p className="font-mono text-2xs uppercase tracking-widest2 text-dim text-center">
            {d?.audit?.issues_count ?? 0} issues · last run
          </p>
        </div>
      </motion.section>

      {/* Top keywords + pages */}
      <motion.section variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-line">
        <TopKeywordsTable rows={d?.top_keywords || []} loading={dashQ.isLoading} />
        <TopPagesTable rows={d?.top_pages || []} loading={dashQ.isLoading} />
      </motion.section>
    </motion.div>
  );
}

const fadeIn = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
};

function TopKeywordsTable({ rows, loading }) {
  return (
    <div className="bg-ink-200 p-6">
      <SectionHeading eyebrow="● GSC / TOP KEYWORDS" title="Top 10" kicker="Last 28 days" />
      <div className="mt-6">
        {loading ? (
          <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="shimmer h-8" />)}</div>
        ) : rows.length === 0 ? (
          <p className="text-2xs font-mono uppercase tracking-widest2 text-dim py-12 text-center">No GSC data</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dim border-b border-line">
                <th className="text-left font-mono text-2xs uppercase tracking-widest2 font-normal pb-2">Keyword</th>
                <th className="text-right font-mono text-2xs uppercase tracking-widest2 font-normal pb-2">Clicks</th>
                <th className="text-right font-mono text-2xs uppercase tracking-widest2 font-normal pb-2">Pos</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 10).map((r) => (
                <tr key={r.keyword} className="border-b border-line/60">
                  <td className="py-2 truncate max-w-[260px] text-bone">{r.keyword}</td>
                  <td className="py-2 text-right num-mono text-bone">{fmtInt(r.clicks)}</td>
                  <td className="py-2 text-right num-mono text-muted">{fmtNum(r.position, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function TopPagesTable({ rows, loading }) {
  return (
    <div className="bg-ink-200 p-6">
      <SectionHeading eyebrow="● GSC / TOP PAGES" title="Top 5" kicker="By organic clicks" />
      <div className="mt-6 space-y-2">
        {loading ? (
          <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-12" />)}</div>
        ) : rows.length === 0 ? (
          <p className="text-2xs font-mono uppercase tracking-widest2 text-dim py-12 text-center">No GSC data</p>
        ) : (
          rows.slice(0, 5).map((r, i) => (
            <div key={r.page} className="flex items-baseline gap-3 py-2 border-b border-line/40">
              <span className="font-mono text-2xs text-dim num-mono w-6">{String(i + 1).padStart(2, '0')}</span>
              <a href={r.page} target="_blank" rel="noreferrer" className="flex-1 text-sm text-bone hover:text-signal truncate transition-colors">
                {(() => {
                  try { return new URL(r.page).pathname || '/'; } catch { return r.page; }
                })()}
              </a>
              <span className="num-mono text-sm text-bone">{fmtInt(r.clicks)}</span>
              <span className="num-mono text-2xs text-dim">·</span>
              <span className="num-mono text-2xs text-dim">{fmtNum(r.position, 1)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
