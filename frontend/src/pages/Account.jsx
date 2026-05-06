import { useState } from 'react';
import { motion } from 'framer-motion';
import { LogOut, KeyRound } from 'lucide-react';
import { toast } from 'sonner';

import { post } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { PageHeader, SectionHeading } from '@/components/SectionHeading';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function Account() {
  const { user, logout } = useAuth();
  const [form, setForm] = useState({ current: '', next: '', confirm: '' });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (form.next !== form.confirm) {
      toast.error('New passwords do not match');
      return;
    }
    if (form.next.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await post('/auth/change-password', {
        current_password: form.current,
        new_password: form.next,
      });
      toast.success('Password changed');
      setForm({ current: '', next: '', confirm: '' });
    } catch {
      // toast already shown by interceptor
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">
      <PageHeader
        eyebrow="WORKSPACE / ACCOUNT"
        title={<>Account <em className="text-signal not-italic">/ session</em></>}
        kicker="Authenticated as the account below. Sessions are JWT-signed with the server SECRET_KEY (TTL 7 days)."
      />

      <section className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-px bg-line">
        <div className="bg-ink-200 p-6">
          <p className="eyebrow mb-4">● IDENTITY</p>
          <div className="space-y-3">
            <Field label="Email" value={user?.email} mono />
            <Field label="Role" value={user?.is_admin ? 'admin' : 'user'} />
            <Field label="User ID" value={user?.id} mono small />
          </div>
          <Button variant="danger" className="mt-6" onClick={logout}>
            <LogOut className="w-3.5 h-3.5" /> sign out
          </Button>
        </div>

        <div className="bg-ink-200 p-6">
          <SectionHeading eyebrow="● SECURITY" title="Change password" />
          <form onSubmit={submit} className="mt-6 grid grid-cols-1 gap-4 max-w-md">
            <Input
              label="Current password"
              type="password"
              required
              value={form.current}
              onChange={(e) => setForm({ ...form, current: e.target.value })}
              autoComplete="current-password"
            />
            <Input
              label="New password"
              type="password"
              required
              value={form.next}
              onChange={(e) => setForm({ ...form, next: e.target.value })}
              hint="min 8 characters"
              autoComplete="new-password"
            />
            <Input
              label="Confirm new password"
              type="password"
              required
              value={form.confirm}
              onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              autoComplete="new-password"
            />
            <Button variant="primary" type="submit" loading={loading} className="mt-2 self-start">
              <KeyRound className="w-3.5 h-3.5" /> rotate password
            </Button>
          </form>
        </div>
      </section>
    </motion.div>
  );
}

function Field({ label, value, mono, small }) {
  return (
    <div>
      <p className="font-mono text-2xs uppercase tracking-widest2 text-dim mb-1">{label}</p>
      <p className={`text-bone ${mono ? 'font-mono' : ''} ${small ? 'text-xs' : 'text-sm'} break-all`}>
        {value || '—'}
      </p>
    </div>
  );
}
