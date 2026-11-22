import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from 'react';

import { ApiError, getMyProfile, logout as logoutRequest, refreshTokens, type AuthTokens, type AuthUser, type LoginResponse } from './api';
import { clearTokens, readTokens, saveTokens } from './auth-storage';

type AuthContextValue = {
  user: AuthUser | null;
  isReady: boolean;
  signIn: (session: LoginResponse) => Promise<void>;
  signOut: () => Promise<void>;
  clearLocalSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    const restoreSession = async () => {
      try {
        const storedTokens = await readTokens();
        if (!storedTokens) return;

        try {
          const profile = await getMyProfile(storedTokens.access);
          if (mounted) setUser(profile);
          return;
        } catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401) return;
        }

        try {
          const renewedTokens = await refreshTokens(storedTokens.refresh);
          const profile = await getMyProfile(renewedTokens.access);
          await saveTokens(renewedTokens);
          if (mounted) setUser(profile);
        } catch (error) {
          if (error instanceof ApiError && [400, 401].includes(error.status)) {
            await clearTokens();
          }
        }
      } catch {
        // Keep stored tokens when the API is temporarily unreachable.
      } finally {
        if (mounted) setIsReady(true);
      }
    };

    void restoreSession();
    return () => {
      mounted = false;
    };
  }, []);

  const signIn = useCallback(async (session: LoginResponse) => {
    await saveTokens({ access: session.access, refresh: session.refresh });
    setUser(session.utilisateur);
  }, []);

  const signOut = useCallback(async () => {
    try {
      let tokens: AuthTokens | null = await readTokens();
      if (tokens) {
        try {
          await logoutRequest(tokens.access, tokens.refresh);
        } catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401) throw error;
          tokens = await refreshTokens(tokens.refresh);
          await saveTokens(tokens);
          await logoutRequest(tokens.access, tokens.refresh);
        }
      }
    } finally {
      await clearTokens();
      setUser(null);
    }
  }, []);

  const clearLocalSession = useCallback(async () => {
    await clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isReady, signIn, signOut, clearLocalSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth doit être utilisé dans AuthProvider.');
  return context;
}
