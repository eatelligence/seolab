import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Globe2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

import { projectsApi, tagsApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Modal } from '@/components/ui/Modal';
import { Empty } from '@/components/ui/Empty';
import { useProject } from '@/context/ProjectContext';
import { fmtDate } from '@/lib/format';

const COUNTRIES = [
  'US', 'GB', 'IT', 'ES', 'FR', 'DE', 'PT', 'NL', 'CH', 'AT',
  'SE', 'NO', 'DK', 'BR', 'MX', 'AR', 'CA', 'AU', 'JP', 'IN',
];

export default function Projects() {
  const qc = useQueryClient();
  const { setActiveId } = useProject();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [tagFilter, setTagFilter] = useState('');

  const projectsQ = useQuery({ queryKey: ['projects', 'list'], queryFn: () => projectsApi.list() });
  const tagsQ = useQuery({ queryKey: ['tags', 'list'], queryFn: () => tagsApi.list() });

  const remove = useMutation({
    mutationFn: (id) => projectsApi.remove(id),
    onSuccess: () => {
      toast.success('Project removed');
      qc.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const filtered = (projectsQ.data || []).filter((p) =>
    !tagFilter || p.tags?.some((t) => t.id === tagFilter)
  );

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="space-y-10">
      <PageHeader
        eyebrow="WORKSPACE / 01"
        title={<>Projects <em className="text-signal not-italic">/ portfolio</em></>}
        kicker="Each project is an isolated SEO surface — keywords, rankings, audits, backlinks, AI visibility, GSC tokens, all scoped to one domain."
        action={
          <div className="flex gap-2">
            <Select
              label=""
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              className="min-w-[160px]"
            >
              <option value="">all tags</option>
              {(tagsQ.data || []).map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </Select>
            <Button variant="primary" onClick={() => setOpen(true)}><Plus className="w-3.5 h-3.5" /> New Project</Button>
          </div>
        }
        meta={
          <>
            <span>{(projectsQ.data || []).length} projects</span>
            <span className="text-line2">·</span>
            <span>{(tagsQ.data || []).length} tags</span>
          </>
        }
      />

      {projectsQ.isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-line">
          {Array.from({ length: 6 }).map((_, i) => <div key={i} className="bg-ink-200 h-44 shimmer" />)}
        </div>
      ) : filtered.length === 0 ? (
        <Empty
          icon={Globe2}
          title="No projects yet"
          description="Add your first domain to start tracking keywords, running audits and monitoring AI visibility."
          action={<Button variant="primary" onClick={() => setOpen(true)}><Plus className="w-3.5 h-3.5" /> Create project</Button>}
        />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-line">
          {filtered.map((p, i) => (
            <motion.button
              key={p.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.04 * i, duration: 0.3 }}
              onClick={() => { setActiveId(p.id); navigate(`/p/${p.id}/dashboard`); }}
              className="group relative bg-ink-200 hover:bg-ink-100 p-6 text-left transition-colors"
            >
              <span className="absolute top-0 left-0 w-2 h-px bg-signal opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="absolute top-0 left-0 w-px h-2 bg-signal opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="flex items-start justify-between mb-6">
                <span className="font-mono text-2xs uppercase tracking-widest2 text-dim">
                  // {String(i + 1).padStart(3, '0')}
                </span>
                <span className="font-mono text-2xs uppercase tracking-widest2 text-signal">{p.country}</span>
              </div>

              <h3 className="font-display text-2xl text-bone mb-1 leading-tight"
                  style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1" }}>
                {p.name}
              </h3>
              <p className="text-sm text-muted font-mono mb-6">{p.domain}</p>

              <div className="flex items-center justify-between text-2xs font-mono uppercase tracking-widest2 text-dim">
                <div className="flex gap-1.5 flex-wrap">
                  {(p.tags || []).slice(0, 3).map((t) => (
                    <span key={t.id} className="px-1.5 py-0.5 border" style={{ color: t.color, borderColor: t.color + '40' }}>
                      {t.name}
                    </span>
                  ))}
                  {(p.tags || []).length === 0 && <span className="text-dim/50">no tags</span>}
                </div>
                <span>{fmtDate(p.created_at)}</span>
              </div>

              <span
                role="button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`Delete "${p.name}"? This cascades to all SEO data.`)) {
                    remove.mutate(p.id);
                  }
                }}
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 text-dim hover:text-minus transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </span>
            </motion.button>
          ))}
        </div>
      )}

      <NewProjectModal
        open={open}
        onClose={() => setOpen(false)}
        tags={tagsQ.data || []}
        countries={COUNTRIES}
        onCreated={(p) => {
          setActiveId(p.id);
          navigate(`/p/${p.id}/dashboard`);
        }}
      />
    </motion.div>
  );
}

function NewProjectModal({ open, onClose, tags, countries, onCreated }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: '', domain: '', country: 'US', competitors: '', tag_ids: [] });

  const create = useMutation({
    mutationFn: (body) => projectsApi.create(body),
    onSuccess: (p) => {
      toast.success('Project created');
      qc.invalidateQueries({ queryKey: ['projects'] });
      setForm({ name: '', domain: '', country: 'US', competitors: '', tag_ids: [] });
      onClose();
      onCreated?.(p);
    },
  });

  const submit = (e) => {
    e.preventDefault();
    create.mutate({
      name: form.name,
      domain: form.domain,
      country: form.country,
      competitors: form.competitors.split(',').map((s) => s.trim()).filter(Boolean),
      tag_ids: form.tag_ids,
    });
  };

  return (
    <Modal
      open={open} onClose={onClose}
      eyebrow="WORKSPACE / NEW"
      title="Create project"
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>cancel</Button>
          <Button variant="primary" onClick={submit} loading={create.isPending}>create project</Button>
        </div>
      }
    >
      <form onSubmit={submit} className="grid grid-cols-2 gap-4">
        <Input label="Project name" placeholder="Acme Corp" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="col-span-2" />
        <Input label="Domain" placeholder="acme.com" required value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} hint="https:// and www. are stripped automatically" />
        <Select label="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}>
          {countries.map((c) => <option key={c} value={c}>{c}</option>)}
        </Select>
        <Input label="Competitors" placeholder="competitor1.com, competitor2.com"
          value={form.competitors} onChange={(e) => setForm({ ...form, competitors: e.target.value })}
          hint="Comma-separated. Up to 5 used for gap analysis." className="col-span-2" />
        <div className="col-span-2">
          <p className="eyebrow !text-2xs mb-2">Tags</p>
          <div className="flex flex-wrap gap-2">
            {tags.map((t) => {
              const on = form.tag_ids.includes(t.id);
              return (
                <button
                  type="button"
                  key={t.id}
                  onClick={() => setForm({
                    ...form,
                    tag_ids: on ? form.tag_ids.filter((x) => x !== t.id) : [...form.tag_ids, t.id],
                  })}
                  className="px-2 py-1 border font-mono text-2xs uppercase tracking-widest2 transition-colors"
                  style={{
                    borderColor: on ? t.color : '#1F2632',
                    color: on ? t.color : '#5A6377',
                    backgroundColor: on ? t.color + '10' : 'transparent',
                  }}
                >
                  {t.name}
                </button>
              );
            })}
            {tags.length === 0 && <span className="text-dim text-xs font-mono">No tags yet — create them in /tags</span>}
          </div>
        </div>
      </form>
    </Modal>
  );
}
