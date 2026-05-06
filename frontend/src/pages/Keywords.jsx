import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Download, Search, Sparkles, Bookmark, History, RotateCcw, Trash2, Eye, Activity } from 'lucide-react';
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
import { fmtCompact, fmtMoney, fmtNum, fmtRelative } from '@/lib/format';
import { Sparkline } from '@/components/Sparkline';
import { COUNTRIES } from '@/lib/countries';

export default function Keywords() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const projectQ = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.get(projectId) });
  const [tab, setTab] = useState('research');

  const [seed, setSeed] = useState('');
  const [country, setCountry] = useState(projectQ.data?.country || 'US');
  const [levels, setLevels] = useState(2);
  const [results, setResults] = useState(null);
  const [currentRunId, setCurrentRunId] = useState(null);

  // Auto-saved research history (per-project)
  const historyQ = useQuery({
    queryKey: ['kw-research', 'history', projectId],
    queryFn: () => keywordsApi.research.history(projectId, 50),
    staleTime: 0,
  });

  const research = useMutation({
    mutationFn: (body) => keywordsApi.research(projectId, body),
    onSuccess: (data) => {
      setResults(data);
      setCurrentRunId(data.run_id || null);
      qc.invalidateQueries({ queryKey: ['kw-research', 'history', projectId] });
      toast.success(`${data.total} keywords expanded · auto-saved`);
    },
  });

  const related = useMutation({ mutationFn: (kw) => keywordsApi.related(projectId, { keyword: kw, country }) });
  const questions = useMutation({ mutationFn: (kw) => keywordsApi.questions(projectId, { keyword: kw, country }) });

  const savedQ = useQuery({
    queryKey: ['keywords', 'saved', projectId],
    queryFn: () => keywordsApi.list(projectId, { page_size: 500 }),
  });

  const save = useMutation({
    mutationFn: ({ rows, track }) => keywordsApi.save(projectId, { keywords: rows, country, track }),
    onSuccess: (r) => {
      toast.success(`${r.saved} saved · ${r.updated_or_skipped} updated`);
      qc.invalidateQueries({ queryKey: ['keywords'] });
    },
  });

  const bulkTrack = useMutation({
    mutationFn: ({ ids, tracked }) => keywordsApi.bulkTrack(projectId, ids, tracked),
    onSuccess: (r) => {
      toast.success(`${r.updated} keyword${r.updated === 1 ? '' : 's'} ${r.tracked ? 'now tracked' : 'untracked'}`);
      qc.invalidateQueries({ queryKey: ['keywords'] });
      qc.invalidateQueries({ queryKey: ['rankings'] });
    },
  });

  const bulkDelete = useMutation({
    mutationFn: (ids) => keywordsApi.bulkDelete(projectId, ids),
    onSuccess: (r) => {
      toast.success(`${r.deleted} deleted`);
      qc.invalidateQueries({ queryKey: ['keywords'] });
    },
  });

  const loadHistory = async (id) => {
    const rec = await keywordsApi.research.one(projectId, id);
    setSeed(rec.seed);
    setCountry(rec.country);
    setLevels(rec.suggest_levels);
    setResults({
      seed: rec.seed,
      country: rec.country,
      total: rec.total,
      keywords: rec.keywords || [],
      run_id: rec.id,
    });
    setCurrentRunId(rec.id);
    setTab('research');
  };

  const removeHistory = useMutation({
    mutationFn: (id) => keywordsApi.research.remove(projectId, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kw-research', 'history', projectId] });
    },
  });

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 02"
        title={<>Keyword <em className="text-signal not-italic">Research</em></>}
        kicker="Recursive Google Suggest expansion enriched with DataForSEO. Every research is auto-saved per project — reload from the history rail."
      />

      <div className="panel p-5">
        <form
          className="grid grid-cols-1 md:grid-cols-[1fr_180px_120px_auto_auto] gap-3 items-end"
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
            {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.label}</option>)}
          </Select>
          <Select label="Depth" value={levels} onChange={(e) => setLevels(Number(e.target.value))}>
            <option value={1}>1 level</option>
            <option value={2}>2 levels</option>
            <option value={3}>3 levels</option>
          </Select>
          <Button type="submit" variant="primary" loading={research.isPending}>
            <Search className="w-3.5 h-3.5" /> expand
          </Button>
          {results && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => { setResults(null); setCurrentRunId(null); setSeed(''); }}
              title="New blank research"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
          )}
        </form>
        {currentRunId && (
          <p className="mt-3 text-2xs font-mono uppercase tracking-widest2 text-dim">
            ● viewing saved run · #{String(currentRunId).slice(0, 8)} · {results?.total} keywords
          </p>
        )}
      </div>

      {/* Research history strip — collapsible */}
      <ResearchHistory
        runs={historyQ.data || []}
        currentId={currentRunId}
        onLoad={loadHistory}
        onDelete={(id) => { if (window.confirm('Delete this saved research?')) removeHistory.mutate(id); }}
      />

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
          onSave={(rows, track) => save.mutate({ rows, track })}
        />
      )}
      {tab === 'related' && (
        <ResultsTable rows={related.data?.items || []} loading={related.isPending} />
      )}
      {tab === 'questions' && (
        <ResultsTable rows={questions.data?.items || []} loading={questions.isPending} questions />
      )}
      {tab === 'saved' && (
        <SavedTable
          rows={savedQ.data?.items || []}
          loading={savedQ.isLoading}
          projectId={projectId}
          onBulkTrack={(ids, tracked) => bulkTrack.mutate({ ids, tracked })}
          onBulkDelete={(ids) => bulkDelete.mutate(ids)}
        />
      )}
    </motion.div>
  );
}

/* ──────────── Research history strip ──────────── */

function ResearchHistory({ runs, currentId, onLoad, onDelete }) {
  if (!runs || runs.length === 0) return null;
  return (
    <div className="panel p-4">
      <div className="flex items-center gap-3 mb-3">
        <History className="w-3.5 h-3.5 text-signal" />
        <p className="eyebrow !text-2xs">RESEARCH HISTORY</p>
        <span className="font-mono text-2xs text-dim">{runs.length} saved</span>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {runs.map((r) => {
          const active = r.id === currentId;
          return (
            <div
              key={r.id}
              className={`group shrink-0 border px-3 py-2 cursor-pointer transition-colors ${
                active ? 'border-signal bg-signal/5' : 'border-line hover:border-line2 hover:bg-ink-100'
              }`}
              onClick={() => onLoad(r.id)}
            >
              <div className="flex items-baseline gap-2 max-w-[280px]">
                <span className={`text-sm truncate ${active ? 'text-signal' : 'text-bone'}`}>
                  {r.seed}
                </span>
                <span className="font-mono text-2xs text-dim">{r.country}</span>
                <span className="font-mono text-2xs text-dim">·</span>
                <span className="font-mono text-2xs text-dim num-mono">{r.total}</span>
              </div>
              <div className="flex items-center justify-between gap-2 mt-1">
                <span className="font-mono text-2xs text-dim">{fmtRelative(r.created_at)}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(r.id); }}
                  className="opacity-0 group-hover:opacity-100 text-dim hover:text-minus transition-all"
                  title="Delete saved research"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ──────────── Tables ──────────── */

function ResearchTable({ rows, loading, onSave }) {
  const [selected, setSelected] = useState(new Set());
  const toggle = (kw) => {
    const next = new Set(selected);
    next.has(kw) ? next.delete(kw) : next.add(kw);
    setSelected(next);
  };
  const toggleAll = (visible) => {
    if (selected.size === visible.length) setSelected(new Set());
    else setSelected(new Set(visible.map((r) => r.keyword)));
  };

  const cols = [
    {
      key: '_sel', header: <input type="checkbox" className="accent-signal"
        checked={rows.length > 0 && selected.size === rows.length}
        onChange={() => toggleAll(rows)} />,
      sortable: false, width: 40,
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
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                const sel = rows.filter((r) => selected.has(r.keyword));
                onSave(sel, false);
                setSelected(new Set());
              }}
            >
              <Bookmark className="w-3.5 h-3.5" /> save
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                const sel = rows.filter((r) => selected.has(r.keyword));
                onSave(sel, true);
                setSelected(new Set());
              }}
            >
              <Activity className="w-3.5 h-3.5" /> save & track
            </Button>
          </div>
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

function SavedTable({ rows, loading, projectId, onBulkTrack, onBulkDelete }) {
  const [selected, setSelected] = useState(new Set());

  const toggle = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };
  const toggleAll = () => {
    if (selected.size === rows.length) setSelected(new Set());
    else setSelected(new Set(rows.map((r) => r.id)));
  };

  return (
    <>
      <div className="flex items-center justify-between gap-3">
        <p className="text-2xs font-mono uppercase tracking-widest2 text-dim">
          {selected.size > 0 ? <span className="text-signal">{selected.size} selected</span> : `${rows.length} keywords`}
        </p>
        <div className="flex gap-2">
          {selected.size > 0 && (
            <>
              <Button
                variant="outline"
                onClick={() => { onBulkTrack(Array.from(selected), true); setSelected(new Set()); }}
              >
                <Activity className="w-3.5 h-3.5" /> track ({selected.size})
              </Button>
              <Button
                variant="outline"
                onClick={() => { onBulkTrack(Array.from(selected), false); setSelected(new Set()); }}
              >
                <Eye className="w-3.5 h-3.5" /> untrack
              </Button>
              <Button
                variant="danger"
                onClick={() => {
                  if (window.confirm(`Delete ${selected.size} keyword${selected.size === 1 ? '' : 's'}? Their rankings history will also be deleted.`)) {
                    onBulkDelete(Array.from(selected));
                    setSelected(new Set());
                  }
                }}
              >
                <Trash2 className="w-3.5 h-3.5" /> delete
              </Button>
            </>
          )}
          <a href={`/api/projects/${projectId}/keywords/export.csv`} target="_blank" rel="noreferrer">
            <Button variant="outline"><Download className="w-3.5 h-3.5" /> export csv</Button>
          </a>
        </div>
      </div>
      <DataTable
        columns={[
          {
            key: '_sel', header: <input type="checkbox" className="accent-signal"
              checked={rows.length > 0 && selected.size === rows.length}
              onChange={toggleAll} />,
            sortable: false, width: 40,
            render: (r) => (
              <input type="checkbox" checked={selected.has(r.id)}
                onChange={() => toggle(r.id)} className="accent-signal" />
            ),
          },
          { key: 'keyword', header: 'Keyword', render: (r) => <span className="text-bone">{r.keyword}</span> },
          { key: 'country', header: 'Geo', width: 80 },
          { key: 'search_volume', header: 'Volume', align: 'right', render: (r) => <span className="num-mono">{fmtCompact(r.search_volume)}</span> },
          { key: 'keyword_difficulty', header: 'KD', align: 'right', render: (r) => <span className="num-mono">{fmtNum(r.keyword_difficulty, 0)}</span> },
          { key: 'cpc', header: 'CPC', align: 'right', render: (r) => <span className="num-mono">{fmtMoney(r.cpc)}</span> },
          { key: 'tracked', header: 'Tracked', render: (r) => r.tracked ? <Badge tone="signal">●  ON</Badge> : <span className="text-dim text-2xs font-mono">off</span> },
        ]}
        rows={rows}
        loading={loading}
        keyField="id"
      />
    </>
  );
}
