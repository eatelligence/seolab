import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/Input';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
      const redirect = new URLSearchParams(location.search).get('next') || '/';
      navigate(redirect, { replace: true });
    } catch (err) {
      setError('Invalid credentials');
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full grid lg:grid-cols-[1fr_minmax(360px,420px)] bg-ink-400 text-bone overflow-hidden">
      {/* Decorative panel — left */}
      <aside className="relative hidden lg:flex flex-col justify-between p-10 border-r border-line">
        <div className="absolute inset-0 stripes opacity-40 pointer-events-none" />
        <div className="relative">
          <p className="font-mono text-2xs uppercase tracking-widest2 text-dim flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse-dot" />
            ACCESS / SECURE PORT // 01
          </p>
          <h1
            className="mt-10 font-display text-bone leading-[0.95]"
            style={{ fontVariationSettings: "'opsz' 144, 'WONK' 1", fontSize: 'clamp(72px, 9vw, 144px)', letterSpacing: '-0.04em' }}
          >
            Search<br />
            <em className="text-signal not-italic">Intelligence</em>
          </h1>
          <p className="mt-8 max-w-md text-base text-muted leading-relaxed">
            Self-hosted SEO platform. Multi-project search analytics, audits,
            backlinks, AI visibility — running on your infrastructure.
          </p>
        </div>

        {/* Animated marquee badge strip */}
        <div className="relative overflow-hidden border-y border-line py-3">
          <div className="flex gap-12 animate-marquee whitespace-nowrap font-mono text-xs uppercase tracking-widest2 text-dim">
            {Array.from({ length: 2 }).map((_, k) => (
              <div key={k} className="flex gap-12">
                <span>● GSC · LIVE</span>
                <span>● DATAFORSEO · LIVE</span>
                <span>● CLAUDE SONNET 4.5</span>
                <span>● PAGESPEED · CWV</span>
                <span>● OPEN PAGERANK</span>
                <span>● CELERY · BEAT</span>
                <span>● POSTGRES · 15</span>
                <span>● REDIS · 7</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative font-mono text-2xs uppercase tracking-widest2 text-dim">
          <span className="text-bone">SEOLAB v0.1.0</span> · 2026 · self-hosted single-tenant
        </div>
      </aside>

      {/* Form — right */}
      <main className="flex items-center justify-center p-8 sm:p-12">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-sm"
        >
          <p className="eyebrow mb-6">● AUTHENTICATE</p>
          <h2
            className="font-display text-5xl text-bone mb-2 leading-none"
            style={{ fontVariationSettings: "'opsz' 96, 'WONK' 1", letterSpacing: '-0.025em' }}
          >
            Sign in
          </h2>
          <p className="text-sm text-muted mb-10 font-sans">
            Enter your credentials to access the workspace.
          </p>

          <form onSubmit={onSubmit} className="space-y-5">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              autoFocus
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              error={error || undefined}
            />

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full h-11 mt-2 bg-signal text-ink-400 hover:bg-signal-glow border border-signal font-mono uppercase tracking-widest2 text-2xs flex items-center justify-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed focus-ring hover:shadow-glow"
            >
              {loading ? (
                <span className="w-3 h-3 border border-current border-r-transparent rounded-full animate-spin" />
              ) : (
                <>access workspace <ArrowRight className="w-3.5 h-3.5" /></>
              )}
            </button>
          </form>

          <div className="mt-12 pt-6 border-t border-line">
            <p className="font-mono text-2xs uppercase tracking-widest2 text-dim leading-relaxed">
              <span className="text-bone">REC ● </span>
              session signed with HS256 · token TTL 7d
              <br />
              <span className="text-dim/60">all routes protected · /api/health public</span>
            </p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
