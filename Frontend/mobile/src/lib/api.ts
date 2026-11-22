export type AuthTokens = {
  access: string;
  refresh: string;
};

export type AuthUser = {
  uuid: string;
  email: string;
  nom: string;
  prenom: string;
  role: string;
  doit_changer_mot_de_passe: boolean;
};

export type LoginResponse = AuthTokens & { utilisateur: AuthUser };

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function getApiBaseUrl() {
  const baseUrl = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');
  if (!baseUrl) {
    throw new Error('Configurez EXPO_PUBLIC_API_URL avec l’adresse de l’API StockFlow.');
  }
  return baseUrl;
}

function getErrorMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== 'object') return fallback;
  const body = payload as Record<string, unknown>;
  const nested = body.details ?? body.erreurs;
  if (nested && typeof nested === 'object') {
    const messages = Object.values(nested as Record<string, unknown>)
      .flatMap((value) => (Array.isArray(value) ? value : [value]))
      .filter((value): value is string => typeof value === 'string');
    if (messages.length) return messages.join(' ');
  }
  const detail = body.detail ?? body.message;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.filter((item) => typeof item === 'string').join(' ');
  if (detail && typeof detail === 'object') {
    const messages = Object.values(detail as Record<string, unknown>)
      .flatMap((value) => (Array.isArray(value) ? value : [value]))
      .filter((value): value is string => typeof value === 'string');
    if (messages.length) return messages.join(' ');
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...init.headers,
      },
    });
  } catch {
    throw new Error(`Impossible de joindre l’API StockFlow (${url}). Vérifiez son adresse et qu’elle est démarrée.`);
  }

  if (response.status === 204) return undefined as T;
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new ApiError(getErrorMessage(payload, 'La demande a échoué. Réessayez.'), response.status);
  }
  return payload as T;
}

export function login(email: string, password: string) {
  return request<LoginResponse>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  });
}

export function getMyProfile(accessToken: string) {
  return request<AuthUser>('/auth/me/', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function refreshTokens(refreshToken: string) {
  return request<AuthTokens>('/auth/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });
}

export function logout(accessToken: string, refreshToken: string) {
  return request<void>('/auth/logout/', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ refresh: refreshToken }),
  });
}

export function requestPasswordReset(email: string) {
  return request<{ detail: string }>('/auth/password/reset/request/', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(
  uid: string,
  token: string,
  newPassword: string,
  confirmation: string,
) {
  return request<{ detail: string }>('/auth/password/reset/confirm/', {
    method: 'POST',
    body: JSON.stringify({
      uid,
      token,
      nouveau_mot_de_passe: newPassword,
      confirmation_nouveau_mot_de_passe: confirmation,
    }),
  });
}

export function changeMyPassword(
  accessToken: string,
  currentPassword: string,
  newPassword: string,
  confirmation: string,
) {
  return request<{ detail: string }>('/auth/password/change/', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({
      ancien_mot_de_passe: currentPassword,
      nouveau_mot_de_passe: newPassword,
      confirmation_nouveau_mot_de_passe: confirmation,
    }),
  });
}
