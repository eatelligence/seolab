import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Search, ExternalLink, Globe2 } from 'lucide-react';

import { serpApi, projectsApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Empty } from '@/components/ui/Empty';
import { Badge } from '@/components/ui/Badge';
import { COUNTRIES } from '@/lib/countries';
import { fmtRelative } from '@/lib/format';

export default function SerpOverview() {
  const { projectId } = useParams();
  const projectQ = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.get(projectId) });

  const [keyword, setKeyword] = useState('');
  const [country, setCountry] = useState('');

  const m = useMutation({
    mutationFn: () => serpApi.overview(projectId, { keyword: keyword.trim(), country: country || projectQ.data?.country || 'US' }),
  });

  const data = m.data;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 09"
        title={<>SERP <em className="text-signal not-italic">Overview</em></>}
        kicker="Look up the live top-20 organic results for any keyword in any geo, without having to track it. Cached at 6h."
      />

      <div className="panel p-5">
        <form
          className="grid grid-cols-1 md:grid-cols-[1fr_220px_auto] gap-3 items-end"
          onSubmit={(e) => { e.preventDefault(); if (keyword.trim()) m.mutate(); }}
        >
          <Input
            label="Keyword"
            placeholder="best running shoes"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            autoFocus
          />
          <Select
            label="Country"
            value={country || projectQ.data?.country || 'US'}
            onChange={(e) => setCountry(e.target.value)}
          >
            {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.label}</option>)}
          </Select>
          <Button variant="primary" type="submit" loading={m.isPending} disabled={!keyword.trim()}>
            <Search className="w-3.5 h-3.5" /> lookup
          </Button>
        </form>
      </div>

      {!data && !m.isPending && (
        <Empty
          icon={Globe2}
          title="Live SERP lookup"
          description="Enter a keyword and geo to fetch the live top-20 organic results, with your domain and tracked competitors highlighted."
        />
      )}

      {m.isPending && (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => <div key={i} className="shimmer h-16" />)}
        </div>
      )}

      {data && (
        <>
          <ResultMeta data={data} />
          <ResultList data={data} />
        </>
      )}
    </motion.div>
  );
}

function ResultMeta({ data }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-px bg-line">
      <Stat label="Keyword" value={data.keyword} mono />
      <Stat label="Country" value={data.country} />
      <Stat
        label="Your position"
        value={data.target_position ? `#${data.target_position}` : 'not in top 100'}
        accent={data.target_position && data.target_position <= 10}
        muted={!data.target_position}
      />
      <Stat
        label="SERP features"
        value={data.serp_features?.length ? data.serp_features.length : '—'}
        small
        hint={(data.serp_features || []).slice(0, 3).join(' · ')}
      />
    </div>
  );
}

function Stat({ label, value, mono, small, accent, muted, hint }) {
  return (
    <div className="bg-ink-200 p-5">
      <p className="eyebrow !text-2xs mb-3">{label}</p>
      <p
        className={`num-display leading-none ${small ? 'text-2xl' : 'text-3xl'} ${
          accent ? 'text-signal' : muted ? 'text-dim' : 'text-bone'
        } ${mono ? '!font-mono' : ''}`}
        style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}
      >
        {value}
      </p>
      {hint && <p className="mt-2 text-2xs font-mono uppercase tracking-widest2 text-dim truncate">{hint}</p>}
    </div>
  );
}

function ResultList({ data }) {
  return (
    <div className="panel">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-line">
        <p className="eyebrow !text-2xs">● TOP 20 ORGANIC</p>
        <span className="font-mono text-2xs text-dim">checked {fmtRelative(data.checked_at)}</span>
      </div>
      <div className="space-y-px bg-line">
        {(data.items || []).map((it) => (
          <div
            key={it.rank}
            className={`bg-ink-200 p-4 flex gap-4 hover:bg-ink-100 transition-colors ${
              it.is_self ? 'border-l-2 border-signal' : it.is_competitor ? 'border-l-2 border-info' : ''
            }`}
          >
            <span className="num-display text-3xl text-bone w-12 shrink-0 leading-none"
                  style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
              {String(it.rank).padStart(2, '0')}
            </span>
            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <a href={it.url} target="_blank" rel="noreferrer"
                   className="text-bone hover:text-signal text-base leading-tight font-display"
                   style={{ fontVariationSettings: "'opsz' 72" }}>
                  {it.title}
                </a>
                {it.is_self && <Badge tone="signal">YOU</Badge>}
                {it.is_competitor && <Badge tone="info">competitor</Badge>}
              </div>
              <p className="font-mono text-2xs text-muted truncate flex items-center gap-1">
                <Globe2 className="w-3 h-3 inline shrink-0" /> {it.domain}
              </p>
              {it.snippet && (
                <p className="text-xs text-muted leading-snug line-clamp-2">{it.snippet}</p>
              )}
            </div>
            <a href={it.url} target="_blank" rel="noreferrer" className="text-dim hover:text-signal shrink-0">
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
