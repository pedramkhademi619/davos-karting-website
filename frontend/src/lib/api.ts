/**
 * Browser client for the Davos API (same origin, `/api/v1`). Session cookies are httpOnly and never touched here; state
 * changes carry the CSRF token the API returned at sign-in (`X-CSRF-Token`). Error messages come from the API in Persian and
 * are safe to show as they are.
 */

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly fields: Record<string, string> = {},
  ) {
    super(message);
  }

  get isUnauthenticated(): boolean {
    return this.status === 401;
  }
}

const NETWORK_ERROR = "ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید.";
const SERVER_ERROR = "خطایی در سرور رخ داد. کمی بعد دوباره تلاش کنید.";

type Method = "GET" | "POST" | "PUT" | "DELETE";

export type RequestOptions = {
  method?: Method;
  body?: unknown;
  csrf?: string | null;
  query?: Record<string, string | number | boolean | null | undefined>;
  signal?: AbortSignal;
};

function url(path: string, query?: RequestOptions["query"]): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function toError(response: Response): Promise<ApiError> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object") {
      const record = body as Record<string, unknown>;
      const message = typeof record.message === "string" && response.status < 500 ? record.message : SERVER_ERROR;
      const code = typeof record.code === "string" ? record.code : "error";
      const fields: Record<string, string> = {};
      if (Array.isArray(record.details)) {
        for (const item of record.details) {
          if (item && typeof item.field === "string" && typeof item.message === "string") fields[item.field] = item.message;
        }
      }
      return new ApiError(message, response.status, code, fields);
    }
  } catch {
    // not JSON (e.g. an nginx error page): fall through
  }
  if (response.status === 429) return new ApiError("تعداد درخواست‌ها زیاد است. کمی صبر کنید و دوباره تلاش کنید.", 429, "rate_limited");
  return new ApiError(response.status >= 500 ? SERVER_ERROR : "درخواست انجام نشد.", response.status, "error");
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, csrf, query, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (csrf) headers["X-CSRF-Token"] = csrf;

  let response: Response;
  try {
    response = await fetch(url(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "same-origin",
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(NETWORK_ERROR, 0, "network");
  }
  if (!response.ok) throw await toError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return SERVER_ERROR;
}
