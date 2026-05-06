import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { post, get, tokenStore } from '@/lib/api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading'); // 'loading' | 'authed' | 'anon'

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setUser(null);
      setStatus('anon');
      return;
    }
    try {
      const me = await get('/auth/me');
      setUser(me);
      setStatus('authed');
    } catch {
      tokenStore.clear();
      setUser(null);
      setStatus('anon');
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    const res = await post('/auth/login', { email, password });
    tokenStore.set(res.access_token);
    setUser(res.user);
    setStatus('authed');
    return res.user;
  };

  const logout = async () => {
    try {
      await post('/auth/logout');
    } catch {
      /* token may already be invalid; ignore */
    }
    tokenStore.clear();
    setUser(null);
    setStatus('anon');
    window.location.href = '/login';
  };

  return (
    <AuthCtx.Provider value={{ user, status, login, logout, refresh }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error('useAuth must be inside <AuthProvider>');
  return ctx;
}
