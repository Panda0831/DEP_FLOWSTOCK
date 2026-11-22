import type { AuthTokens } from './api';

const SESSION_KEY = 'flowstock.auth.tokens';

export async function readTokens(): Promise<AuthTokens | null> {
  if (typeof window === 'undefined') return null;
  const serialized = window.sessionStorage.getItem(SESSION_KEY);
  if (!serialized) return null;
  try {
    const value = JSON.parse(serialized) as AuthTokens;
    return value.access && value.refresh ? value : null;
  } catch {
    return null;
  }
}

export async function saveTokens(tokens: AuthTokens) {
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(tokens));
  }
}

export async function clearTokens() {
  if (typeof window !== 'undefined') window.sessionStorage.removeItem(SESSION_KEY);
}
