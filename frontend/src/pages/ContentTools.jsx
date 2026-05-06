import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Sparkles, FileText, Tag, Calendar, Trash2, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

import { contentApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Tabs } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Empty } from '@/components/ui/Empty';
import { COUNTRIES } from '@/lib/countries';
import { fmtRelative } from '@/lib/format';

const TOOL_LABELS = {
  brief: 'SEO Brief',
  optimize: 'Optimizer',
  meta: 'Meta',
  calendar: 'Calendar',
};

export default function ContentTools() {
  const { projectId } = useParams();
  const [tab, setTab] = useState('brief');

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 07"
        title={<>Content & <em className="text-signal not-italic">AI</em></>}
        kicker="Powered by Anthropic Claude. Every generation is auto-saved per project — switch tabs, reload, come back tomorrow, your work is there."
      />

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { value: 'brief', label: 'SEO Brief' },
          { value: 'optimize', label: 'Optimizer' },
          { value: 'meta', label: 'Meta Generator' },
          { value: 'calendar', label: 'Calendar' },
        ]}
      />

      {tab === 'brief' && <SeoBriefTool projectId={projectId} />}
      {tab === 'optimize' && <OptimizerTool projectId={projectId} />}
      {tab === 'meta' && <MetaTool projectId={projectId} />}
      {tab === 'calendar' && <CalendarTool projectId={projectId} />}
    </motion.div>
  );
}

/* ──────────── Reusable history rail ──────────── */

function HistoryRail({ projectId, toolType, currentId, onLoad }) {
  const qc = useQueryClient();
  const historyQ = useQuery({
    queryKey: ['content', 'history', projectId, toolType],
    queryFn: () => contentApi.history(projectId, { tool_type: toolType, limit: 50 }),
    staleTime: 0,
  });

  const remove = useMutation({
    mutationFn: (id) => contentApi.historyDelete(projectId, id),
    onSuccess: () => {
      toast.success('Removed');
      qc.invalidateQueries({ queryKey: ['content', 'history', projectId, toolType] });
    },
  });

  return (
    <div className="bg-ink-200 p-5 border-l border-line min-h-[520px] flex flex-col">
      <p className="eyebrow mb-4">● HISTORY · {TOOL_LABELS[toolType]}</p>
      {historyQ.isLoading ? (
        <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-12" />)}</div>
      ) : (historyQ.data || []).length === 0 ? (
        <p className="text-2xs font-mono uppercase tracking-widest2 text-dim py-12 text-center">
          empty<br /><span className="text-dim/60">your saved generations<br />will appear here</span>
        </p>
      ) : (
        <div className="space-y-px bg-line flex-1 overflow-y-auto">
          {historyQ.data.map((it) => {
            const active = it.id === currentId;
            return (
              <div
                key={it.id}
                className={`group bg-ink-200 hover:bg-ink-100 px-3 py-2.5 border-l-2 transition-colors flex items-start gap-2 ${active ? 'border-signal bg-ink-100' : 'border-transparent'}`}
              >
                <button
                  onClick={() => onLoad(it.id)}
                  className="flex-1 text-left min-w-0"
                >
                  <p className="text-sm text-bone truncate">{it.title}</p>
                  <p className="text-2xs font-mono text-dim mt-0.5">{fmtRelative(it.created_at)}</p>
                </button>
                <button
                  onClick={() => { if (window.confirm('Delete this saved generation?')) remove.mutate(it.id); }}
                  className="opacity-0 group-hover:opacity-100 text-dim hover:text-minus transition-all"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function useToolState(projectId, toolType) {
  const qc = useQueryClient();
  const [currentId, setCurrentId] = useState(null);
  const [output, setOutput] = useState(null);

  const reset = () => { setCurrentId(null); setOutput(null); };
  const onSaved = (id, result) => {
    setCurrentId(id);
    setOutput(result);
    qc.invalidateQueries({ queryKey: ['content', 'history', projectId, toolType] });
  };
  const restore = (rec) => {
    setCurrentId(rec.id);
    setOutput(rec.output);
  };

  return { currentId, output, reset, onSaved, restore };
}

/* ──────────── 1. SEO Brief ──────────── */

function SeoBriefTool({ projectId }) {
  const [keyword, setKeyword] = useState('');
  const [country, setCountry] = useState('US');
  const [intent, setIntent] = useState('informational');

  const { currentId, output, reset, onSaved, restore } = useToolState(projectId, 'brief');

  const m = useMutation({
    mutationFn: () => contentApi.brief(projectId, { keyword, country, search_intent: intent }),
    onSuccess: ({ id, result }) => {
      onSaved(id, result);
      toast.success('Brief saved');
    },
  });

  const onLoad = async (id) => {
    const rec = await contentApi.historyOne(projectId, id);
    setKeyword(rec.input?.keyword || '');
    setCountry(rec.input?.country || 'US');
    setIntent(rec.input?.search_intent || 'informational');
    restore(rec);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr_320px] gap-px bg-line">
      <div className="bg-ink-200 p-5 space-y-4">
        <p className="eyebrow">● INPUT / TARGETS</p>
        <Input label="Target keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="best running shoes" />
        <div className="grid grid-cols-2 gap-3">
          <Select label="Country" value={country} onChange={(e) => setCountry(e.target.value)}>
            {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.label}</option>)}
          </Select>
          <Select label="Intent" value={intent} onChange={(e) => setIntent(e.target.value)}>
            <option value="informational">Informational</option>
            <option value="commercial">Commercial</option>
            <option value="transactional">Transactional</option>
            <option value="navigational">Navigational</option>
          </Select>
        </div>
        <div className="flex gap-2">
          <Button variant="primary" onClick={() => m.mutate()} loading={m.isPending} disabled={!keyword.trim()} className="flex-1">
            <Sparkles className="w-3.5 h-3.5" /> generate
          </Button>
          {output && (
            <Button variant="ghost" onClick={reset} title="New blank">
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
        {currentId && (
          <p className="text-2xs font-mono uppercase tracking-widest2 text-dim border-t border-line pt-3">
            ● viewing saved · #{String(currentId).slice(0, 8)}
          </p>
        )}
      </div>

      <div className="bg-ink-200 p-6">
        {!output && !m.isPending && <Empty icon={FileText} title="Brief output" description="Provide a target keyword to generate a complete SEO brief, or pick a previous one from the history rail." />}
        {m.isPending && <div className="space-y-3">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="shimmer h-6" />)}</div>}
        {output && (
          <article className="space-y-6">
            <header>
              <p className="eyebrow mb-2">● BRIEF</p>
              <h2 className="font-display text-2xl text-bone leading-tight" style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
                {output.title}
              </h2>
              <p className="text-sm text-muted mt-2">{output.meta_description}</p>
            </header>
            <div className="grid grid-cols-3 gap-px bg-line">
              <Stat label="Word count" value={output.recommended_word_count} />
              <Stat label="Audience" value={output.target_audience} small />
              <Stat label="Snippet" value={output.featured_snippet_target} small />
            </div>
            <Block title="H STRUCTURE">
              <ul className="space-y-1.5 font-mono text-xs">
                {(output.h_structure || []).map((h, i) => (
                  <li key={i} className="flex gap-3">
                    <span className="text-signal">{h.level}</span>
                    <span className="text-bone">{h.text}</span>
                  </li>
                ))}
              </ul>
            </Block>
            <Block title="TOPICS TO COVER"><ChipList items={output.topics_to_cover} /></Block>
            <Block title="LSI / SEMANTIC"><ChipList items={output.lsi_keywords} tone="signal" /></Block>
            <Block title="QUESTIONS TO ANSWER">
              <ul className="space-y-1.5 text-sm text-bone">
                {(output.questions_to_answer || []).map((q, i) => <li key={i} className="before:content-['→'] before:text-signal before:mr-2">{q}</li>)}
              </ul>
            </Block>
          </article>
        )}
      </div>

      <HistoryRail projectId={projectId} toolType="brief" currentId={currentId} onLoad={onLoad} />
    </div>
  );
}

/* ──────────── 2. Optimizer ──────────── */

function OptimizerTool({ projectId }) {
  const [target, setTarget] = useState('');
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');

  const { currentId, output, reset, onSaved, restore } = useToolState(projectId, 'optimize');

  const m = useMutation({
    mutationFn: () => contentApi.optimize(projectId, { target_keyword: target, content: content || undefined, url: url || undefined }),
    onSuccess: ({ id, result }) => { onSaved(id, result); toast.success('Optimization saved'); },
  });

  const onLoad = async (id) => {
    const rec = await contentApi.historyOne(projectId, id);
    setTarget(rec.input?.target_keyword || '');
    setUrl(rec.input?.url || '');
    setContent(rec.input?.content || '');
    restore(rec);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px_320px] gap-px bg-line">
      <div className="bg-ink-200 p-5 space-y-4">
        <Input label="Target keyword" value={target} onChange={(e) => setTarget(e.target.value)} required />
        <Input label="URL (optional)" placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} hint="Provide either URL or paste content below" />
        <Textarea label="Content" placeholder="Paste your content here..." value={content} onChange={(e) => setContent(e.target.value)} rows={14} />
        <div className="flex gap-2">
          <Button variant="primary" onClick={() => m.mutate()} loading={m.isPending} disabled={!target.trim() || (!content && !url)} className="flex-1">
            <Sparkles className="w-3.5 h-3.5" /> score & optimize
          </Button>
          {output && <Button variant="ghost" onClick={reset}><RotateCcw className="w-3.5 h-3.5" /></Button>}
        </div>
        {currentId && (
          <p className="text-2xs font-mono uppercase tracking-widest2 text-dim border-t border-line pt-3">
            ● viewing saved · #{String(currentId).slice(0, 8)}
          </p>
        )}
      </div>

      <div className="bg-ink-200 p-6">
        {!output && !m.isPending && <Empty title="Optimization report" description="Paste content or URL + target keyword, or pick from history." />}
        {m.isPending && <div className="space-y-3">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="shimmer h-6" />)}</div>}
        {output && (
          <div className="space-y-5">
            <div className="text-center">
              <p className="eyebrow mb-3">● SCORE</p>
              <p className="num-display text-7xl text-signal" style={{ fontVariationSettings: "'opsz' 144, 'WONK' 1" }}>
                {output.overall_score}
              </p>
              <p className="text-2xs font-mono uppercase tracking-widest2 text-dim mt-2">/ 100</p>
            </div>
            <Block title="Diagnostics">
              <div className="grid grid-cols-2 gap-px bg-line">
                <MiniStat label="Density" value={`${output.keyword_density_pct}%`} />
                <MiniStat label="Words" value={output.word_count} />
                <MiniStat label="In title" value={output.keyword_in_title ? '✓' : '✗'} />
                <MiniStat label="First 100w" value={output.keyword_in_first_100_words ? '✓' : '✗'} />
              </div>
            </Block>
            <Block title="Issues">
              <ul className="space-y-2">
                {(output.issues || []).map((iss, i) => (
                  <li key={i} className="border-l-2 pl-3 py-1" style={{
                    borderColor: iss.severity === 'high' ? '#F87171' : iss.severity === 'medium' ? '#FACC15' : '#60A5FA',
                  }}>
                    <p className="text-sm text-bone">{iss.issue}</p>
                    <p className="text-xs text-muted mt-1">{iss.fix}</p>
                  </li>
                ))}
              </ul>
            </Block>
            <Block title="Add semantic terms"><ChipList items={output.semantic_keywords_to_add} tone="signal" /></Block>
            <Block title="Missing topics"><ChipList items={output.missing_topics} /></Block>
          </div>
        )}
      </div>

      <HistoryRail projectId={projectId} toolType="optimize" currentId={currentId} onLoad={onLoad} />
    </div>
  );
}

/* ──────────── 3. Meta Generator ──────────── */

function MetaTool({ projectId }) {
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');

  const { currentId, output, reset, onSaved, restore } = useToolState(projectId, 'meta');

  const m = useMutation({
    mutationFn: () => contentApi.meta(projectId, { content: content || undefined, url: url || undefined, n_variants: 5 }),
    onSuccess: ({ id, result }) => { onSaved(id, result); toast.success('Meta variants saved'); },
  });

  const onLoad = async (id) => {
    const rec = await contentApi.historyOne(projectId, id);
    setUrl(rec.input?.url || '');
    setContent(rec.input?.content || '');
    restore(rec);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px_320px] gap-px bg-line">
      <div className="bg-ink-200 p-5 space-y-4">
        <Input label="URL (optional)" placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} />
        <Textarea label="Content" placeholder="Paste page content..." value={content} onChange={(e) => setContent(e.target.value)} rows={14} />
        <div className="flex gap-2">
          <Button variant="primary" onClick={() => m.mutate()} loading={m.isPending} disabled={!content && !url} className="flex-1">
            <Tag className="w-3.5 h-3.5" /> generate variants
          </Button>
          {output && <Button variant="ghost" onClick={reset}><RotateCcw className="w-3.5 h-3.5" /></Button>}
        </div>
        {currentId && (
          <p className="text-2xs font-mono uppercase tracking-widest2 text-dim border-t border-line pt-3">
            ● viewing saved · #{String(currentId).slice(0, 8)}
          </p>
        )}
      </div>

      <div className="bg-ink-200 p-6">
        {!output && !m.isPending && <Empty title="Title & meta variants" description="5 high-CTR variants will appear here." />}
        {m.isPending && <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-16" />)}</div>}
        {output && (
          <div className="space-y-3">
            {(output.variants || []).map((v, i) => (
              <div key={i} className="panel-soft p-4 space-y-2">
                <p className="eyebrow !text-2xs">● VARIANT {String(i + 1).padStart(2, '0')} · {v.tone}</p>
                <p className="font-display text-lg text-bone leading-snug" style={{ fontVariationSettings: "'opsz' 72, 'WONK' 1" }}>
                  {v.title}
                </p>
                <p className="text-sm text-muted">{v.meta_description}</p>
                <p className="text-2xs font-mono uppercase tracking-widest2 text-signal">CTR · {v.estimated_ctr_lift}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <HistoryRail projectId={projectId} toolType="meta" currentId={currentId} onLoad={onLoad} />
    </div>
  );
}

/* ──────────── 4. Calendar ──────────── */

function CalendarTool({ projectId }) {
  const [niche, setNiche] = useState('');
  const [goals, setGoals] = useState('');
  const [days, setDays] = useState(30);

  const { currentId, output, reset, onSaved, restore } = useToolState(projectId, 'calendar');

  const m = useMutation({
    mutationFn: () => contentApi.calendar(projectId, { niche, goals, days }),
    onSuccess: ({ id, result }) => { onSaved(id, result); toast.success('Calendar saved'); },
  });

  const onLoad = async (id) => {
    const rec = await contentApi.historyOne(projectId, id);
    setNiche(rec.input?.niche || '');
    setGoals(rec.input?.goals || '');
    setDays(rec.input?.days || 30);
    restore(rec);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-px bg-line">
        <div className="bg-ink-200 p-5 grid grid-cols-1 lg:grid-cols-3 gap-3 items-end">
          <Input label="Niche" placeholder="Vegan running shoes" value={niche} onChange={(e) => setNiche(e.target.value)} />
          <Textarea
            label="Goals"
            placeholder="Drive top-of-funnel traffic, build authority for 'vegan running' cluster, capture comparison queries"
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            rows={3}
          />
          <div className="flex gap-3">
            <Select label="Days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </Select>
            <Button variant="primary" onClick={() => m.mutate()} loading={m.isPending} disabled={!niche.trim() || !goals.trim()} className="flex-1 self-end">
              <Calendar className="w-3.5 h-3.5" /> plan
            </Button>
            {output && <Button variant="ghost" onClick={reset} className="self-end"><RotateCcw className="w-3.5 h-3.5" /></Button>}
          </div>
        </div>
        <HistoryRail projectId={projectId} toolType="calendar" currentId={currentId} onLoad={onLoad} />
      </div>

      {output && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-line">
          {(output.items || []).map((it, i) => (
            <div key={i} className="bg-ink-200 p-4">
              <div className="flex items-baseline gap-3 mb-2">
                <span className="num-display text-2xl text-signal" style={{ fontVariationSettings: "'opsz' 72, 'WONK' 1" }}>
                  {String(it.day).padStart(2, '0')}
                </span>
                <span className="font-mono text-2xs uppercase tracking-widest2 text-dim">{it.format}</span>
                <span className="ml-auto font-mono text-2xs text-dim">{it.word_count}w</span>
              </div>
              <p className="text-sm text-bone leading-tight mb-1">{it.title}</p>
              <p className="text-2xs font-mono text-muted">{it.primary_keyword}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ──────────── Helpers ──────────── */

function Stat({ label, value, small }) {
  return (
    <div className="bg-ink-200 p-4">
      <p className="eyebrow !text-2xs mb-2">{label}</p>
      {small ? (
        <p className="text-sm text-bone">{value || '—'}</p>
      ) : (
        <p className="num-display text-2xl text-bone" style={{ fontVariationSettings: "'opsz' 72" }}>{value || '—'}</p>
      )}
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-ink-200 p-3 text-center">
      <p className="eyebrow !text-2xs mb-1.5 before:!w-1 before:!h-1">{label}</p>
      <p className="num-mono text-base text-bone">{value}</p>
    </div>
  );
}

function Block({ title, children }) {
  return (
    <div>
      <p className="eyebrow mb-3">● {title}</p>
      {children}
    </div>
  );
}

function ChipList({ items, tone }) {
  if (!items || items.length === 0) return <p className="text-2xs font-mono text-dim">—</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((s, i) => (
        <span
          key={i}
          className={`px-2 py-1 border font-mono text-2xs uppercase tracking-widest2 ${
            tone === 'signal' ? 'border-signal/40 text-signal bg-signal/5' : 'border-line2 text-muted'
          }`}
        >
          {s}
        </span>
      ))}
    </div>
  );
}
