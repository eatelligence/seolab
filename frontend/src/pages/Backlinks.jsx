import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Camera, Skull, Hash, Globe, ExternalLink } from 'lucide-react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { toast } from 'sonner';

import { backlinksApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { MetricCard } from '@/components/MetricCard';
import { Tabs } from '@/components/ui/Tabs';
import { DataTable } from '@/components/ui/DataTable';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/Badge';
import { fmtCompact, fmtNum, fmtPct, fmtRelative } from '@/lib/format';

export default function Backlinks() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState('refdomains');

  const overview = useQuery({ queryKey: ['bl', 'overview', projectId], queryFn: () => backlinksApi.overview(projectId) });
  const history = useQuery({ queryKey: ['bl', 'history', projectId], queryFn: () => backlinksApi.history(projectId, 90) });

  const refdomains = useQuery({ queryKey: ['bl', 'refdomains', projectId], queryFn: () => backlinksApi.refdomains(projectId, 200), enabled: tab === 'refdomains' });
  const list = useQuery({ queryKey: ['bl', 'list', projectId], queryFn: () => backlinksApi.list(projectId, 200), enabled: tab === 'list' });
  const anchors = useQuery({ queryKey: ['bl', 'anchors', projectId], queryFn: () => backlinksApi.anchors(projectId, 100), enabled: tab === 'anchors' });
  const toxic = useQuery({ queryKey: ['bl', 'toxic', projectId], queryFn: () => backlinksApi.toxic(projectId, 200), enabled: tab === 'toxic' });

  const snapshot = useMutation({
    mutationFn: () => backlinksApi.snapshot(projectId),
    onSuccess: () => {
      toast.success('Snapshot stored');
      qc.invalidateQueries({ queryKey: ['bl'] });
    },
  });

  const o = overview.data;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 05"
        title={<>Back<em className="text-signal not-italic">links</em></>}
        kicker="DataForSEO live index · Open PageRank for domain authority · daily snapshots persisted in Postgres."
        action={
          <Button variant="primary" loading={snapshot.isPending} onClick={() => snapshot.mutate()}>
            <Camera className="w-3.5 h-3.5" /> snapshot now
          </Button>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
        {overview.isLoading ? (
          <>{[1,2,3,4].map((i) => <SkeletonCard key={i} />)}</>
        ) : (
          <>
            <MetricCard label="● BACKLINKS / TOTAL" value={fmtCompact(o?.total_backlinks)} hint={`broken ${fmtCompact(o?.broken_backlinks)}`} />
            <MetricCard label="● REF. DOMAINS" value={fmtCompact(o?.referring_domains)} hint={`main ${fmtCompact(o?.referring_main_domains)}`} sparkColor="#60A5FA" />
            <MetricCard label="● DOFOLLOW / NF" value={`${fmtCompact(o?.dofollow)}`} unit={`/ ${fmtCompact(o?.nofollow)}`} sparkColor="#FACC15" />
            <MetricCard label="● DOMAIN AUTHORITY" value={fmtNum(o?.domain_authority, 1)} unit="/10" hint="Open PageRank" />
          </>
        )}
      </div>

      {history.data && history.data.length > 1 && (
        <div className="panel p-6">
          <SectionHeading eyebrow="● HISTORY / 90D" title="Backlink growth" kicker="Total backlinks per snapshot" />
          <div className="mt-6">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={history.data}>
                <defs>
                  <linearGradient id="bl-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D4F542" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#D4F542" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tickLine={false} axisLine={{ stroke: '#1F2632' }} interval="preserveStartEnd" />
                <YAxis tickLine={false} axisLine={false} tickFormatter={fmtCompact} width={48} />
                <Tooltip contentStyle={{ background: '#11151E', border: '1px solid #1F2632', borderRadius: 0, fontFamily: 'JetBrains Mono', fontSize: 11 }} />
                <Area type="monotone" dataKey="total_backlinks" stroke="#D4F542" strokeWidth={1.5} fill="url(#bl-grad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { value: 'refdomains', label: 'Referring Domains' },
          { value: 'list', label: 'Backlinks' },
          { value: 'anchors', label: 'Anchors' },
          { value: 'toxic', label: 'Toxic' },
        ]}
      />

      {tab === 'refdomains' && (
        <DataTable
          columns={[
            { key: 'domain', header: 'Domain', render: (r) => (
              <a href={`https://${r.domain}`} target="_blank" rel="noreferrer" className="text-bone hover:text-signal flex items-center gap-1.5 font-mono text-sm">
                <Globe className="w-3 h-3 text-dim" /> {r.domain}
              </a>
            )},
            { key: 'rank', header: 'Rank', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.rank, 0)}</span> },
            { key: 'backlinks', header: 'Links', align: 'right', render: (r) => <span className="num-mono text-bone">{fmtCompact(r.backlinks)}</span> },
            { key: 'is_lost', header: 'Status', render: (r) => r.is_lost ? <Badge tone="minus">Lost</Badge> : <Badge tone="plus">Live</Badge> },
            { key: 'last_seen', header: 'Last seen', align: 'right', render: (r) => <span className="text-2xs font-mono text-dim">{fmtRelative(r.last_seen)}</span> },
          ]}
          rows={refdomains.data || []}
          loading={refdomains.isLoading}
          keyField="domain"
        />
      )}

      {tab === 'list' && (
        <DataTable
          columns={[
            { key: 'source_domain', header: 'Source', render: (r) => <span className="text-bone font-mono text-sm">{r.source_domain}</span> },
            { key: 'anchor', header: 'Anchor', render: (r) => <span className="text-muted truncate max-w-[300px] block">{r.anchor || <span className="text-dim">—</span>}</span> },
            { key: 'is_dofollow', header: 'Type', render: (r) => r.is_dofollow ? <Badge tone="signal">dofollow</Badge> : <Badge>nofollow</Badge> },
            { key: 'rank', header: 'Rank', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.rank, 0)}</span> },
            { key: 'source_url', header: '', sortable: false, render: (r) => (
              <a href={r.source_url} target="_blank" rel="noreferrer" className="text-dim hover:text-signal"><ExternalLink className="w-3.5 h-3.5" /></a>
            )},
          ]}
          rows={list.data || []}
          loading={list.isLoading}
          keyField="source_url"
        />
      )}

      {tab === 'anchors' && (
        <DataTable
          columns={[
            { key: 'anchor', header: 'Anchor', render: (r) => <span className="text-bone">{r.anchor || <span className="text-dim italic">(empty)</span>}</span> },
            { key: 'backlinks', header: 'Links', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.backlinks)}</span> },
            { key: 'referring_domains', header: 'Domains', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtCompact(r.referring_domains)}</span> },
            { key: 'share', header: 'Share', align: 'right', render: (r) => (
              <div className="flex items-center justify-end gap-2">
                <div className="w-20 h-1 bg-ink-50 relative">
                  <div className="absolute inset-y-0 left-0 bg-signal" style={{ width: `${Math.min(100, r.share * 100)}%` }} />
                </div>
                <span className="num-mono text-bone w-12 text-right">{fmtPct(r.share, 1)}</span>
              </div>
            )},
          ]}
          rows={anchors.data || []}
          loading={anchors.isLoading}
          keyField="anchor"
        />
      )}

      {tab === 'toxic' && (
        <DataTable
          columns={[
            { key: 'source_domain', header: 'Source', render: (r) => (
              <span className="flex items-center gap-2 text-bone">
                <Skull className="w-3.5 h-3.5 text-minus" />
                <span className="font-mono text-sm">{r.source_domain}</span>
              </span>
            )},
            { key: 'anchor', header: 'Anchor', render: (r) => <span className="text-muted truncate max-w-[260px] block">{r.anchor || '—'}</span> },
            { key: 'domain_rating', header: 'DR', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.domain_rating, 1)}</span> },
            { key: 'is_dofollow', header: 'Type', render: (r) => r.is_dofollow ? <Badge tone="signal">dofollow</Badge> : <Badge>nofollow</Badge> },
            { key: 'toxic_score', header: 'Toxic', align: 'right', render: (r) => (
              <span className={`num-mono font-bold ${r.toxic_score > 0.7 ? 'text-minus' : 'text-warn'}`}>
                {fmtNum(r.toxic_score, 2)}
              </span>
            )},
          ]}
          rows={toxic.data || []}
          loading={toxic.isLoading}
          keyField="source_url"
        />
      )}
    </motion.div>
  );
}
