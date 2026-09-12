import { redirect } from "next/navigation";
import { authenticated, upstream } from "@/lib/session";
import { home } from "@/lib/access";
import { Landing } from "@/components/landing";
import type {Account} from "@/lib/contracts";
export const dynamic="force-dynamic";
export default async function Page(){const token=await authenticated();if(!token)return <Landing/>;const r=await upstream("user","me",token);if(!r.ok)redirect("/connexion");const account=await r.json() as Account;redirect(home(account.roles));}
