import "server-only";
import { allowedOrigin } from "./origin";
import { createClient } from "redis";
import { readFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import { z } from "zod";
export const cookieName = "edu_session";
const ttl = 604800;
const pairSchema = z.object({access_token:z.string(),refresh_token:z.string(),expires_in:z.number()});
type Stored = z.infer<typeof pairSchema> & { expiresAt: number; absoluteExpiry: number };
let connection: ReturnType<typeof createClient> | undefined;
let connecting: Promise<unknown> | undefined;
export async function cache() {
  if (!connection) { connection = createClient({url:process.env.REDIS_URL || "redis://redis:6379", username:"edu_web", password:readFileSync(/*turbopackIgnore: true*/ process.env.REDIS_PASSWORD_FILE || "/run/secrets/redis_web","utf8").trim(), socket:{connectTimeout:5000}}); connection.on("error",()=>{}); }
  if (!connection.isOpen) { connecting ??= connection.connect().finally(()=>{connecting=undefined;}); await connecting; }
  return connection;
}
export async function upstream(service: string, path: string, token?: string, options: RequestInit = {}) {
  const base = process.env.BACKEND_BASE; // DÃ©rogation rÃ©servÃ©e au serveur de recette.
  const url = base ? `${base}/services/${service}-service/${path}` : `http://${service}-service:8000/${path}`;
  return fetch(url,{...options, cache:"no-store", signal:AbortSignal.timeout(service==="tutor"?65000:20000), headers:{"Content-Type":"application/json", ...(token?{Authorization:`Bearer ${token}`}:{})}});
}
export async function newSession(value: unknown) {
  const pair = pairSchema.parse(value), sid=randomBytes(32).toString("hex");
  await (await cache()).set(`edu:web:${sid}`,JSON.stringify({...pair,expiresAt:Date.now()+pair.expires_in*1000,absoluteExpiry:Date.now()+ttl*1000}),{EX:ttl});
  return sid;
}
export async function sidCookie() { const sid=(await cookies()).get(cookieName)?.value; return sid && /^[a-f0-9]{64}$/.test(sid)?sid:null; }
export async function tokenFor(sid: string): Promise<string|null> {
  const r=await cache(), key=`edu:web:${sid}`;
  for (let attempt=0;attempt<100;attempt++) {
    const raw=await r.get(key); if(!raw) return null;
    const stored=JSON.parse(raw) as Stored;
    if(stored.absoluteExpiry<=Date.now()) {await r.del(key);return null;}
    if(stored.expiresAt>Date.now()+30000) return stored.access_token;
    const lock=randomBytes(16).toString("hex"), lockKey=`${key}:lock`;
    if(await r.set(lockKey,lock,{NX:true,PX:30000})) {
      try {
        const latest=await r.get(key); if(!latest)return null;
        const current=JSON.parse(latest) as Stored;
        if(current.expiresAt>Date.now()+30000)return current.access_token;
        const response=await upstream("auth","refresh",undefined,{method:"POST",body:JSON.stringify({refresh_token:current.refresh_token})});
        if(!response.ok) {if(response.status<500)await r.del(key);return null;}
        const pair=pairSchema.parse(await response.json());
        // Une dÃ©connexion concurrente ne doit pas recrÃ©er la session.
        await r.set(key,JSON.stringify({...pair,absoluteExpiry:current.absoluteExpiry,expiresAt:Date.now()+pair.expires_in*1000}),{XX:true,EX:Math.max(1,Math.floor((current.absoluteExpiry-Date.now())/1000))});
        return pair.access_token;
      } finally { await r.eval("if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0",{keys:[lockKey],arguments:[lock]}); }
    }
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  throw new Error("session_busy");
}
export async function authenticated() { const sid=await sidCookie();return sid?tokenFor(sid):null; }
export function sameOrigin(request: Request) {
  return allowedOrigin(request,process.env.WEB_ORIGINS||"http://localhost:3000,http://127.0.0.1:3000");
}
export const cookieOptions={httpOnly:true,sameSite:"strict" as const,secure:process.env.COOKIE_SECURE!=="false",path:"/",maxAge:ttl};
