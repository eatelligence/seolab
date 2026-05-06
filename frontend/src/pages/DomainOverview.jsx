import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Search, Globe2, ExternalLink } from 'lucide-react';

import { domainApi, projectsApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { MetricCard } from '@/components/MetricCard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { DataTable } from '@/components/ui/DataTable';
import { Empty } from '@/components/ui/Empty';
import { Badge } from '@/components/ui/Badge';
import { COUNTRIES } from '@/lib/countries';
import { fmtCompact, fmtNum } from '@/lib/format';

export default function DomainOverview() {
  const { projectId } = useParams();
  const projectQ = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.get(projectId) });

  const [target, setTarget] = useState('');
  const [country, setCountry] = useState('');

  const m = useMutation({
    mutationFn: () => domainApi.overview(projectId, {
      target: target.trim(),
      country: country || projectQ.data?.country || 'US',
    }),
  });

  const data = m.data;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 10"
        title={<>Domain <em className="text-signal not-italic">Overview</em></>}
        kicker="Plug any domain — yours, a competitor, a research target — and pull headline metrics, top organic keywords, top pages and competitors in one round-trip."
      />

      <div className="panel p-5">
        <form
          className="grid grid-cols-1 md:grid-cols-[1fr_220px_auto] gap-3 items-end"
          onSubmit={(e) => { e.preventDefault(); if (target.trim()) m.mutate(); }}
        >
          <Input
            label="Domain"
            placeholder="competitor.com"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            autoFocus
            hint="https:// and www. stripped automatically"
          />
          <Select
            label="Country"
            value={country || projectQ.data?.country || 'US'}
            onChange={(e) => setCountry(e.target.value)}
          >
            {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.label}</option>)}
          </Select>
          <Button variant="primary" type="submit" loading={m.isPending} disabled={!target.trim()}>
            <Search className="w-3.5 h-3.5" /> lookup
          </Button>
        </form>
      </div>

      {!data && !m.isPending && (
        <Empty
          icon={Globe2}
          title="Domain lookup"
          description="Enter any domain and geo to get organic traffic, keywords, backlinks, top pages and direct competitors."
        />
      )}

      {m.isPending && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="bg-ink-200 h-32 shimmer" />)}
        </div>
      )}

      {data && (
        <>
          {data.is_self && (
            <div className="panel-soft p-3">
              <p className="font-mono text-2xs uppercase tracking-widest2 text-signal">
                ●  YOU · this is the project's domain
              </p>
            </div>
          )}

          <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
            <MetricCard
              label="● DOMAIN AUTH"
              value={fmtNum(data.metrics.domain_authority, 1)}
              unit="/10"
              hint="Open PageRank"
            />
            <MetricCard
              label="● ORGANIC TRAFFIC"
              value={fmtCompact(data.metrics.organic_traffic)}
              unit="visits/mo"
              hint={`${fmtCompact(data.metrics.organic_keywords)} keywords`}
              sparkColor="#60A5FA"
            />
            <MetricCard
              label="● BACKLINKS"
              value={fmtCompact(data.metrics.backlinks)}
              hint={`${fmtCompact(data.metrics.referring_domains)} ref. domains`}
              sparkColor="#FACC15"
            />
            <MetricCard
              label="● PAID TRAFFIC"
              value={fmtCompact(data.metrics.paid_traffic)}
              unit="visits/mo"
              hint={`${fmtCompact(data.metrics.paid_keywords)} paid keywords`}
              sparkColor="#F87171"
            />
          </section>

          {/* Top organic keywords */}
          <section>
            <p className="eyebrow mb-3">● TOP ORGANIC KEYWORDS · {data.country}</p>
            <DataTable
              columns={[
                { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
                { key: 'position', header: 'Pos', align: 'right', render: (r) => <span className="num-mono text-bone">{r.position ?? '—'}</span> },
                { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.search_volume)}</span> },
                { key: 'etv', header: 'Traffic', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtCompact(r.etv)}</span> },
                { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono text-muted">${fmtNum(r.cpc, 2)}</span> },
                { key: 'url', header: '', sortable: false, render: (r) => r.url ? (
                  <a href={r.url} target="_blank" rel="noreferrer" className="text-dim hover:text-signal">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                ) : null },
              ]}
              rows={data.top_keywords || []}
              keyField="keyword"
              pageSize={20}
            />
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-line">
            <section className="bg-ink-200 p-5">
              <p className="eyebrow mb-3">● TOP PAGES BY TRAFFIC</p>
              <div className="space-y-px bg-line">
                {(data.top_pages || []).slice(0, 12).map((p, i) => (
                  <div key={p.page} className="bg-ink-200 px-3 py-2 flex items-baseline gap-3">
                    <span className="num-mono text-2xs text-dim w-6">{String(i + 1).padStart(2, '0')}</span>
                    <a href={p.page} target="_blank" rel="noreferrer" className="flex-1 text-sm text-bone hover:text-signal truncate font-mono text-xs">
                      {p.page ? (() => { try { return new URL(p.page).pathname || '/'; } catch { return p.page; } })() : '—'}
                    </a>
                    <span className="num-mono text-bone">{fmtCompact(p.organic_traffic)}</span>
                  </div>
                ))}
                {(data.top_pages || []).length === 0 && (
                  <p className="text-2xs font-mono uppercase tracking-widest2 text-dim p-8 text-center">No pages found</p>
                )}
              </div>
            </section>

            <section className="bg-ink-200 p-5">
              <p className="eyebrow mb-3">● ORGANIC COMPETITORS</p>
              <div className="space-y-px bg-line">
                {(data.competitors || []).slice(0, 12).map((c, i) => (
                  <div key={c.domain} className="bg-ink-200 px-3 py-2 flex items-baseline gap-3">
                    <span className="num-mono text-2xs text-dim w-6">{String(i + 1).padStart(2, '0')}</span>
                    <span className="flex-1 text-sm text-bone truncate font-mono">{c.domain}</span>
                    <span className="num-mono text-2xs text-dim">{fmtCompact(c.intersections)} shared</span>
                    <span className="num-mono text-bone">{fmtCompact(c.organic_traffic)}</span>
                  </div>
                ))}
                {(data.competitors || []).length === 0 && (
                  <p className="text-2xs font-mono uppercase tracking-widest2 text-dim p-8 text-center">No competitors found</p>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </motion.div>
  );
}
