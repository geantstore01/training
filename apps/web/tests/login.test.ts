import {beforeEach,expect,it,vi} from "vitest";
const mocks=vi.hoisted(()=>({upstream:vi.fn(),newSession:vi.fn(),sameOrigin:vi.fn(),sidCookie:vi.fn(),del:vi.fn()}));
vi.mock("../src/lib/session",()=>({...mocks,authenticated:vi.fn(),cache:async()=>({del:mocks.del}),cookieName:"edu_session",cookieOptions:{httpOnly:true,sameSite:"strict",path:"/"}}));
import {POST} from "../src/app/api/session/route";
const school="301b04d4-d1ef-4912-8959-5fbe65bbbf2e";
const response=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status});
const request=(data:unknown={level:"CM2",login:"eleve1",password:"a-valid-password"})=>new Request("http://localhost/api/session",{method:"POST",body:JSON.stringify(data)});
beforeEach(()=>{
 vi.resetAllMocks();process.env.LOGIN_SCHOOL_ID=school;mocks.sameOrigin.mockReturnValue(true);mocks.newSession.mockResolvedValue("a".repeat(64));
 mocks.upstream.mockImplementation(async(service:string,path:string)=>{
  if(path==="login")return response({access_token:"private-token",refresh_token:"private-refresh",expires_in:300});
  if(path==="me")return response({school_id:school,roles:["student"],student_id:"student-1"});
  if(path==="students/student-1")return response({level:"CM2"});
  return response({});
 });
});
it("connecte CM2 à son profil sans exposer les jetons ni demander un établissement",async()=>{
 const r=await POST(request());expect(r.status).toBe(200);expect(await r.json()).toEqual({ok:true,redirect:"/eleve"});
 expect(r.headers.get("set-cookie")).toContain("HttpOnly");
 expect(JSON.parse(mocks.upstream.mock.calls[0][3].body)).toEqual({school_id:school,login:"eleve1",password:"a-valid-password"});
});
it("refuse une autre classe et révoque la session intermédiaire",async()=>{
 const r=await POST(request({level:"CP",login:"eleve1",password:"a-valid-password"}));expect(r.status).toBe(403);
 expect(mocks.newSession).not.toHaveBeenCalled();expect(mocks.upstream).toHaveBeenCalledWith("auth","logout","private-token",{method:"POST"});
});
it("refuse de remplacer l’établissement depuis le navigateur",async()=>{
 expect((await POST(request({level:"CM2",login:"eleve1",password:"pass",school_id:school}))).status).toBe(422);expect(mocks.upstream).not.toHaveBeenCalled();
});
it("refuse un niveau inconnu",async()=>{expect((await POST(request({level:"6e",login:"eleve1",password:"pass"}))).status).toBe(422);});
it("conserve la protection contre les requêtes d’un autre site",async()=>{mocks.sameOrigin.mockReturnValue(false);expect((await POST(request())).status).toBe(403);});
it("refuse un mot de passe invalide sans créer de session web",async()=>{
 mocks.upstream.mockResolvedValue(response({},401));expect((await POST(request())).status).toBe(401);expect(mocks.newSession).not.toHaveBeenCalled();
});
it("dirige l’administrateur vers son espace sans lui attribuer un profil élève",async()=>{
 mocks.upstream.mockImplementation(async(_service:string,path:string)=>path==="login"?response({access_token:"token",refresh_token:"refresh",expires_in:300}):response({school_id:school,roles:["school_admin"],student_id:null}));
 expect(await (await POST(request())).json()).toEqual({ok:true,redirect:"/administration"});
});
it("échoue proprement si l’établissement serveur n’est pas configuré",async()=>{delete process.env.LOGIN_SCHOOL_ID;expect((await POST(request())).status).toBe(503);expect(mocks.upstream).not.toHaveBeenCalled();});
it("ne crée pas de session si le profil est indisponible",async()=>{mocks.upstream.mockImplementation(async(_s:string,p:string)=>p==="login"?response({access_token:"token",refresh_token:"refresh",expires_in:300}):response({},503));expect((await POST(request())).status).toBe(503);expect(mocks.newSession).not.toHaveBeenCalled();});
