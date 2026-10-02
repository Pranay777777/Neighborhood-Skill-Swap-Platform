// Thin client for the FastAPI backend. The access token lives in memory only; the
// refresh token is kept in localStorage so a reload stays signed in (see README limits).
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const REFRESH_KEY = 'skillswap.refresh';

let accessToken = null;

export class ApiError extends Error {
  constructor(status, detail) {
    // FastAPI sends a string, or a list of validation errors for a 422.
    const first = Array.isArray(detail) ? detail[0]?.msg : detail;
    super(typeof first === 'string' ? first : 'Please check the form and try again.');
    this.status = status;
  }
}

export const tokens = {
  set({ access_token, refresh_token }) {
    accessToken = access_token;
    try { localStorage.setItem(REFRESH_KEY, refresh_token); } catch { /* private mode */ }
  },
  clear() {
    accessToken = null;
    try { localStorage.removeItem(REFRESH_KEY); } catch { /* private mode */ }
  },
  refresh() {
    try { return localStorage.getItem(REFRESH_KEY); } catch { return null; }
  },
};

async function send(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  return fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

let refreshing = null;

// One refresh at a time: rotation means a second concurrent refresh would look like reuse.
export function refreshSession() {
  const token = tokens.refresh();
  if (!token) return Promise.resolve(false);
  refreshing ??= send('/auth/refresh', { method: 'POST', body: { refresh_token: token }, auth: false })
    .then(async (r) => {
      if (!r.ok) { tokens.clear(); return false; }
      tokens.set(await r.json());
      return true;
    })
    .finally(() => { refreshing = null; });
  return refreshing;
}

export async function api(path, options = {}) {
  let r = await send(path, options);
  if (r.status === 401 && options.auth !== false && (await refreshSession())) {
    r = await send(path, options);
  }
  if (r.status === 204) return null;
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new ApiError(r.status, data?.detail);
  return data;
}
