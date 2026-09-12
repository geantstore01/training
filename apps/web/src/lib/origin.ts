// Liste explicite : ne jamais faire confiance au Host ou au X-Forwarded-Host reçu.
export function allowedOrigin(request:Request, origins:string) {
  const allowed=origins.split(",").map(value=>value.trim()).filter(Boolean);
  return allowed.includes(request.headers.get("origin")||"") && request.headers.get("sec-fetch-site")!=="cross-site";
}
