import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from 'react';

import { getMyProfile, logout as logoutRequest, type AuthUser } from './api';

type AuthContextValue = {
  user: AuthUser | null;
  isReady: boolean;
  signIn: (user: AuthUser) => void;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    getMyProfile().then((profile) => { if (mounted) setUser(profile); }).catch(() => {
      if (mounted) setUser(null);
    }).finally(() => { if (mounted) setIsReady(true); });
    return () => { mounted = false; };
  }, []);

  const signIn = useCallback((profile: AuthUser) => setUser(profile), []);
  const signOut = useCallback(async () => {
    try { await logoutRequest(); } finally { setUser(null); }
  }, []);

  return <AuthContext.Provider value={{ user, isReady, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth doit être utilisé dans AuthProvider.');
  return context;
}
