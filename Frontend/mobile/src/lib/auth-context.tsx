import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from 'react';
import { clearStoredSession, getMyProfile, hasStoredSession, login, logout as logoutRequest, type AuthUser } from './session-api';

type AuthContextValue = { user: AuthUser | null; isReady: boolean; signIn: (email: string, password: string) => Promise<AuthUser>; updateUser: (user: AuthUser) => void; signOut: () => Promise<void> };
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);
  useEffect(() => {
    let mounted = true;
    const restore = async () => {
      try {
        if (!await hasStoredSession()) return;
        const profile = await getMyProfile();
        if (mounted) setUser(profile);
      }
      catch {
        if (mounted) setUser(null);
        await clearStoredSession();
      }
      finally { if (mounted) setIsReady(true); }
    };
    void restore(); return () => { mounted = false; };
  }, []);
  const signIn = useCallback(async (email: string, password: string) => { const profile = await login(email, password); setUser(profile); return profile; }, []);
  const updateUser = useCallback((profile: AuthUser) => setUser(profile), []);
  const signOut = useCallback(async () => { try { await logoutRequest(); } finally { setUser(null); } }, []);
  return <AuthContext.Provider value={{ user, isReady, signIn, updateUser, signOut }}>{children}</AuthContext.Provider>;
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error('useAuth doit être utilisé dans AuthProvider.'); return context; }
