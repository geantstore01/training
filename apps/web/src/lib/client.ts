export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/${path}`, { ...options, credentials: "same-origin", cache: "no-store", headers: { "Content-Type": "application/json", ...options.headers } });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail = body && typeof body === "object" && "detail" in body && typeof body.detail === "string" ? body.detail : "Le service ne répond pas. Réessaie dans un instant.";
    if (response.status === 401 && path !== "session") window.location.assign("/connexion");
    throw new ApiError(response.status, detail);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}
export function write<T>(path: string, body: unknown, method = "POST") { return api<T>(path, { method, body: JSON.stringify(body) }); }
export function errorText(e: unknown) { return e instanceof Error ? e.message : "Une erreur empêche cette action."; }
