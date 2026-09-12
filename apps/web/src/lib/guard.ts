import { redirect } from "next/navigation";
import { authenticated,upstream } from "./session";
import { mayEnter } from "./access";
import type { Account } from "./contracts";
export async function guard(area:string) {const token=await authenticated();if(!token)redirect("/connexion");const r=await upstream("user","me",token);if(!r.ok)redirect("/connexion");const a=await r.json() as Account;if(!mayEnter(a.roles,area))redirect("/acces-interdit");return a;}
