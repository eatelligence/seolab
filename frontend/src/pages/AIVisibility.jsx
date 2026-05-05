import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Sparkles, Plus, RefreshCcw, Lightbulb } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { toast } from 'sonner';

import { aiVisApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DataTable } from '@/components/ui/DataTable';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { MetricCard } from '@/components/MetricCard';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { Empty } from '@/components/ui/Empty';
import { fmtPct, fmtRelative } from '@/lib/format';

export default function AIVisibility() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const [newQuery, setNewQuery] = useState('');
  const [openCheck, setOpenCheck] = useState(null);

  const queriesQ = useQuery({ queryKey: ['av', 'queries', projectId], queryFn: () => aiVisApi.queries(projectId) });
  const overviewQ = useQuery({ queryKey: ['av', 'overview', projectId], queryFn: () => aiVisApi.overview(projectId, 30) });
  const historyQ = useQuery({ queryKey: ['av', 'history', projectId], queryFn: () => aiVisApi.history(projectId, 90) });
  const sugQ = useQuery({ queryKey: ['av', 'sug', projectId], queryFn: () => aiVisApi.suggestions(projectId), enabled: false });

  const create = useMutation({
    mutationFn: (query) => aiVisApi.createQuery(projectId, { query }),
    onSuccess: () => { setNewQuery(''); toast.success('Query added'); qc.invalidateQueries({ queryKey: ['av'] }); },
  });
  const checkAll = useMutation({
    mutationFn: () => aiVisApi.checkAll(projectId),
    onSuccess: (r) => { toast.success(`${r.checked} queries checked`); qc.invalidateQueries({ queryKey: ['av'] }); },
  });
  const checkOne = useMutation({
    mutationFn: (qid) => aiVisApi.checkOne(projectId, qid),
    onSuccess: () => { toast.success('Check complete'); qc.invalidateQueries({ queryKey: ['av'] }); },
  });
  const remove = useMutation({
    mutationFn: (qid) => aiVisApi.removeQuery(projectId, qid),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['av'] }); },
  });

  const o = overviewQ.data;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 08"
        title={<>AI <em className="text-signal not-italic">Visibility</em></>}
        kicker="GEO / LLMO. Track how often your brand surfaces in AI assistant responses, with sentiment and competitor share."
        action={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => sugQ.refetch()} loading={sugQ.isFetching}>
              <Lightbulb className="w-3.5 h-3.5" /> recommendations
            </Button>
            <Button variant="primary" onClick={() => checkAll.mutate()} loading={checkAll.isPending}>
              <RefreshCcw className="w-3.5 h-3.5" /> check all
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
        {overviewQ.isLoading ? (
          [1,2,3,4].map((i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <MetricCard label="● MENTION RATE / 30D" value={fmtPct(o?.mention_rate, 1)} hint={`${o?.checks ?? 0} checks`} />
            <MetricCard label="● SENTIMENT / AVG" value={o?.avg_sentiment_score != null ? o.avg_sentiment_score.toFixed(2) : '—'} unit="-1..+1" sparkColor={o?.avg_sentiment_score > 0 ? '#4ADE80' : '#F87171'} />
            <MetricCard label="● QUERIES / TRACKED" value={o?.queries_tracked ?? 0} sparkColor="#60A5FA" />
            <MetricCard label="● COMPETITORS" value={o?.competitor_share?.length ?? 0} hint="distinct mentioned" />
          </>
        )}
      </div>

      {historyQ.data && historyQ.data.length > 0 && (
        <div className="panel p-6">
          <SectionHeading eyebrow="● HISTORY / 90D" title="Mention rate trend" />
          <div className="mt-6">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={historyQ.data}>
                <CartesianGrid stroke="#1F2632" strokeDasharray="2 4" />
                <XAxis dataKey="date" tickLine={false} axisLine={{ stroke: '#1F2632' }} />
                <YAxis tickLine={false} axisLine={false} domain={[0, 1]} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} width={48} />
                <Tooltip contentStyle={{ background: '#11151E', border: '1px solid #1F2632', borderRadius: 0, fontFamily: 'JetBrains Mono', fontSize: 11 }} />
                <Line type="monotone" dataKey="mention_rate" stroke="#D4F542" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {o?.competitor_share?.length > 0 && (
        <div className="panel p-6">
          <SectionHeading eyebrow="● SHARE OF VOICE / 30D" title="Competitor mentions" />
          <div className="mt-4 space-y-px bg-line">
            {o.competitor_share.map((c, i) => (
              <div key={i} className="bg-ink-200 px-4 py-2.5 flex items-center gap-4">
                <span className="num-mono text-2xs text-dim w-6">{String(i + 1).padStart(2, '0')}</span>
                <span className="text-sm text-bone flex-1">{c.competitor}</span>
                <span className="num-mono text-bone">{c.mentions}</span>
                <div className="w-40 h-1 bg-ink-50 relative">
                  <div className="absolute inset-y-0 left-0 bg-info" style={{ width: `${Math.min(100, c.share * 100)}%` }} />
                </div>
                <span className="num-mono text-2xs text-muted w-12 text-right">{fmtPct(c.share, 1)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <SectionHeading eyebrow="● TRACKED QUERIES" title="Prompts" kicker="Each query is asked to Claude, then scanned for brand mentions and sentiment." />

      <div className="panel p-5">
        <form
          className="flex gap-3"
          onSubmit={(e) => { e.preventDefault(); if (newQuery.trim()) create.mutate(newQuery.trim()); }}
        >
          <input
            value={newQuery}
            onChange={(e) => setNewQuery(e.target.value)}
            placeholder="e.g. best email marketing tools for small business"
            className="flex-1 h-9 px-3 bg-ink-100 border border-line text-bone text-sm font-mono placeholder:text-dim focus:border-signal/60 focus-ring"
          />
          <Button variant="primary" type="submit" loading={create.isPending}><Plus className="w-3.5 h-3.5" /> add prompt</Button>
        </form>
      </div>

      {(queriesQ.data || []).length === 0 && !queriesQ.isLoading ? (
        <Empty
          icon={Sparkles}
          title="No tracked queries"
          description="Add prompts that real users would ask an AI assistant about your industry. Daily Celery checks track mention rate over time."
        />
      ) : (
        <DataTable
          columns={[
            { key: 'query', header: 'Prompt', render: (r) => <span className="text-bone">{r.query}</span> },
            { key: 'enabled', header: 'Status', render: (r) => r.enabled ? <Badge tone="signal">● ON</Badge> : <Badge>off</Badge> },
            { key: 'created_at', header: 'Added', align: 'right', render: (r) => <span className="text-2xs font-mono text-dim">{fmtRelative(r.created_at)}</span> },
            {
              key: '_act', header: '', sortable: false,
              render: (r) => (
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); checkOne.mutate(r.id); }} loading={checkOne.isPending}>check</Button>
                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); setOpenCheck(r); }}>history</Button>
                  <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); if (window.confirm('Delete prompt?')) remove.mutate(r.id); }}>×</Button>
                </div>
              ),
            },
          ]}
          rows={queriesQ.data || []}
          loading={queriesQ.isLoading}
          rowAction={(r) => setOpenCheck(r)}
        />
      )}

      <CheckHistoryModal projectId={projectId} query={openCheck} onClose={() => setOpenCheck(null)} />

      <SuggestionsModal data={sugQ.data} open={sugQ.isFetched && !sugQ.isFetching && !!sugQ.data} onClose={() => sugQ.remove()} />
    </motion.div>
  );
}

function CheckHistoryModal({ projectId, query, onClose }) {
  const checksQ = useQuery({
    queryKey: ['av', 'checks', projectId, query?.id],
    queryFn: () => aiVisApi.checks(projectId, query.id, 30),
    enabled: !!query,
  });
  if (!query) return null;
  return (
    <Modal open={!!query} onClose={onClose} eyebrow="● PROMPT HISTORY" title={query.query} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        {(checksQ.data || []).map((c) => (
          <div key={c.id} className="panel-soft p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xs font-mono text-dim">{fmtRelative(c.checked_at)}</span>
              {c.brand_mentioned ? <Badge tone="signal">● mentioned</Badge> : <Badge tone="minus">absent</Badge>}
              {c.sentiment && <Badge tone={c.sentiment === 'positive' ? 'plus' : c.sentiment === 'negative' ? 'minus' : 'default'}>
                {c.sentiment} {c.sentiment_score != null && `(${c.sentiment_score.toFixed(2)})`}
              </Badge>}
              {c.competitors_mentioned?.length > 0 && (
                <span className="text-2xs font-mono text-dim">competitors: {c.competitors_mentioned.join(', ')}</span>
              )}
            </div>
            <p className="text-sm text-muted whitespace-pre-wrap leading-relaxed">{c.response_text}</p>
          </div>
        ))}
        {(!checksQ.data || checksQ.data.length === 0) && (
          <p className="text-center text-2xs font-mono text-dim py-12">No checks yet</p>
        )}
      </div>
    </Modal>
  );
}

function SuggestionsModal({ data, open, onClose }) {
  if (!open) return null;
  return (
    <Modal open onClose={onClose} eyebrow="● AI / RECOMMENDATIONS" title="Improve AI visibility" size="lg">
      <div className="prose prose-invert max-w-none text-sm whitespace-pre-wrap font-sans text-bone leading-relaxed">
        {data?.markdown || 'No recommendations yet.'}
      </div>
    </Modal>
  );
}
