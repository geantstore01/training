import { redirect } from "next/navigation";
import { authenticated, upstream } from "@/lib/session";
import { Shell } from "@/components/shell";
import type {Account} from "@/lib/contracts";
export const dynamic="force-dynamic";
export default async function Layout({children}:{children:React.ReactNode}){const token=await authenticated();if(!token)redirect("/connexion");const r=await upstream("user","me",token);if(!r.ok)redirect("/connexion");return <Shell account={await r.json() as Account}>{children}</Shell>;}
