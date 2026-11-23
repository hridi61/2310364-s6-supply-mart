import type { TokenResponse, User } from "../types";

// Vite dev server /api কে backend-এ (port 8000) পাঠায়; Vercel-এও একই origin
export const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  fields: Record<string, string>;

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

export function messageOf(err: unknown): string {
  return err instanceof ApiError ? err.message : "কিছু একটা সমস্যা হয়েছে, আবার চেষ্টা করুন";
}

// ---- access token শুধু মেমোরিতে (localStorage-এ না), তাই XSS-এ চুরি করা কঠিন ----
let accessToken: string | null = null;

interface Handlers {
  onRefreshed: (user: User) => void; // চুপচাপ refresh হলে UI-র user আপডেট
  onLost: () => void; // session শেষ বা ban: UI লগআউট হবে
}
let handlers: Handlers = { onRefreshed: () => {}, onLost: () => {} };

export function setSessionHandlers(h: Handlers): void {
  handlers = h;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

// সার্ভারের এরর body থেকে বার্তা আর কোন ঘরে ভুল সেটা বের করে
async function toApiError(res: Response): Promise<ApiError> {
  let message = `অনুরোধ ব্যর্থ হয়েছে (${res.status})`;
  const fields: Record<string, string> = {};
  try {
    const data = await res.json();
    const detail = data?.detail;
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      for (const item of detail) {
        const loc: unknown[] = item.loc ?? [];
        const field = String(loc[loc.length - 1] ?? "");
        if (field) fields[field] = String(item.msg);
      }
      message = "ইনপুটে ভুল আছে, লাল চিহ্নিত ঘরগুলো দেখুন";
    }
  } catch {
    // body JSON না হলে ডিফল্ট বার্তাই থাকবে
  }
  return new ApiError(res.status, message, fields);
}

// ---- refresh: একসাথে অনেক কল এলেও একটাই চলে (নইলে refresh token ঘুরে গিয়ে গোলমাল হয়) ----
let refreshing: Promise<TokenResponse | null> | null = null;

export function refreshSession(): Promise<TokenResponse | null> {
  refreshing ??= (async () => {
    try {
      const res = await fetch(`${BASE}/auth/refresh`, { method: "POST", credentials: "same-origin" });
      if (!res.ok) return null;
      const data: TokenResponse = await res.json();
      accessToken = data.access_token;
      return data;
    } catch {
      return null;
    }
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(`${BASE}${path}`, { ...init, headers, credentials: "same-origin" });
}

export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  let res: Response;
  try {
    res = await send(path, init);
    // token-এর মেয়াদ শেষ (401) হলে একবার refresh করে একই অনুরোধ আবার পাঠাই
    if (res.status === 401 && !path.startsWith("/auth/")) {
      const renewed = await refreshSession();
      if (renewed) {
        handlers.onRefreshed(renewed.user);
        res = await send(path, init);
      } else {
        accessToken = null;
        handlers.onLost();
      }
    }
  } catch {
    throw new ApiError(0, "সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না। ব্যাকএন্ড চালু আছে কিনা দেখুন");
  }
  if (!res.ok) {
    const err = await toApiError(res);
    if (err.status === 403 && err.message === "Account banned") {
      accessToken = null;
      handlers.onLost(); // অ্যাডমিন ban করলে সাথে সাথে লগআউট
    }
    throw err;
  }
  return res;
}

export async function json<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await request(path, init);
  return res.json();
}

export function body(data: unknown): string {
  return JSON.stringify(data);
}

export function query(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") sp.set(key, String(value));
  }
  const text = sp.toString();
  return text ? `?${text}` : "";
}

export async function paged<T>(path: string): Promise<{ items: T[]; total: number }> {
  const res = await request(path);
  const items: T[] = await res.json();
  return { items, total: Number(res.headers.get("X-Total-Count") ?? items.length) };
}
