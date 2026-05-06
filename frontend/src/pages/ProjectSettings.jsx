import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ExternalLink, Link2, Unlink } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

import { projectsApi, tagsApi, gscApi } from '@/api';
import { COUNTRIES } from '@/lib/countries';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';

export default function ProjectSettings() {
  const { projectId } = useParams();
  const qc = useQueryClient();
  const [params] = useSearchParams();

  useEffect(() => {
    if (params.get('gsc') === 'connected') {
      toast.success('Google Search Console connected');
    }
  }, [params]);

  const projectQ = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.get(projectId) });
  const tagsQ = useQuery({ queryKey: ['tags', 'list'], queryFn: () => tagsApi.list() });
  const gscStatusQ = useQuery({ queryKey: ['gsc', 'status', projectId], queryFn: () => gscApi.status(projectId) });
  const gscPropsQ = useQuery({
    queryKey: ['gsc', 'props', projectId],
    queryFn: () => gscApi.properties(projectId),
    enabled: !!gscStatusQ.data?.connected,
  });

  const [form, setForm] = useState(null);
  useEffect(() => {
    if (projectQ.data && !form) {
      setForm({
        name: projectQ.data.name,
        domain: projectQ.data.domain,
        country: projectQ.data.country,
        competitors: (projectQ.data.competitors || []).join(', '),
        tag_ids: (projectQ.data.tags || []).map((t) => t.id),
        gsc_property: projectQ.data.gsc_property || '',
      });
    }
  }, [projectQ.data, form]);

  const update = useMutation({
    mutationFn: (body) => projectsApi.update(projectId, body),
    onSuccess: () => {
      toast.success('Saved');
      qc.invalidateQueries({ queryKey: ['project', projectId] });
      qc.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const setGscProp = useMutation({
    mutationFn: (site_url) => gscApi.setProperty(projectId, site_url),
    onSuccess: () => {
      toast.success('GSC property set');
      qc.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  const disconnectGsc = useMutation({
    mutationFn: () => gscApi.disconnect(projectId),
    onSuccess: () => {
      toast.success('Disconnected');
      qc.invalidateQueries({ queryKey: ['gsc'] });
      qc.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  const onConnectGsc = async () => {
    try {
      const { auth_url } = await gscApi.authUrl(projectId);
      window.location.href = auth_url;
    } catch (e) { /* toast already shown */ }
  };

  if (!form) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">
      <PageHeader
        eyebrow="WORKSPACE / SETTINGS"
        title={<>{form.name} <em className="text-signal not-italic">/ config</em></>}
        kicker={form.domain}
      />

      <section className="space-y-5">
        <SectionHeading eyebrow="● PROFILE" title="Project profile" />
        <div className="grid sm:grid-cols-2 gap-4">
          <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Domain" value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} />
          <Select label="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}>
            {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.label}</option>)}
          </Select>
          <Input
            label="Competitors"
            value={form.competitors}
            onChange={(e) => setForm({ ...form, competitors: e.target.value })}
            hint="Comma-separated up to 5"
          />
        </div>

        <div>
          <p className="eyebrow !text-2xs mb-2">Tags</p>
          <div className="flex flex-wrap gap-2">
            {(tagsQ.data || []).map((t) => {
              const on = form.tag_ids.includes(t.id);
              return (
                <button
                  key={t.id} type="button"
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
                >{t.name}</button>
              );
            })}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button
            variant="primary"
            loading={update.isPending}
            onClick={() => update.mutate({
              name: form.name,
              domain: form.domain,
              country: form.country,
              competitors: form.competitors.split(',').map((s) => s.trim()).filter(Boolean),
              tag_ids: form.tag_ids,
            })}
          >
            save changes
          </Button>
        </div>
      </section>

      <section className="space-y-5">
        <SectionHeading
          eyebrow="● GSC / GOOGLE SEARCH CONSOLE"
          title="Search Console"
          kicker="OAuth connection per project. Refresh token is encrypted at rest."
        />
        {gscStatusQ.data?.connected ? (
          <div className="panel p-5 space-y-5">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-plus" />
                <span className="text-bone">Connected</span>
              </p>
              <Button variant="danger" onClick={() => { if (window.confirm('Disconnect GSC?')) disconnectGsc.mutate(); }}>
                <Unlink className="w-3.5 h-3.5" /> disconnect
              </Button>
            </div>
            <div>
              <p className="eyebrow !text-2xs mb-2">Property</p>
              <Select
                value={projectQ.data.gsc_property || ''}
                onChange={(e) => setGscProp.mutate(e.target.value)}
              >
                <option value="">— select —</option>
                {(gscPropsQ.data || []).map((p) => (
                  <option key={p.site_url} value={p.site_url}>{p.site_url}</option>
                ))}
              </Select>
              <p className="text-xs text-dim font-mono mt-2">
                Permissions: {(gscPropsQ.data || []).find((p) => p.site_url === projectQ.data.gsc_property)?.permission_level || '—'}
              </p>
            </div>
          </div>
        ) : (
          <div className="panel p-8 flex items-center justify-between">
            <div>
              <p className="eyebrow mb-3">Not connected</p>
              <h3 className="font-display text-xl text-bone mb-2" style={{ fontVariationSettings: "'opsz' 72" }}>
                Authorize Google Search Console
              </h3>
              <p className="text-sm text-muted max-w-md">
                Connect to import organic clicks, impressions, top keywords and pages directly from your verified property.
              </p>
            </div>
            <Button variant="primary" onClick={onConnectGsc}>
              <Link2 className="w-3.5 h-3.5" /> connect <ExternalLink className="w-3 h-3" />
            </Button>
          </div>
        )}
      </section>
    </motion.div>
  );
}
