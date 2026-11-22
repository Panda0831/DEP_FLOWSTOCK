import * as SecureStore from 'expo-secure-store';

import type { AuthTokens } from './api';

const SESSION_KEY = 'flowstock.auth.tokens';

export async function readTokens(): Promise<AuthTokens | null> {
  const serialized = await SecureStore.getItemAsync(SESSION_KEY);
  if (!serialized) return null;
  try {
    const value = JSON.parse(serialized) as AuthTokens;
    return value.access && value.refresh ? value : null;
  } catch {
    return null;
  }
}

export function saveTokens(tokens: AuthTokens) {
  return SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(tokens));
}

export function clearTokens() {
  return SecureStore.deleteItemAsync(SESSION_KEY);
}
