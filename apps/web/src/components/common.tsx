"use client";
import { useEffect, useState } from "react";
import { ArrowRight, Compass, RefreshCw } from "lucide-react";
import { Button } from "./ui/button";
import { api, errorText } from "@/lib/client";
export function useApi<T>(path:string|null) {
  const [data,setData]=useState<T|null>(null),[error,setError]=useState(""),[loading,setLoading]=useState(true),[version,setVersion]=useState(0);
  useEffect(()=>{let alive=true;setData(null);setError("");setLoading(true);if(!path){setLoading(false);return;}api<T>(path).then(v=>{if(alive)setData(v);}).catch(e=>{if(alive)setError(errorText(e));}).finally(()=>{if(alive)setLoading(false);});return()=>{alive=false;};},[path,version]);
  return {data,error,loading,reload:()=>setVersion(v=>v+1)};
}
export function ErrorBox({message,retry}:{message:string;retry?:()=>void}) {return <div role="alert" className="error-box"><strong>Une étape à reprendre</strong><p>{message}</p>{retry&&<Button variant="outline" onClick={retry}><RefreshCw size={18}/> Réessayer</Button>}</div>;}
export function Empty({title,children}:{title:string;children:React.ReactNode}) {return <div className="empty"><Compass size={40} aria-hidden="true"/><h2>{title}</h2><div>{children}</div></div>;}
export function Loading(){return <p role="status" className="loading">Un instant, on prépare ton espace…</p>;}
export function PageTitle({eyebrow,title,children}:{eyebrow:string;title:string;children?:React.ReactNode}) {return <header className="page-title"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children&&<p className="lede">{children}</p>}</header>;}
export function NextIcon(){return <ArrowRight size={19} aria-hidden="true"/>;}
