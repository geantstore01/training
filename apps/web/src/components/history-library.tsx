"use client";
import {useState,type ReactNode} from "react";
import {ArrowUpRight,BookOpen,Compass,Landmark,Search} from "lucide-react";
import {useApi,Loading,ErrorBox} from "./common";
import type {Competency} from "@/lib/contracts";
import type {HistoryCatalogue} from "@/lib/history";
import "./history-workshop.css";

export function HistoryLibrary({topics,renderStart,studentId}:{topics:Competency[];renderStart:(topic:Competency)=>ReactNode;studentId?:string}) {
  const catalogue=useApi<HistoryCatalogue>("assessment/history/catalogue"),[theme,setTheme]=useState("republique");
  const progress=useApi<{competency_id:string;level:string;next_review_at:string|null}[]>(studentId?`assessment/students/${studentId}/mastery`:null);
  const chapters=catalogue.data?.chapters.filter(c=>c.theme===theme)??[];
  const existing=topics.filter(t=>!catalogue.data?.chapters.some(c=>c.code===t.code));
  return <section className="history-home" aria-label="Atelier d’histoire CM2">
    <header className="history-hero"><div><p className="history-kicker"><Compass size={16}/> L’ATELIER DU TEMPS · CM2</p><h2>Le passé a des indices.<br/><em>À toi de les relier.</em></h2><p>Une date. Un lieu. Un document. Explore leur histoire et construis une réponse avec des preuves.</p><div className="history-steps"><span>01 · Observer</span><span>02 · Situer</span><span>03 · Expliquer</span></div></div>
      <div className="history-portal" aria-hidden="true"><div className="history-orbit orbit-two"/><div className="history-orbit"/><div className="history-archive"><Landmark size={58}/><span>ARCHIVES<br/>À EXPLORER</span></div><span className="history-tag tag-one">LE DOCUMENT</span><span className="history-tag tag-two">LE CONTEXTE</span><div className="history-tickline"/></div>
    </header>
    {catalogue.loading?<Loading/>:catalogue.error?<ErrorBox message={catalogue.error} retry={catalogue.reload}/>:<>
      <div className="history-section-title"><div><p className="history-kicker">TON TERRAIN D’ENQUÊTE</p><h2>Trois portes sur l’histoire</h2></div><span>Observe à ton rythme</span></div>
      <div className="history-themes">{catalogue.data?.themes.map((t,i)=><button key={t.id} aria-pressed={theme===t.id} onClick={()=>setTheme(t.id)}><span className="history-theme-number">0{i+1}</span><strong>{t.title}</strong><small>{t.subtitle}</small><ArrowUpRight size={20}/></button>)}</div>
      <div className="history-courses">{chapters.map((c,i)=>{const topic=topics.find(t=>t.code===c.code),state=progress.data?.find(p=>p.competency_id===topic?.id);return <article className="history-course" key={c.chapter}><div className={`history-cover history-cover-${c.theme}`} aria-hidden="true"><span>DOSSIER {String(i+1).padStart(2,"0")}</span>{c.chapter==="ferry"?<BookOpen size={58}/>:<Landmark size={58}/>}<div className="history-cover-lines"/></div><div className="history-course-body"><p className="history-kicker">{c.period}</p><h3>{c.title}</h3><p>{topic?.description??"Lire un document, situer les événements et justifier sa réponse."}</p><div className="history-features"><span>Frise interactive</span><span>Document sourcé</span><span>3 défis</span></div>{state&&<p className="history-progress">Mon repère : {state.level.replaceAll("_"," ")}{state.next_review_at&&new Date(state.next_review_at)<=new Date()?" · Une révision peut t’aider.":""}</p>}{topic?renderStart(topic):<p>Ce dossier est en préparation dans ton cours.</p>}</div></article>;})}</div>
      {!!existing.length&&<section><h3>Les autres cours de mon école</h3><div className="history-courses">{existing.map(topic=><article key={topic.id} className="history-course"><div className="history-course-body"><h3>{topic.label}</h3><p>{topic.description}</p>{renderStart(topic)}</div></article>)}</div></section>}
      <aside className="history-rule"><Search size={26}/><div><strong>Un historien cherche aussi ce qu’il ne sait pas.</strong><p>Un document peut nous apprendre beaucoup. Il ne prouve pas tout : nous apprendrons à reconnaître ses limites.</p></div></aside>
    </>}
  </section>;
}
