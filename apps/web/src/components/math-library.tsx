"use client";
import {useState,type ReactNode} from "react";
import {Search,Shapes,Calculator,Ruler,ChartColumn,Lightbulb,Hash,BarChart3} from "lucide-react";
import type {Competency,CourseProgress} from "@/lib/contracts";
import {useApi} from "./common";
import {SubjectBanner} from "./subject-banner";
import "./math-workshop.css";

const domains=[
 {id:"nombres",title:"Nombres",verb:"Compare et partage",icon:Hash,codes:["ENTIERS","COMPARER-ENTIERS","DECIMAUX","FRACTIONS","FRACTION-QUANTITE","FRACTIONS-DECIMALES","RANGER-DECIMAUX"]},
 {id:"calculs",title:"Calculs",verb:"Trouve ta méthode",icon:Calculator,codes:["ADDITION-SOUSTRACTION","SOUSTRACTION","MULTIPLICATION","DIVISION","CALCUL-MENTAL","ESTIMATION"]},
 {id:"mesures",title:"Mesures",verb:"Mesure le quotidien",icon:Ruler,codes:["LONGUEURS","MASSES-CAPACITES","CONTENANCES","DUREES","PERIMETRE","AIRE","RECTANGLES-COMPARER"]},
 {id:"geometrie",title:"Géométrie",verb:"Observe et construis",icon:Shapes,codes:["FIGURES","CONSTRUCTIONS","SYMETRIE","ANGLES","REPERAGE"]},
 {id:"donnees",title:"Données",verb:"Fais parler les nombres",icon:ChartColumn,codes:["TABLEAUX","GRAPHIQUES","DONNEES-COMPARER"]},
 {id:"problemes",title:"Problèmes",verb:"Mène ton raisonnement",icon:Lightbulb,codes:["PROBLEMES","PROPORTION","MONNAIE","PARTAGES"]},
];
const fold=(s:string)=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const domainOf=(c:Competency)=>domains.find(d=>d.codes.includes(c.code.replace("CM2-MATH-","")));

const statusLabel=(row:CourseProgress)=>row.status==="passed"?`PASSED${row.note!==null?` · ${row.note}/20`:""}`:row.status==="à_revoir"?`À revoir${row.note!==null?` · ${row.note}/20`:""}`:row.status==="à_relire"?"À relire":row.status==="en_cours"?"En cours":"À commencer";

export function MathLibrary({topics,studentId,refreshKey=0,renderStart}:{topics:Competency[];studentId?:string;refreshKey?:number;renderStart:(topic:Competency)=>ReactNode}){
 const [domain,setDomain]=useState("all"),[query,setQuery]=useState("");
 const progress=useApi<CourseProgress[]>(studentId?`assessment/students/${studentId}/course-progress?subject=mathematiques&cards=${refreshKey}`:null);
 const progressByCompetency=new Map((progress.data??[]).map(row=>[row.competency_id,row]));
 const filtered=topics.filter(t=>(domain==="all"||domainOf(t)?.id===domain)&&fold(t.label+" "+t.description+" "+t.objectives.join(" ")).includes(fold(query)));
 return <div className="french-workshop math-workshop">
 <SubjectBanner subject="mathematiques"/>

 <section aria-labelledby="math-domains"><div className="atelier-section-title"><div><p className="atelier-kicker">Choisis ton terrain de découverte</p><h2 id="math-domains">Six façons de raisonner</h2></div><button className="text-link" aria-pressed={domain==="all"} onClick={()=>{setDomain("all");setQuery("");}}>Tout explorer</button></div><div className="atelier-domains">{domains.map(d=>{const Icon=d.icon;return <button key={d.id} className={`atelier-domain math-domain-${d.id} ${domain===d.id?"active":""}`} aria-pressed={domain===d.id} onClick={()=>setDomain(d.id)}><span className="domain-symbol"><Icon size={26}/></span><strong>{d.title}</strong><span>{d.verb}</span><small>{topics.filter(t=>domainOf(t)?.id===d.id).length} leçons</small></button>;})}</div></section>
 <section className="atelier-catalogue" aria-labelledby="math-courses"><div className="atelier-section-title"><div><p className="atelier-kicker">Une situation, une méthode, des essais</p><h2 id="math-courses">{domains.find(d=>d.id===domain)?.title??"Ton carnet de mathématiques"}</h2></div><label className="atelier-search"><Search size={20}/><span className="sr-only">Rechercher une leçon de mathématiques</span><input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Fractions, monnaie, durées…"/></label></div><p className="catalogue-count" aria-live="polite">{filtered.length} leçons disponibles{query?` pour « ${query} »`:""}</p>{filtered.length?<div className="atelier-lessons">{filtered.map(topic=>{const d=domainOf(topic),Icon=d?.icon??Calculator,row=progressByCompetency.get(topic.id);return <article key={topic.id} className={`topic-card atelier-lesson math-domain-${d?.id??"nombres"}`}><div className="lesson-heading"><span className="lesson-stamp"><Icon size={24}/></span><span>{d?.title??"Mathématiques"}</span></div><h3>{topic.label}</h3><p>{topic.description}</p>{row&&<div className="lesson-progress"><div><BarChart3 size={16}/><strong>{statusLabel(row)}</strong><span>{row.progress_percent}%</span></div><span className="lesson-progress-track"><i style={{width:`${row.progress_percent}%`}}/></span></div>}<div className="lesson-route"><span>Observer</span><span>Essayer</span><span>Expliquer</span></div>{renderStart(topic)}</article>;})}</div>:<div className="atelier-empty"><Search size={30}/><h3>Aucune leçon avec ces mots.</h3><p>Essaie « fraction », « mesure » ou un autre domaine.</p><button className="text-link" onClick={()=>{setDomain("all");setQuery("");}}>Retrouver toutes les leçons</button></div>}</section></div>;
}
