const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

export function clearToken(): void {
  localStorage.removeItem("token");
}

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
  }
  return res;
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Credenciais invalidas");
  const data = await res.json();
  return data.access_token as string;
}

export async function getStatus(): Promise<Record<string, number | string>> {
  const res = await apiFetch("/api/status");
  if (!res.ok) throw new Error("Erro ao buscar status");
  return res.json();
}

export async function startJob(type: string): Promise<string> {
  const res = await apiFetch("/api/jobs", {
    method: "POST",
    body: JSON.stringify({ type }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error((err.detail as string) ?? "Erro ao iniciar job");
  }
  const data = await res.json();
  return data.job_id as string;
}

export function createLogSocket(jobId: string): WebSocket {
  const wsBase = (window.location.origin).replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/api/jobs/${jobId}/logs`);
}
