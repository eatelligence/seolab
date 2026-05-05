import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowLeft, Download } from 'lucide-react';

import { auditApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { HealthRing } from '@/components/HealthRing';
import { Tabs } from '@/components/ui/Tabs';
import { DataTable } from '@/components/ui/DataTable';
import { SeverityBadge, StatusDot } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fmtDateTime, fmtInt } from '@/lib/format';

export default function AuditRunDetail() {
  const { projectId, runId } = useParams();
  const [tab, setTab] = useState('issues');
  const [severity, setSeverity] = useState(null);

  const runQ = useQuery({ queryKey: ['audit', 'run', runId], queryFn: () => auditApi.get(projectId, runId) });
  const issuesQ = useQuery({
    queryKey: ['audit', 'issues', runId, severity],
    queryFn: () => auditApi.issues(projectId, runId, { severity, page_size: 500 }),
  });
  const pagesQ = useQuery({
    queryKey: ['audit', 'pages', runId],
    queryFn: () => auditApi.pages(projectId, runId, { page_size: 500 }),
  });

  const summary = runQ.data?.summary || {};
  const byType = summary.by_type || {};

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <Link to={`/p/${projectId}/audit`} className="text-2xs font-mono uppercase tracking-widest2 text-dim hover:text-bone inline-flex items-center gap-2">
        <ArrowLeft className="w-3 h-3" /> back to audits
      </Link>

      <PageHeader
        eyebrow={`● RUN / ${runId.slice(0, 8)}`}
        title={<>Audit run <em className="text-signal not-italic">/ detail</em></>}
        kicker={runQ.data ? `Started ${fmtDateTime(runQ.data.started_at || runQ.data.created_at)}` : 'Loading...'}
        action={
          <a href={auditApi.pdfUrl(projectId, runId)} target="_blank" rel="noreferrer">
            <Button variant="outline"><Download className="w-3.5 h-3.5" /> download PDF</Button>
          </a>
        }
        meta={
          runQ.data && (
            <>
              <span className="flex items-center gap-2"><StatusDot status={runQ.data.status} /> {runQ.data.status}</span>
              <span className="text-line2">/</span>
              <span>pages <span className="text-bone num-mono">{runQ.data.pages_crawled}</span></span>
              <span className="text-line2">/</span>
              <span>total issues <span className="text-bone num-mono">{summary.total ?? 0}</span></span>
            </>
          )
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-px bg-line">
        <div className="bg-ink-200 p-6 flex items-center justify-center">
          {runQ.data?.health_score != null ? (
            <HealthRing score={runQ.data.health_score} size={200} />
          ) : (
            <div className="h-[200px] w-[200px] stripes" />
          )}
        </div>

        <div className="bg-ink-200 p-6">
          <SectionHeading eyebrow="● BREAKDOWN" title="Issues by severity" />
          <div className="grid grid-cols-3 gap-px bg-line mt-6">
            <SeverityBlock label="High" value={summary.by_severity?.high ?? 0} color="#F87171" onClick={() => setSeverity('high')} />
            <SeverityBlock label="Medium" value={summary.by_severity?.medium ?? 0} color="#FACC15" onClick={() => setSeverity('medium')} />
            <SeverityBlock label="Low" value={summary.by_severity?.low ?? 0} color="#60A5FA" onClick={() => setSeverity('low')} />
          </div>

          <SectionHeading eyebrow="● BY TYPE" title="Top issue types" className="mt-8" />
          <div className="space-y-px bg-line mt-4">
            {Object.entries(byType).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([type, count]) => (
              <div key={type} className="bg-ink-200 px-4 py-2 flex items-center gap-3">
                <span className="text-sm text-bone flex-1 capitalize">{type.replaceAll('_', ' ')}</span>
                <span className="num-mono text-sm text-bone">{count}</span>
                <div className="w-32 h-1 bg-ink-50 relative">
                  <div className="absolute inset-y-0 left-0 bg-signal" style={{ width: `${Math.min(100, (count / (summary.total || 1)) * 200)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={(v) => { setTab(v); setSeverity(null); }}
        tabs={[
          { value: 'issues', label: 'Issues', count: issuesQ.data?.total },
          { value: 'pages', label: 'Pages', count: pagesQ.data?.total },
        ]}
      />

      {tab === 'issues' && (
        <>
          <div className="flex gap-2">
            <Button variant={!severity ? 'primary' : 'outline'} size="sm" onClick={() => setSeverity(null)}>all</Button>
            <Button variant={severity === 'high' ? 'primary' : 'outline'} size="sm" onClick={() => setSeverity('high')}>high</Button>
            <Button variant={severity === 'medium' ? 'primary' : 'outline'} size="sm" onClick={() => setSeverity('medium')}>medium</Button>
            <Button variant={severity === 'low' ? 'primary' : 'outline'} size="sm" onClick={() => setSeverity('low')}>low</Button>
          </div>
          <DataTable
            columns={[
              { key: 'severity', header: 'Sev', render: (r) => <SeverityBadge severity={r.severity} />, width: 100 },
              { key: 'issue_type', header: 'Type', render: (r) => <span className="text-bone capitalize">{r.issue_type.replaceAll('_', ' ')}</span> },
              { key: 'url', header: 'URL', render: (r) => (
                <a href={r.url} target="_blank" rel="noreferrer" className="font-mono text-xs text-muted hover:text-signal truncate block max-w-[400px]">
                  {r.url}
                </a>
              )},
              { key: 'details', header: 'Detail', sortable: false, render: (r) => (
                <span className="font-mono text-2xs text-dim">{Object.entries(r.details || {}).slice(0, 2).map(([k, v]) => `${k}=${String(v).slice(0, 30)}`).join(' · ')}</span>
              )},
            ]}
            rows={issuesQ.data?.items || []}
            loading={issuesQ.isLoading}
            density="compact"
          />
        </>
      )}

      {tab === 'pages' && (
        <DataTable
          columns={[
            { key: 'url', header: 'URL', render: (r) => (
              <a href={r.url} target="_blank" rel="noreferrer" className="font-mono text-xs text-bone hover:text-signal truncate block max-w-[420px]">
                {r.url}
              </a>
            )},
            { key: 'status_code', header: 'Status', align: 'right', render: (r) => (
              <span className={`num-mono ${r.status_code >= 400 ? 'text-minus' : r.status_code >= 300 ? 'text-warn' : 'text-bone'}`}>
                {r.status_code ?? '—'}
              </span>
            )},
            { key: 'depth', header: 'Depth', align: 'right', render: (r) => <span className="num-mono">{r.depth}</span> },
            { key: 'word_count', header: 'Words', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtInt(r.word_count)}</span> },
            { key: 'h1_count', header: 'H1', align: 'right', render: (r) => <span className="num-mono">{r.h1_count}</span> },
            { key: 'load_time_ms', header: 'Load', align: 'right', render: (r) => <span className="num-mono text-muted">{r.load_time_ms ? `${r.load_time_ms}ms` : '—'}</span> },
            { key: 'is_https', header: 'TLS', align: 'right', render: (r) => r.is_https ? <span className="text-plus text-2xs">●</span> : <span className="text-minus text-2xs">●</span> },
          ]}
          rows={pagesQ.data?.items || []}
          loading={pagesQ.isLoading}
          density="compact"
        />
      )}
    </motion.div>
  );
}

function SeverityBlock({ label, value, color, onClick }) {
  return (
    <button onClick={onClick} className="bg-ink-200 hover:bg-ink-100 p-5 text-left transition-colors group">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
        <span className="font-mono text-2xs uppercase tracking-widest2 text-dim">{label}</span>
      </div>
      <p className="num-display text-4xl group-hover:text-signal transition-colors text-bone"
         style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
        {value}
      </p>
    </button>
  );
}
