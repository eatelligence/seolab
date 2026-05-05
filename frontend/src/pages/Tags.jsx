import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

import { tagsApi } from '@/api';
import { PageHeader } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Empty } from '@/components/ui/Empty';

const PRESET_COLORS = ['#D4F542', '#4ADE80', '#60A5FA', '#FACC15', '#F87171', '#A78BFA', '#F472B6', '#FB923C'];

export default function Tags() {
  const qc = useQueryClient();
  const tagsQ = useQuery({ queryKey: ['tags', 'list'], queryFn: () => tagsApi.list() });
  const [name, setName] = useState('');
  const [color, setColor] = useState('#D4F542');

  const create = useMutation({
    mutationFn: (body) => tagsApi.create(body),
    onSuccess: () => {
      toast.success('Tag created');
      qc.invalidateQueries({ queryKey: ['tags'] });
      qc.invalidateQueries({ queryKey: ['projects'] });
      setName('');
    },
  });
  const remove = useMutation({
    mutationFn: (id) => tagsApi.remove(id),
    onSuccess: () => {
      toast.success('Tag removed');
      qc.invalidateQueries({ queryKey: ['tags'] });
      qc.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">
      <PageHeader
        eyebrow="WORKSPACE / 02"
        title={<>Tags <em className="text-signal not-italic">/ taxonomy</em></>}
        kicker="Group projects by client, vertical, or campaign. Tags appear in the sidebar switcher and project filter."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-px bg-line">
        <div className="bg-ink-200 p-6">
          {tagsQ.isLoading ? null : (tagsQ.data || []).length === 0 ? (
            <Empty title="No tags yet" description="Create your first tag to organize projects." />
          ) : (
            <div className="grid sm:grid-cols-2 gap-px bg-line">
              {(tagsQ.data || []).map((t, i) => (
                <motion.div
                  key={t.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="group bg-ink-200 p-4 flex items-center gap-3 hover:bg-ink-100 transition-colors"
                >
                  <span className="w-2 h-12" style={{ backgroundColor: t.color }} />
                  <div className="flex-1 min-w-0">
                    <p className="font-mono text-2xs uppercase tracking-widest2" style={{ color: t.color }}>
                      {t.name}
                    </p>
                    <p className="text-2xs font-mono text-dim mt-0.5 num-mono">{t.color}</p>
                  </div>
                  <button
                    onClick={() => { if (window.confirm(`Delete tag "${t.name}"?`)) remove.mutate(t.id); }}
                    className="opacity-0 group-hover:opacity-100 text-dim hover:text-minus transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-ink-200 p-6">
          <p className="eyebrow mb-4">Create tag</p>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (!name.trim()) return;
              create.mutate({ name: name.trim(), color });
            }}
          >
            <Input label="Name" placeholder="Clienti 2026" value={name} onChange={(e) => setName(e.target.value)} required />
            <div>
              <p className="eyebrow !text-2xs mb-2">Color</p>
              <div className="flex flex-wrap gap-1.5">
                {PRESET_COLORS.map((c) => (
                  <button
                    key={c} type="button"
                    onClick={() => setColor(c)}
                    className="w-7 h-7 border-2 transition-all"
                    style={{
                      backgroundColor: c,
                      borderColor: color === c ? '#E5E7EB' : 'transparent',
                    }}
                  />
                ))}
              </div>
              <Input
                className="mt-2"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                placeholder="#D4F542"
              />
            </div>
            <Button variant="primary" type="submit" loading={create.isPending} className="w-full">
              <Plus className="w-3.5 h-3.5" /> create tag
            </Button>
          </form>
        </div>
      </div>
    </motion.div>
  );
}
