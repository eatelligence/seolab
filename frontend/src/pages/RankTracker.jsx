import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { RefreshCw, Bell, X } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { toast } from 'sonner';

import { rankingsApi, keywordsApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Tabs } from '@/components/ui/Tabs';
import { DataTable } from '@/components/ui/DataTable';
import { Empty } from '@/components/ui/Empty';
import { PositionDelta } from '@/components/DeltaBadge';
import { Modal } from '@/components/ui/Modal';
import { fmtCompact, fmtNum, fmtRelative } from '@/lib/format';

export default function RankTracker() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState('current');
  const [selected, setSelected] = useState(null); // for history modal

  const rankingsQ = useQuery({ queryKey: ['rankings', projectId], queryFn: () => rankingsApi.list(projectId) });
  const visQ = useQuery({ queryKey: ['visibility', projectId], queryFn: () => rankingsApi.visibility(projectId, 90) });
  const alertsQ = useQuery({ queryKey: ['alerts', projectId], queryFn: () => rankingsApi.alerts(projectId, 7) });
  const allKwQ = useQuery({ queryKey: ['keywords', 'saved', projectId], queryFn: () => keywordsApi.list(projectId, { page_size: 500 }) });

  const checkNow = useMutation({
    mutationFn: () => rankingsApi.checkNow(projectId),
    onSuccess: (r) => {
      toast.success(`${r.checked} keywords checked`);
      qc.invalidateQueries({ queryKey: ['rankings', projectId] });
      qc.invalidateQueries({ queryKey: ['visibility', projectId] });
    },
  });

  const startTrack = useMutation({
    mutationFn: (kid) => rankingsApi.startTracking(projectId, kid),
    onSuccess: () => {
      toast.success('Tracking started');
      qc.invalidateQueries({ queryKey: ['keywords'] });
      qc.invalidateQueries({ queryKey: ['rankings'] });
    },
  });
  const stopTrack = useMutation({
    mutationFn: (kid) => rankingsApi.stopTracking(projectId, kid),
    onSuccess: () => {
      toast.success('Tracking stopped');
      qc.invalidateQueries({ queryKey: ['keywords'] });
      qc.invalidateQueries({ queryKey: ['rankings'] });
    },
  });

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 03"
        title={<>Rank <em className="text-signal not-italic">Tracker</em></>}
        kicker="Daily SERP positions via DataForSEO. Visibility uses a CTR-weighted curve. Alerts trigger when |delta| > 5 spots."
        action={
          <Button variant="primary" onClick={() => checkNow.mutate()} loading={checkNow.isPending}>
            <RefreshCw className="w-3.5 h-3.5" /> check now
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-px bg-line">
        <div className="bg-ink-200 p-6">
          <SectionHeading
            eyebrow="● VISIBILITY / 90D"
            title="Index trend"
            kicker="0–100 weighted by SERP position CTR"
          />
          <div className="mt-6">
            {visQ.data && visQ.data.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={visQ.data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke="#1F2632" strokeDasharray="2 4" vertical={false} />
                  <XAxis dataKey="date" tickLine={false} interval="preserveStartEnd" axisLine={{ stroke: '#1F2632' }} />
                  <YAxis tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    contentStyle={{ background: '#11151E', border: '1px solid #1F2632', borderRadius: 0, fontFamily: 'JetBrains Mono', fontSize: 11 }}
                  />
                  <Line type="monotone" dataKey="score" stroke="#D4F542" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[240px] stripes mt-2" />
            )}
          </div>
        </div>
        <div className="bg-ink-200 p-6">
          <SectionHeading eyebrow="● ALERTS / 7D" title="Significant shifts" />
          <div className="mt-4 space-y-2 max-h-[240px] overflow-y-auto">
            {alertsQ.data && alertsQ.data.length > 0 ? alertsQ.data.slice(0, 8).map((a, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-line/50">
                <Bell className="w-3 h-3 text-signal shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-bone truncate">{a.keyword}</p>
                  <p className="text-2xs font-mono text-dim">{fmtRelative(a.checked_at)}</p>
                </div>
                <PositionDelta delta={a.delta} />
              </div>
            )) : (
              <p className="text-2xs font-mono uppercase tracking-widest2 text-dim py-12 text-center">No alerts</p>
            )}
          </div>
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { value: 'current', label: 'Tracked', count: rankingsQ.data?.length },
          { value: 'all', label: 'All keywords', count: allKwQ.data?.total },
        ]}
      />

      {tab === 'current' && (
        <>
          {rankingsQ.data && rankingsQ.data.length === 0 ? (
            <Empty
              title="No tracked keywords"
              description="Switch to the All keywords tab to start tracking. The daily Celery beat will refresh positions automatically."
            />
          ) : (
            <DataTable
              columns={[
                { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
                { key: 'country', header: 'Geo', width: 80 },
                { key: 'current_position', header: 'Pos', align: 'right',
                  render: (r) => <span className="num-mono text-bone">{r.current_position ?? '>100'}</span> },
                { key: 'delta', header: 'Δ', align: 'right',
                  render: (r) => <PositionDelta delta={r.delta} /> },
                { key: 'search_volume', header: 'Volume', align: 'right',
                  render: (r) => <span className="num-mono text-muted">{fmtCompact(r.search_volume)}</span> },
                { key: 'serp_features', header: 'SERP feat.', sortable: false,
                  render: (r) => (
                    <div className="flex gap-1 flex-wrap">
                      {(r.serp_features || []).slice(0, 3).map((f) => (
                        <span key={f} className="text-[10px] font-mono uppercase tracking-widest2 px-1.5 py-0.5 border border-line2 text-muted">{f}</span>
                      ))}
                    </div>
                  ) },
                { key: 'last_checked', header: 'Checked', align: 'right',
                  render: (r) => <span className="text-2xs font-mono text-dim">{fmtRelative(r.last_checked)}</span> },
                {
                  key: '_act', header: '', sortable: false, width: 50,
                  render: (r) => (
                    <button
                      onClick={(e) => { e.stopPropagation(); stopTrack.mutate(r.keyword_id); }}
                      className="text-dim hover:text-minus"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  ),
                },
              ]}
              rows={rankingsQ.data || []}
              keyField="keyword_id"
              loading={rankingsQ.isLoading}
              rowAction={(r) => setSelected(r)}
            />
          )}
        </>
      )}

      {tab === 'all' && (
        <DataTable
          columns={[
            { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
            { key: 'country', header: 'Geo', width: 80 },
            { key: 'search_volume', header: 'Volume', align: 'right',
              render: (r) => <span className="num-mono">{fmtCompact(r.search_volume)}</span> },
            { key: 'tracked', header: 'Status',
              render: (r) => r.tracked ? <span className="text-2xs font-mono uppercase tracking-widest2 text-signal">● tracking</span> : <span className="text-2xs font-mono text-dim">off</span> },
            {
              key: '_act', header: '', sortable: false,
              render: (r) => r.tracked ? (
                <Button variant="outline" size="sm" onClick={() => stopTrack.mutate(r.id)}>stop</Button>
              ) : (
                <Button variant="primary" size="sm" onClick={() => startTrack.mutate(r.id)}>track</Button>
              ),
            },
          ]}
          rows={allKwQ.data?.items || []}
          loading={allKwQ.isLoading}
        />
      )}

      <HistoryModal projectId={projectId} keyword={selected} onClose={() => setSelected(null)} />
    </motion.div>
  );
}

function HistoryModal({ projectId, keyword, onClose }) {
  const historyQ = useQuery({
    queryKey: ['history', projectId, keyword?.keyword_id],
    queryFn: () => rankingsApi.history(projectId, keyword.keyword_id, 90),
    enabled: !!keyword,
  });

  if (!keyword) return null;

  return (
    <Modal
      open={!!keyword}
      onClose={onClose}
      eyebrow={`● POSITION HISTORY · ${keyword.country}`}
      title={keyword.keyword}
      size="lg"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-px bg-line">
          <Stat label="Current" value={keyword.current_position ?? '>100'} />
          <Stat label="Previous" value={keyword.previous_position ?? '>100'} />
          <Stat label="Delta" value={<PositionDelta delta={keyword.delta} />} />
        </div>
        <div className="h-72 mt-4">
          {historyQ.data && historyQ.data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyQ.data}>
                <CartesianGrid stroke="#1F2632" strokeDasharray="2 4" />
                <XAxis dataKey="checked_at" tickFormatter={(v) => v ? new Date(v).toLocaleDateString() : ''} />
                <YAxis reversed domain={[1, 100]} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#11151E', border: '1px solid #1F2632', borderRadius: 0, fontFamily: 'JetBrains Mono', fontSize: 11 }} />
                <Line type="monotone" dataKey="position" stroke="#D4F542" strokeWidth={1.5} dot={{ r: 2, fill: '#D4F542' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full stripes" />
          )}
        </div>
      </div>
    </Modal>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-ink-200 p-4">
      <p className="eyebrow !text-2xs mb-2">{label}</p>
      <p className="font-display text-3xl text-bone num-display" style={{ fontVariationSettings: "'opsz' 96" }}>
        {value}
      </p>
    </div>
  );
}
