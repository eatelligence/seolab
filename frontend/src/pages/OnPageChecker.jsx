import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ScanLine, FileSearch, ExternalLink } from 'lucide-react';

import { onpageApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Empty } from '@/components/ui/Empty';
import { SeverityBadge } from '@/components/ui/Badge';
import { HealthRing } from '@/components/HealthRing';
import { fmtNum } from '@/lib/format';

export default function OnPageChecker() {
  const { projectId } = useParams();
  const [url, setUrl] = useState('');
  const [withPSI, setWithPSI] = useState(true);

  const m = useMutation({
    mutationFn: () => onpageApi.check(projectId, { url: url.trim(), pagespeed: withPSI }),
  });

  const data = m.data;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <PageHeader
        eyebrow="MODULE / 11"
        title={<>On-page <em className="text-signal not-italic">SEO Checker</em></>}
        kicker="Single-URL deep audit. Same checks as Site Audit + live Core Web Vitals via PageSpeed Insights, in one shot."
      />

      <div className="panel p-5">
        <form
          className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-3 items-end"
          onSubmit={(e) => { e.preventDefault(); if (url.trim()) m.mutate(); }}
        >
          <Input
            label="URL"
            placeholder="https://example.com/blog/article"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoFocus
          />
          <label className="flex items-end gap-2 pb-2">
            <input type="checkbox" checked={withPSI} onChange={(e) => setWithPSI(e.target.checked)} className="accent-signal" />
            <span className="font-mono text-2xs uppercase tracking-widest2 text-bone">PageSpeed</span>
          </label>
          <Button variant="primary" type="submit" loading={m.isPending} disabled={!url.trim()}>
            <ScanLine className="w-3.5 h-3.5" /> analyze
          </Button>
        </form>
      </div>

      {!data && !m.isPending && (
        <Empty
          icon={FileSearch}
          title="Single-URL audit"
          description="Paste any URL to fetch it, run the 14 SEO checks, and (optionally) call PageSpeed for Core Web Vitals."
        />
      )}

      {m.isPending && (
        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-px bg-line">
          <div className="bg-ink-200 h-[260px] shimmer" />
          <div className="bg-ink-200 p-5 space-y-3">
            {Array.from({ length: 8 }).map((_, i) => <div key={i} className="shimmer h-8" />)}
          </div>
        </div>
      )}

      {data && <Result data={data} />}
    </motion.div>
  );
}

function Result({ data }) {
  const psi = data.pagespeed || {};
  const lab = psi.lab || {};
  const field = psi.field || {};
  const lcp = field.lcp_ms || lab.lcp_ms;
  const cls = field.cls != null ? field.cls : lab.cls;
  const inp = field.inp_ms;

  return (
    <div className="space-y-6">
      {/* Header strip */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-px bg-line">
        <div className="bg-ink-200 p-5 flex flex-col items-center justify-center">
          <HealthRing score={data.score} size={180} label="ON-PAGE" />
        </div>
        <div className="bg-ink-200 p-5">
          <p className="eyebrow mb-3">● PAGE PROFILE</p>
          <h2 className="font-display text-2xl text-bone leading-snug mb-2"
              style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
            {data.title || <span className="text-minus">[no title]</span>}
          </h2>
          <p className="text-sm text-muted mb-3">
            {data.meta_description || <span className="text-minus">[no meta description]</span>}
          </p>
          <p className="font-mono text-2xs text-dim flex items-center gap-2 truncate">
            <ExternalLink className="w-3 h-3 shrink-0" />
            <a href={data.final_url} target="_blank" rel="noreferrer" className="hover:text-signal truncate">
              {data.final_url}
            </a>
          </p>

          <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-px bg-line">
            <Stat label="Status" value={data.status_code} accent={data.status_code >= 400 ? 'minus' : 'bone'} />
            <Stat label="Words" value={data.word_count} />
            <Stat label="H1" value={data.h1_count} accent={data.h1_count !== 1 ? 'warn' : 'bone'} />
            <Stat label="Load" value={`${data.load_time_ms}ms`} accent={data.load_time_ms > 3000 ? 'minus' : 'bone'} />
          </div>
        </div>
      </div>

      {/* CWV */}
      {psi.performance_score !== undefined && (
        <div>
          <p className="eyebrow mb-3">● CORE WEB VITALS · MOBILE</p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
            <Stat label="Performance" value={psi.performance_score} unit="/100" accent={psi.performance_score < 50 ? 'minus' : psi.performance_score < 70 ? 'warn' : 'plus'} big />
            <Stat label="LCP" value={lcp ? `${(lcp / 1000).toFixed(1)}s` : '—'} accent={!lcp ? 'dim' : lcp > 4000 ? 'minus' : lcp > 2500 ? 'warn' : 'plus'} big />
            <Stat label="CLS" value={cls != null ? fmtNum(cls, 2) : '—'} accent={cls == null ? 'dim' : cls > 0.25 ? 'minus' : cls > 0.1 ? 'warn' : 'plus'} big />
            <Stat label="INP" value={inp ? `${inp}ms` : '—'} accent={!inp ? 'dim' : inp > 500 ? 'minus' : inp > 200 ? 'warn' : 'plus'} big />
          </div>
        </div>
      )}

      {/* Issues */}
      <div>
        <p className="eyebrow mb-3">● ISSUES · {data.issues.length}</p>
        {data.issues.length === 0 ? (
          <div className="panel p-8 text-center">
            <p className="font-display text-3xl text-plus" style={{ fontVariationSettings: "'WONK' 1" }}>Clean</p>
            <p className="text-sm text-muted mt-2">No issues detected on this page.</p>
          </div>
        ) : (
          <div className="space-y-px bg-line">
            {data.issues.map((iss, i) => (
              <div key={i} className="bg-ink-200 p-4 flex items-start gap-4">
                <SeverityBadge severity={iss.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-bone capitalize">{iss.issue_type.replaceAll('_', ' ')}</p>
                  {Object.keys(iss.details || {}).length > 0 && (
                    <p className="font-mono text-2xs text-dim mt-1 truncate">
                      {Object.entries(iss.details).map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v).slice(0, 50) : String(v).slice(0, 80)}`).join(' · ')}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
        <Stat label="Links internal" value={data.links_internal_count} />
        <Stat label="Links external" value={data.links_external_count} />
        <Stat label="Images" value={`${data.images_total}`} hint={`${data.images_missing_alt} no alt · ${data.images_oversized} oversized`} />
        <Stat label="Structured data" value={data.has_structured_data ? '✓' : '✗'} accent={data.has_structured_data ? 'plus' : 'warn'} />
      </div>
    </div>
  );
}

const accents = {
  bone: 'text-bone', plus: 'text-plus', minus: 'text-minus', warn: 'text-warn', dim: 'text-dim',
};

function Stat({ label, value, unit, hint, accent = 'bone', big = false }) {
  return (
    <div className="bg-ink-200 p-4">
      <p className="eyebrow !text-2xs mb-2">{label}</p>
      <p
        className={`num-display leading-none ${big ? 'text-3xl' : 'text-xl'} ${accents[accent] || 'text-bone'}`}
        style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}
      >
        {value}{unit && <span className="text-xs font-mono text-dim ml-1">{unit}</span>}
      </p>
      {hint && <p className="text-2xs font-mono text-dim mt-2">{hint}</p>}
    </div>
  );
}
