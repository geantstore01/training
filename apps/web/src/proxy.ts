import {NextRequest,NextResponse} from "next/server";
// Le site public passe par Cloudflare puis un tunnel http : CF-Visitor est le seul
// témoin fiable du schéma réel du visiteur (X-Forwarded-Proto est écrasé en http par le proxy interne).
const secureHosts=new Set(["boostclasse.com","www.boostclasse.com"]);
function visitorIsHttps(request:NextRequest){return (request.headers.get("cf-visitor")||"").includes("\"https\"")||request.nextUrl.protocol==="https:";}
export function proxy(request:NextRequest){
  const host=(request.headers.get("x-forwarded-host")||request.headers.get("host")||"").toLowerCase().split(":")[0];
  if(secureHosts.has(host)&&!visitorIsHttps(request))return NextResponse.redirect(new URL(`https://${host}${request.nextUrl.pathname}${request.nextUrl.search}`),308);
  const nonce=btoa(crypto.randomUUID());
  const csp=`default-src 'self'; script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${process.env.NODE_ENV==='development'?" 'unsafe-eval'":""}; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`;
  const headers=new Headers(request.headers);headers.set("x-nonce",nonce);headers.set("Content-Security-Policy",csp);
  const response=NextResponse.next({request:{headers}});response.headers.set("Content-Security-Policy",csp);response.headers.set("Cache-Control","no-store");
  if(secureHosts.has(host))response.headers.set("Strict-Transport-Security","max-age=31536000");return response;
}
export const config={matcher:["/((?!_next/static|_next/image|favicon.ico|api/health).*)"]};
