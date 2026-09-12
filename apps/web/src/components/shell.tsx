"use client";
import {Brand} from "./brand";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, LogOut, BookOpen, Users, Heart, Accessibility } from "lucide-react";
import { Button } from "./ui/button";
import type { Account } from "@/lib/contracts";
import { api } from "@/lib/client";
import { mayEnter } from "@/lib/access";
import { useState } from "react";
export function Shell({account,children}:{account:Account;children:React.ReactNode}) {
  const path=usePathname(),[large,setLarge]=useState(false),[dys,setDys]=useState(false);
  const links=[{area:"eleve",label:"Mes missions",icon:BookOpen},{area:"parent",label:"Espace parent",icon:Heart},{area:"administration",label:"Les cours",icon:BookOpen}].filter(x=>mayEnter(account.roles,x.area));
  const homeHref=links[0]?`/${links[0].area}`:"/acces-interdit";
  const goHome=()=>{if(links[0]&&path.startsWith(`/${links[0].area}`))window.dispatchEvent(new Event("edu:go-home"));};
  const goArea=(area:string)=>{if(path.startsWith(`/${area}`))window.dispatchEvent(new Event("edu:go-home"));};
  const quit=async()=>{await api("session",{method:"DELETE"});window.location.assign("/connexion");};
  const missions=links.find(x=>x.area==="eleve"),extras=links.filter(x=>x.area!=="eleve");
  return <div className={`app-shell ${large?"text-large":""} ${dys?"dys-font":""}`}><a href="#contenu" className="skip-link">Aller au contenu</a><header className="masthead masthead-art">
    <img className="masthead-art-img" src="/masthead-banner.webp" alt="" aria-hidden="true" width={2172} height={312}/>
    <Link href={homeHref} className="masthead-hotspot masthead-hotspot-brand" aria-label="BoostClasse — retour à l'accueil" onClick={goHome}/>
    {missions?<Link href="/eleve" className="masthead-hotspot masthead-hotspot-missions" aria-label={missions.label} aria-current={path.startsWith("/eleve")?"page":undefined} onClick={()=>goArea("eleve")}/>:null}
    {extras.length?<nav className="masthead-extra" aria-label="Autres espaces">{extras.map(x=><Link key={x.area} href={`/${x.area}`} aria-current={path.startsWith(`/${x.area}`)?"page":undefined} onClick={()=>goArea(x.area)}>{x.label}</Link>)}</nav>:null}
    {extras.length?<nav className="masthead-art-nav" aria-label="Autres espaces">{extras.map(x=><Link key={x.area} href={`/${x.area}`} aria-current={path.startsWith(`/${x.area}`)?"page":undefined} onClick={()=>goArea(x.area)}>{x.label}</Link>)}</nav>:null}
    <button type="button" className="masthead-hotspot masthead-hotspot-quitter" aria-label="Se déconnecter" onClick={quit}/>
    <div className="masthead-compact"><Link href={homeHref} className="brand" onClick={goHome}><img className="masthead-mascot" src="/masthead-mascot.jpg" alt="" width={180} height={240}/><Brand/></Link><nav aria-label="Espaces">{links.map(x=><Link key={x.area} href={`/${x.area}`} aria-current={path.startsWith(`/${x.area}`)?"page":undefined} onClick={()=>goArea(x.area)}><x.icon size={18}/>{x.label}</Link>)}</nav><Button variant="ghost" aria-label="Se déconnecter" onClick={quit}><LogOut size={20}/><span className="desktop-label">Quitter</span></Button></div>
  </header><main id="contenu" className="main-content"><div className="page-tools"><Link href={homeHref} className="page-tool" onClick={goHome}><span className="dot"/>Mon espace personnel</Link><details className="page-tools-confort"><summary className="page-tool"><Accessibility size={16}/>Confort de lecture</summary><div className="reading-options"><label><input type="checkbox" checked={large} onChange={e=>setLarge(e.target.checked)}/> Texte agrandi</label><label><input type="checkbox" checked={dys} onChange={e=>setDys(e.target.checked)}/> Lecture aérée</label><p>Ces réglages durent pendant cette visite.</p></div></details></div>{children}</main><footer className="footer"><Compass size={16}/> Chacun son chemin, chacun son rythme.<span>Aucune course. Aucun classement.</span></footer></div>;
}
