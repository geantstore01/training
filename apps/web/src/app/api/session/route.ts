import { NextResponse } from "next/server";
import { authenticated, cache, cookieName, cookieOptions, newSession, sameOrigin, sidCookie, upstream } from "@/lib/session";
import { z } from "zod";
import { home } from "@/lib/access";
import type { Account } from "@/lib/contracts";
export const dynamic="force-dynamic";
const json=(body:unknown,status=200)=>NextResponse.json(body,{status,headers:{"Cache-Control":"no-store"}});
export async function GET() { try {const token=await authenticated();if(!token)return json({detail:"Connecte-toi pour continuer."},401);const r=await upstream("user","me",token);return json(await r.json(),r.status);}catch{return json({detail:"La connexion au service est interrompue."},503);} }
export async function POST(request:Request) {
  if(!sameOrigin(request))return json({detail:"Origine interdite."},403);
  try {
    if(Number(request.headers.get("content-length")||0)>4096)return json({detail:"Requête trop longue."},413);
    const body=z.object({level:z.enum(["CP","CE1","CE2","CM1","CM2"]),login:z.string().trim().toLowerCase().min(3).max(64),password:z.string().min(1).max(128)}).strict().parse(await request.json());
    // Le site détermine son établissement côté serveur ; le navigateur ne le choisit pas.
    const school=z.string().uuid().safeParse(process.env.LOGIN_SCHOOL_ID);
    if(!school.success)return json({detail:"La connexion doit être configurée par l’administrateur."},503);
    const r=await upstream("auth","login",undefined,{method:"POST",body:JSON.stringify({school_id:school.data,login:body.login,password:body.password})});
    if(!r.ok)return json({detail:r.status===429?"Trop de tentatives. Attends un instant.":"Vérifie l’identifiant et le mot de passe."},r.status);
    const pair=z.object({access_token:z.string(),refresh_token:z.string(),expires_in:z.number()}).parse(await r.json());
    let account:Account;
    try {
      const me=await upstream("user","me",pair.access_token);
      if(!me.ok)throw new Error("profile_unavailable");
      account=await me.json();
      if(account.school_id!==school.data)throw new Error("profile_school_mismatch");
      if(account.roles.includes("student")) {
        if(!account.student_id)throw new Error("student_profile_missing");
        const student=await upstream("user",`students/${account.student_id}`,pair.access_token);
        if(!student.ok)throw new Error("student_profile_unavailable");
        if((await student.json()).level!==body.level) {
          await upstream("auth","logout",pair.access_token,{method:"POST"});
          return json({detail:"La classe choisie ne correspond pas à ton profil. Vérifie ta sélection."},403);
        }
      }
    } catch(error) {
      await upstream("auth","logout",pair.access_token,{method:"POST"}).catch(()=>{});
      throw error;
    }
    const old=await sidCookie();if(old)await (await cache()).del(`edu:web:${old}`);
    const sid=await newSession(pair);const response=json({ok:true,redirect:home(account.roles)});response.cookies.set(cookieName,sid,cookieOptions);return response;
  } catch(e) {return json({detail:e instanceof z.ZodError?"Renseigne les trois champs de connexion.":"Le service de connexion est indisponible."},e instanceof z.ZodError?422:503);}
}
export async function DELETE(request:Request) {
  if(!sameOrigin(request))return json({detail:"Origine interdite."},403);
  try {const sid=await sidCookie();if(sid){const token=await authenticated();await (await cache()).del(`edu:web:${sid}`);if(token)await upstream("auth","logout",token,{method:"POST"});}}catch{/* Cookie effacé même si le serveur est momentanément indisponible. */}
  const response=json({ok:true});response.cookies.set(cookieName,"",{...cookieOptions,maxAge:0});return response;
}
