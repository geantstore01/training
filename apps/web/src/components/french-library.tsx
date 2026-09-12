"use client";
import {useState,type ReactNode} from "react";
import {BarChart3,BookOpen,Search,PenLine,SpellCheck,MessagesSquare,Shapes,TimerReset} from "lucide-react";
import type {Competency,CourseProgress} from "@/lib/contracts";
import {useApi} from "./common";
import {SubjectBanner} from "./subject-banner";

const domains=[
  {id:"grammaire",title:"Grammaire",verb:"Démonte les phrases",icon:Shapes,codes:["NATURES","FONCTIONS","OBJETS","ATTRIBUT","PHRASE","CIRCONSTANCES","PRONOMS","EXPANSIONS"]},
  {id:"conjugaison",title:"Conjugaison",verb:"Fais voyager les verbes",icon:TimerReset,codes:["PRESENT","IMPARFAIT","FUTUR","PASSE-COMPOSE","PASSE-SIMPLE","PLUS-QUE-PARFAIT"]},
  {id:"orthographe",title:"Orthographe",verb:"Trouve les bons accords",icon:SpellCheck,codes:["ACCORDS","HOMOPHONES","DICTEE-RELECTURE","PARTICIPE-ETRE","ON-ONT"]},
  {id:"lexique",title:"Lexique",verb:"Joue avec le sens",icon:MessagesSquare,codes:["LEXIQUE","POLYSEMIE","SYNONYMES","ANTONYMES","DICTIONNAIRE"]},
  {id:"lecture",title:"Lecture",verb:"Mène ton enquête",icon:BookOpen,codes:["COMPREHENSION","LECTURE-ENQUETE"]},
  {id:"ecriture",title:"Écriture",verb:"Donne vie à tes idées",icon:PenLine,codes:["ECRIT-REDIGER","RESUMER"]},
];
const domainOf=(c:Competency)=>domains.find(d=>d.codes.includes(c.code.replace("CM2-FR-","")));
const fold=(s:string)=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();

const statusLabel=(row:CourseProgress)=>row.status==="passed"?`PASSED${row.note!==null?` · ${row.note}/20`:""}`:row.status==="à_revoir"?`À revoir${row.note!==null?` · ${row.note}/20`:""}`:row.status==="à_relire"?"À relire":row.status==="en_cours"?"En cours":"À commencer";

export function FrenchLibrary({topics,studentId,refreshKey=0,renderStart}:{topics:Competency[];studentId?:string;refreshKey?:number;renderStart:(topic:Competency)=>ReactNode}){
  const [domain,setDomain]=useState("all"),[query,setQuery]=useState("");
  const progress=useApi<CourseProgress[]>(studentId?`assessment/students/${studentId}/course-progress?subject=francais&cards=${refreshKey}`:null);
  const progressByCompetency=new Map((progress.data??[]).map(row=>[row.competency_id,row]));
  const courseTopics=topics.filter(topic=>domainOf(topic));
  const filtered=courseTopics.filter(t=>(domain==="all"||domainOf(t)?.id===domain)&&fold(t.label+" "+t.description+" "+t.objectives.join(" ")).includes(fold(query)));
  const chosen=domains.find(d=>d.id===domain);
  return <div className="french-workshop">
    <SubjectBanner subject="francais"/>
    <section aria-labelledby="atelier-domaines"><div className="atelier-section-title"><div><p className="atelier-kicker">Choisis ton terrain de découverte</p><h2 id="atelier-domaines">Six façons de progresser</h2></div><button className="text-link" aria-pressed={domain==="all"} onClick={()=>{setDomain("all");setQuery("");}}>Tout explorer</button></div>
      <div className="atelier-domains">{domains.map(d=>{const Icon=d.icon;const count=courseTopics.filter(t=>domainOf(t)?.id===d.id).length;return <button key={d.id} className={`atelier-domain domain-${d.id} ${domain===d.id?"active":""}`} aria-pressed={domain===d.id} onClick={()=>setDomain(d.id)}><span className="domain-symbol"><Icon size={26}/></span><strong>{d.title}</strong><span>{d.verb}</span><small>{count} leçons</small></button>;})}</div>
    </section>
    <section className="atelier-catalogue" aria-labelledby="atelier-cours"><div className="atelier-section-title"><div><p className="atelier-kicker">Une idée, une méthode, des essais</p><h2 id="atelier-cours">{chosen?chosen.title:"Ton carnet de découvertes"}</h2></div><label className="atelier-search"><Search size={20}/><span className="sr-only">Rechercher une leçon de français</span><input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Un sujet, un mot…"/></label></div><p className="catalogue-count" aria-live="polite">{filtered.length} {filtered.length===1?"leçon disponible":"leçons disponibles"}{query?` pour « ${query} »`:""}</p>
      {filtered.length?<div className="atelier-lessons">{filtered.map(topic=>{const d=domainOf(topic),Icon=d?.icon??BookOpen,row=progressByCompetency.get(topic.id);return <article key={topic.id} className={`topic-card atelier-lesson domain-${d?.id??"grammaire"}`}><div className="lesson-heading"><span className="lesson-stamp"><Icon size={24}/></span><span>{d?.title??"Français"}</span></div><h3>{topic.label}</h3><p>{topic.description}</p>{row&&<div className="lesson-progress"><div><BarChart3 size={16}/><strong>{statusLabel(row)}</strong><span>{row.progress_percent}%</span></div><span className="lesson-progress-track"><i style={{width:`${row.progress_percent}%`}}/></span></div>}<div className="lesson-route"><span>Découvrir</span><span>Essayer</span><span>Comprendre</span></div>{renderStart(topic)}</article>;})}</div>:<div className="atelier-empty"><Search size={30}/><h3>Aucune leçon avec ces mots.</h3><p>Essaie « sujet », « récit » ou un autre domaine.</p><button className="text-link" onClick={()=>{setQuery("");setDomain("all");}}>Retrouver toutes les leçons</button></div>}
    </section>
  </div>;
}
