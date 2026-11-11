// REST client. Errors carry the backend's message so the UI can say what went wrong.
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init.headers ?? {}) } });
  } catch {
    throw new ApiError(0, "The RELAY backend is not reachable.");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail ?? msg; } catch { /* not json */ }
    throw new ApiError(res.status, String(msg));
  }
  return res.json() as Promise<T>;
}

export type Health = {
  status: string; database: string; database_ok: boolean; mock_mode: boolean; llm: string; embeddings: string;
  sms_provider: string; ws_clients: number; agents: string[];
};
