import { authenticated, sameOrigin, upstream } from "@/lib/session";
import { allowedPath } from "@/lib/access";
export const dynamic="force-dynamic";
async function handle(request:Request,context:{params:Promise<{service:string;path:string[]}>}) {
  const {service,path}=await context.params, joined=path.join("/");
  const fail=(detail:string,status:number)=>Response.json({detail},{status,headers:{"Cache-Control":"no-store"}});
  if(!allowedPath(service,joined,request.method))return fail("Chemin indisponible.",404);
  if(request.method!=="GET"&&!sameOrigin(request))return fail("Origine interdite.",403);
  try {
    const token=await authenticated();if(!token)return fail("Connecte-toi pour continuer.",401);
    const body=request.method==="GET"?undefined:await request.text();if(body&&body.length>32768)return fail("Requête trop longue.",413);
    const result=await upstream(service,joined+new URL(request.url).search,token,{method:request.method,body:body||undefined});
    return new Response(result.status===204?null:result.body,{status:result.status,headers:{"Content-Type":result.headers.get("Content-Type")||"application/json","Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});
  }catch{return fail("Le service ne répond pas. Réessaie dans un instant.",503);}
}
export {handle as GET,handle as POST,handle as PUT,handle as DELETE};
