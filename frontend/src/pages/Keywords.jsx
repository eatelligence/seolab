import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Download, Search, Sparkles, Bookmark } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

import { keywordsApi, projectsApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Tabs } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { DataTable } from '@/components/ui/DataTable';
import { Badge } from '@/components/ui/Badge';
import { fmtCompact, fmtInt, fmtMoney, fmtNum } from '@/lib/format';
import { Sparkline } from '@/components/Sparkline';

export default function Keywords() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const projectQ = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.get(projectId) });
  const [tab, setTab] = useState('research');

  const [seed, setSeed] = useState('');
  const [country, setCountry] = useState(projectQ.data?.country || 'US');
  const [levels, setLevels] = useState(2);
  const [results, setResults] = useState(null);

  const research = useMutation({
    mutationFn: (body) => keywordsApi.research(projectId, body),
    onSuccess: (data) => {
      setResults(data);
      toast.success(`${data.total} keywords expanded`);
    },
  });

  const related = useMutation({ mutationFn: (kw) => keywordsApi.related(projectId, { keyword: kw, country }) });
  const questions = useMutation({ mutationFn: (kw) => keywordsApi.questions(projectId, { keyword: kw, country }) });

  const savedQ = useQuery({
    queryKey: ['keywords', 'saved', projectId, country],
    queryFn: () => keywordsApi.list(projectId, { page_size: 500 }),
  });

  const save = useMutation({
    mutationFn: (selected) => keywordsApi.save(projectId, {
      keywords: selected, country, track: false,
    }),
    onSuccess: (r) => {
      toast.success(`${r.saved} saved · ${r.updated_or_skipped} updated`);
      qc.invalidateQueries({ queryKey: ['keywords'] });
    },
  });

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 02"
        title={<>Keyword <em className="text-signal not-italic">Research</em></>}
        kicker="Recursive Google Suggest expansion enriched with DataForSEO volume, KD, CPC and intent. Results cache for 24h."
      />

      <div className="panel p-5">
        <form
          className="grid grid-cols-1 md:grid-cols-[1fr_120px_120px_auto] gap-3 items-end"
          onSubmit={(e) => {
            e.preventDefault();
            if (!seed.trim()) return;
            research.mutate({ seed: seed.trim(), country, suggest_levels: levels, max_results: 500, include_metrics: true });
          }}
        >
          <Input
            label="Seed keyword"
            placeholder="best running shoes"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
          />
          <Select label="Country" value={country} onChange={(e) => setCountry(e.target.value)}>
            {['US','GB','IT','ES','FR','DE','PT','NL','BR','MX','JP','IN','AU','CA'].map((c) => <option key={c}>{c}</option>)}
          </Select>
          <Select label="Depth" value={levels} onChange={(e) => setLevels(Number(e.target.value))}>
            <option value={1}>1 level</option>
            <option value={2}>2 levels</option>
            <option value={3}>3 levels</option>
          </Select>
          <Button type="submit" variant="primary" loading={research.isPending}>
            <Search className="w-3.5 h-3.5" /> expand
          </Button>
        </form>
      </div>

      <Tabs
        value={tab}
        onChange={(v) => {
          setTab(v);
          if (v === 'related' && seed) related.mutate(seed);
          if (v === 'questions' && seed) questions.mutate(seed);
        }}
        tabs={[
          { value: 'research', label: 'Research', count: results?.total },
          { value: 'related', label: 'Related' },
          { value: 'questions', label: 'Questions' },
          { value: 'saved', label: 'Saved', count: savedQ.data?.total },
        ]}
      />

      {tab === 'research' && (
        <ResearchTable
          loading={research.isPending}
          rows={results?.keywords || []}
          onSave={(rows) => save.mutate(rows)}
        />
      )}
      {tab === 'related' && (
        <ResultsTable rows={related.data?.items || []} loading={related.isPending} />
      )}
      {tab === 'questions' && (
        <ResultsTable rows={questions.data?.items || []} loading={questions.isPending} questions />
      )}
      {tab === 'saved' && (
        <SavedTable rows={savedQ.data?.items || []} loading={savedQ.isLoading} projectId={projectId} />
      )}
    </motion.div>
  );
}

function ResearchTable({ rows, loading, onSave }) {
  const [selected, setSelected] = useState(new Set());
  const toggle = (kw) => {
    const next = new Set(selected);
    next.has(kw) ? next.delete(kw) : next.add(kw);
    setSelected(next);
  };

  const cols = [
    {
      key: '_sel', header: '', sortable: false, width: 40,
      render: (r) => (
        <input
          type="checkbox"
          checked={selected.has(r.keyword)}
          onChange={() => toggle(r.keyword)}
          className="accent-signal"
        />
      ),
    },
    { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
    { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono text-bone">{fmtCompact(r.search_volume)}</span> },
    { key: 'keyword_difficulty', header: 'KD', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.keyword_difficulty, 0)}</span> },
    { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtMoney(r.cpc)}</span> },
    { key: 'intent', header: 'Intent', render: (r) => r.intent ? <Badge tone="info">{r.intent}</Badge> : <span className="text-dim">—</span> },
    {
      key: 'monthly_searches', header: 'Trend', sortable: false, width: 100,
      render: (r) => {
        const data = (r.monthly_searches || []).slice(-12).map((m) => ({ v: m.search_volume || 0 }));
        return <div className="w-24"><Sparkline data={data} /></div>;
      },
    },
  ];

  return (
    <>
      <div className="flex items-center justify-between gap-3">
        <p className="text-2xs font-mono uppercase tracking-widest2 text-dim">
          {selected.size > 0 ? <span className="text-signal">{selected.size} selected</span> : `${rows.length} results`}
        </p>
        {selected.size > 0 && (
          <Button
            variant="primary"
            onClick={() => {
              const sel = rows.filter((r) => selected.has(r.keyword));
              onSave(sel);
              setSelected(new Set());
            }}
          >
            <Bookmark className="w-3.5 h-3.5" /> save selection
          </Button>
        )}
      </div>
      <DataTable columns={cols} rows={rows} keyField="keyword" loading={loading} pageSize={50} searchKeys={['keyword', 'intent']} />
    </>
  );
}

function ResultsTable({ rows, loading, questions }) {
  const cols = [
    { key: 'keyword', header: questions ? 'Question' : 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
    { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono text-bone">{fmtCompact(r.search_volume)}</span> },
    { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono text-muted">{fmtMoney(r.cpc)}</span> },
    !questions && { key: 'difficulty', header: 'KD', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.difficulty, 0)}</span> },
  ].filter(Boolean);
  return <DataTable columns={cols} rows={rows} keyField="keyword" loading={loading} />;
}

function SavedTable({ rows, loading, projectId }) {
  return (
    <>
      <div className="flex justify-end">
        <a href={`/api/projects/${projectId}/keywords/export.csv`} target="_blank" rel="noreferrer">
          <Button variant="outline"><Download className="w-3.5 h-3.5" /> export csv</Button>
        </a>
      </div>
      <DataTable
        columns={[
          { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
          { key: 'country', header: 'Geo', width: 80 },
          { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.search_volume)}</span> },
          { key: 'keyword_difficulty', header: 'KD', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.keyword_difficulty, 0)}</span> },
          { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono">{fmtMoney(r.cpc)}</span> },
          { key: 'tracked', header: 'Tracked', render: (r) => r.tracked ? <Badge tone="signal">●  ON</Badge> : <span className="text-dim text-2xs font-mono">off</span> },
        ]}
        rows={rows}
        loading={loading}
      />
    </>
  );
}
