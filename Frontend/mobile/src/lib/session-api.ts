import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export type AuthUser = { public_id: string; email: string; nom_complet: string; role: 'ADMIN' | 'VENDEUR' | string; is_active: boolean; is_staff: boolean };
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type Produit = { public_id: string; nomProduit: string; prixVente: string; prixAchat?: string; seuilAlerte: number; photo: string; isActif: boolean; idCategorie: string | null; idFournisseur: string | null };
export type Categorie = { public_id: string; nomCategorie: string };
export type Fournisseur = { public_id: string; nomFournisseur: string };
export type Client = { public_id: string; nomClient: string; contact: string; adresse: string };
export type Commande = { public_id: string; client: string; date: string; statut: string; lignes: { product: string; quantite: number; prixUnitaire: string; coutUnitaire?: string }[] };
export type Stock = { public_id: string; nomProduit: string; stock: number; seuilAlerte: number };
export type Movement = { public_id: string; produit: string; typeMouvement: string; quantite: number; date: string };
export type Delivery = { public_id: string; commande: string; dateLivraison: string | null; statut: string; cout: string; fraisFacture: string };
export type Expense = { public_id: string; date: string; libelle: string; montant: string };

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); this.name = 'ApiError'; }
}

const COOKIE_KEY = 'flowstock.session.cookies';
const getBase = () => {
  const value = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');
  if (!value) throw new Error('Configurez EXPO_PUBLIC_API_URL avec l’adresse de l’API FlowStock.');
  return value;
};
export const getApiBaseUrl = getBase;
let csrf = '';
let cookie = '';
let cookieLoaded = false;
let cookieLoadPromise: Promise<void> | null = null;

async function loadCookieJar() {
  if (cookieLoaded) return;
  if (!cookieLoadPromise) {
    cookieLoadPromise = (async () => {
      if (Platform.OS === 'web') {
        if (typeof window !== 'undefined') cookie = window.sessionStorage.getItem(COOKIE_KEY) || '';
        return;
      }
      cookie = await SecureStore.getItemAsync(COOKIE_KEY) || '';
      csrf = cookie.match(/(?:^|; )csrftoken=([^;]+)/)?.[1] || '';
    })().finally(() => { cookieLoaded = true; cookieLoadPromise = null; });
  }
  await cookieLoadPromise;
}

export async function getSessionCookieHeaders(): Promise<Record<string, string>> {
  await loadCookieJar();
  return cookie && Platform.OS !== 'web' ? { Cookie: cookie } : {};
}

async function saveCookieJar() {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') {
      if (cookie) window.sessionStorage.setItem(COOKIE_KEY, cookie);
      else window.sessionStorage.removeItem(COOKIE_KEY);
    }
    return;
  }
  if (cookie) await SecureStore.setItemAsync(COOKIE_KEY, cookie);
  else await SecureStore.deleteItemAsync(COOKIE_KEY);
}

async function capture(response: Response) {
  if (Platform.OS === 'web') {
    const value = typeof document === 'undefined' ? '' : document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)?.[1] || '';
    if (value) csrf = decodeURIComponent(value);
    return;
  }
  const header = response.headers.get('set-cookie') || '';
  const pairs = header.split(/,(?=\s*[^;,=\s]+=)/).map((item) => item.split(';')[0].trim()).filter(Boolean);
  const jar = new Map(cookie.split(';').map((item) => item.trim().split('=').slice(0, 2) as [string, string]).filter(([key]) => key));
  for (const pair of pairs) {
    const separator = pair.indexOf('=');
    if (separator < 0) continue;
    const key = pair.slice(0, separator).trim();
    const value = pair.slice(separator + 1).trim();
    if (value) jar.set(key, value);
    else jar.delete(key);
  }
  cookie = [...jar].map(([key, value]) => `${key}=${value}`).join('; ');
  csrf = jar.get('csrftoken') || csrf;
  await saveCookieJar();
}

async function loadCsrf() {
  await loadCookieJar();
  const origin = getBase().replace(/\/api\/v1\/?$/, '');
  const headers: Record<string, string> = {};
  if (cookie && Platform.OS !== 'web') headers.Cookie = cookie;
  const response = await fetch(`${origin}/admin/login/`, { credentials: 'include', headers });
  const html = await response.text();
  await capture(response);
  const token = html.match(/name=["']csrfmiddlewaretoken["']\s+value=["']([^"']+)/i)
    || html.match(/value=["']([^"']+)["']\s+name=["']csrfmiddlewaretoken["']/i);
  if (token?.[1]) csrf = token[1];
}

function getErrorMessage(payload: unknown, status: number) {
  if (!payload || typeof payload !== 'object') return `La demande a échoué (${status}).`;
  const body = payload as Record<string, unknown>;
  if (typeof body.detail === 'string') return body.detail;
  const messages = Object.values(body).flatMap((value) => Array.isArray(value) ? value : [value]).filter((value): value is string => typeof value === 'string');
  return messages.join(' ') || `La demande a échoué (${status}).`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  await loadCookieJar();
  const method = (init.method || 'GET').toUpperCase();
  const write = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  if (write && !csrf) await loadCsrf();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };
  if (write && csrf) headers['X-CSRFToken'] = csrf;
  if (cookie && Platform.OS !== 'web') headers.Cookie = cookie;
  const url = `${getBase()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { ...init, method, headers, credentials: 'include' });
  } catch {
    throw new Error(`Impossible de joindre l’API FlowStock (${url}). Vérifiez EXPO_PUBLIC_API_URL et le serveur Django.`);
  }
  await capture(response);
  if (response.status === 204) return undefined as T;
  const isJson = (response.headers.get('content-type') || '').includes('json');
  const payload: unknown = isJson ? await response.json().catch(() => null) : null;
  if (!response.ok) throw new ApiError(getErrorMessage(payload, response.status), response.status);
  return payload as T;
}

export const login = (email: string, password: string) => request<AuthUser>('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
export const signup = (email: string, nom_complet: string, password: string) => request<AuthUser>('/auth/signup/', { method: 'POST', body: JSON.stringify({ email, nom_complet, password }) });
export const getMyProfile = () => request<AuthUser>('/auth/me/');
export const updateMyProfile = (fields: Partial<Pick<AuthUser, 'nom_complet'>>) => request<AuthUser>('/auth/me/', { method: 'PATCH', body: JSON.stringify(fields) });
export async function logout() {
  try { await request<void>('/auth/logout/', { method: 'POST' }); }
  finally { cookie = ''; csrf = ''; cookieLoaded = true; await saveCookieJar(); }
}
export const requestPasswordReset = (email: string) => request<{ detail: string }>('/auth/password/reset/request/', { method: 'POST', body: JSON.stringify({ email }) });
export const confirmPasswordReset = (uid: string, token: string, new_password: string) => request<{ detail: string }>('/auth/password/reset/confirm/', { method: 'POST', body: JSON.stringify({ uid, token, new_password }) });
export const changeMyPassword = (old_password: string, new_password: string) => request<{ detail: string }>('/auth/password/change/', { method: 'POST', body: JSON.stringify({ old_password, new_password }) });

function query(params?: Record<string, string | number | boolean | undefined>) {
  const pairs = Object.entries(params || {}).filter(([, value]) => value !== undefined).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  return pairs.length ? `?${pairs.join('&')}` : '';
}
export const api = {
  get: <T>(path: string, params?: Record<string, string | number | boolean | undefined>) => request<T>(`${path}${query(params)}`),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
};
