import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Users } from 'lucide-react';

import { competitorsApi } from '@/api';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Tabs } from '@/components/ui/Tabs';
import { DataTable } from '@/components/ui/DataTable';
import { Empty } from '@/components/ui/Empty';
import { Badge } from '@/components/ui/Badge';
import { fmtCompact, fmtMoney, fmtNum } from '@/lib/format';

export default function Competitors() {
  const { projectId } = useParams();
  const [tab, setTab] = useState('overview');

  const overview = useQuery({ queryKey: ['cmp', 'overview', projectId], queryFn: () => competitorsApi.overview(projectId) });
  const gap = useQuery({ queryKey: ['cmp', 'gap', projectId], queryFn: () => competitorsApi.keywordGap(projectId, 300), enabled: tab === 'gap' });
  const content = useQuery({ queryKey: ['cmp', 'content', projectId], queryFn: () => competitorsApi.contentGap(projectId, 30), enabled: tab === 'content' });
  const overlap = useQuery({ queryKey: ['cmp', 'overlap', projectId], queryFn: () => competitorsApi.serpOverlap(projectId), enabled: tab === 'overlap' });

  const hasCompetitors = (overview.data || []).filter((r) => !r.is_self).length > 0;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 06"
        title={<>Competitor <em className="text-signal not-italic">Intel</em></>}
        kicker="Side-by-side organic metrics from DataForSEO + Open PageRank. Up to 5 competitors per project."
      />

      {!hasCompetitors && !overview.isLoading ? (
        <Empty
          icon={Users}
          title="No competitors configured"
          description="Add domains in /settings under Competitors. They'll be benchmarked side-by-side and used for keyword/content gap analysis."
        />
      ) : (
        <>
          <SectionHeading eyebrow="● BENCHMARK" title="Side-by-side" kicker="Self row is highlighted" />
          <DataTable
            columns={[
              { key: 'domain', header: 'Domain', render: (r) => (
                <span className={`flex items-center gap-2 ${r.is_self ? 'text-signal' : 'text-bone'} font-mono text-sm`}>
                  {r.is_self && <span className="w-1.5 h-1.5 rounded-full bg-signal" />}
                  {r.domain}
                  {r.is_self && <Badge tone="signal" className="ml-2">YOU</Badge>}
                </span>
              )},
              { key: 'domain_authority', header: 'DA', align: 'right', render: (r) => <span className="num-mono text-bone">{fmtNum(r.domain_authority, 1)}</span> },
              { key: 'organic_traffic', header: 'Org. Traffic', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.organic_traffic)}</span> },
              { key: 'organic_keywords', header: 'Keywords', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.organic_keywords)}</span> },
              { key: 'backlinks', header: 'Backlinks', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.backlinks)}</span> },
              { key: 'referring_domains', header: 'Ref.Dom.', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.referring_domains)}</span> },
            ]}
            rows={overview.data || []}
            loading={overview.isLoading}
            keyField="domain"
            searchable={false}
          />

          <Tabs
            value={tab}
            onChange={setTab}
            tabs={[
              { value: 'overview', label: 'Benchmark' },
              { value: 'gap', label: 'Keyword gap' },
              { value: 'content', label: 'Content gap' },
              { value: 'overlap', label: 'SERP overlap' },
            ]}
          />

          {tab === 'gap' && (
            <DataTable
              columns={[
                { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
                { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.search_volume)}</span> },
                { key: 'difficulty', header: 'KD', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.difficulty, 0)}</span> },
                { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtMoney(r.cpc)}</span> },
                { key: 'competition', header: 'Comp.', render: (r) => r.competition ? <Badge>{r.competition}</Badge> : '—' },
              ]}
              rows={gap.data || []}
              loading={gap.isLoading}
              keyField="keyword"
            />
          )}

          {tab === 'content' && (
            <div className="space-y-px bg-line">
              {(content.data || []).map((c) => (
                <div key={c.domain} className="bg-ink-200 p-5">
                  <p className="eyebrow mb-3">● COMPETITOR / {c.domain}</p>
                  <DataTable
                    columns={[
                      { key: 'page', header: 'Page', render: (r) => (
                        <a href={r.page} target="_blank" rel="noreferrer" className="text-bone hover:text-signal font-mono text-xs truncate block max-w-[480px]">
                          {(() => { try { return new URL(r.page).pathname; } catch { return r.page; }})()}
                        </a>
                      )},
                      { key: 'metrics', header: 'Traffic', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.metrics?.organic?.etv ?? r.metrics?.etv ?? r.traffic)}</span> },
                    ]}
                    rows={(c.pages || []).slice(0, 10)}
                    keyField="page"
                    searchable={false}
                    pageSize={10}
                  />
                </div>
              ))}
            </div>
          )}

          {tab === 'overlap' && (
            <DataTable
              columns={[
                { key: 'domain', header: 'Domain', render: (r) => (
                  <span className={`font-mono text-sm flex items-center gap-2 ${r.is_competitor ? 'text-signal' : 'text-bone'}`}>
                    {r.domain}
                    {r.is_competitor && <Badge tone="signal">tracked</Badge>}
                  </span>
                )},
                { key: 'intersections', header: 'Shared kw.', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.intersections)}</span> },
                { key: 'organic_traffic', header: 'Org. Traffic', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.organic_traffic)}</span> },
                { key: 'organic_keywords', header: 'Keywords', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.organic_keywords)}</span> },
              ]}
              rows={overlap.data || []}
              loading={overlap.isLoading}
              keyField="domain"
            />
          )}
        </>
      )}
    </motion.div>
  );
}
