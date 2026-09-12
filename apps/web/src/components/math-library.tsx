"use client";
import {useState,useEffect,type FormEvent,type ReactNode} from "react";
import {Search,Shapes,Calculator,Ruler,ChartColumn,Lightbulb,Hash,BarChart3,Trophy,Timer,ExternalLink} from "lucide-react";
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

const rand=(min:number,max:number)=>Math.floor(Math.random()*(max-min+1))+min;
type FluenceSerie={id:string;title:string;description:string;make:()=>{label:string;answer:number}};
const FLUENCE_SERIES:FluenceSerie[]=[
 {id:"tables",title:"Tables de multiplication",description:"Produits de 2 à 9",make:()=>{const a=rand(2,9),b=rand(2,9);return{label:`${a} × ${b}`,answer:a*b};}},
 {id:"trous",title:"Multiplications à trou",description:"7 × ? = 56",make:()=>{const a=rand(2,9),b=rand(2,9);return{label:`${a} × ? = ${a*b}`,answer:b};}},
 {id:"complements",title:"Compléments à 100",description:"? + 62 = 100",make:()=>{const a=rand(11,89);return{label:`? + ${a} = 100`,answer:100-a};}},
 {id:"complements-mille",title:"Compléments à 1000",description:"? + 450 = 1000",make:()=>{const a=rand(101,899);return{label:`? + ${a} = 1000`,answer:1000-a};}},
 {id:"doubles",title:"Doubles et moitiés",description:"Double de 35 · moitié de 84",make:()=>{if(Math.random()<.5){const n=rand(12,99);return{label:`Double de ${n}`,answer:n*2};}const n=rand(6,49)*2;return{label:`Moitié de ${n}`,answer:n/2};}},
 {id:"additions",title:"Additions mentales",description:"Deux nombres à deux chiffres",make:()=>{const a=rand(11,55),b=rand(11,55);return{label:`${a} + ${b}`,answer:a+b};}},
 {id:"soustractions",title:"Soustractions mentales",description:"Jusqu'à 100",make:()=>{const a=rand(30,99),b=rand(11,a-2);return{label:`${a} − ${b}`,answer:a-b};}},
 {id:"dizaines",title:"Multiplier par 10, 100",description:"13 × 100 · 25 × 10",make:()=>{const a=rand(12,89),m=Math.random()<.5?10:100;return{label:`${a} × ${m}`,answer:a*m};}},
 {id:"divisions",title:"Tables de division",description:"42 ÷ 7",make:()=>{const b=rand(2,9),q=rand(2,9);return{label:`${b*q} ÷ ${b}`,answer:q};}},
];
const FLUENCE_DURATION=60;

function FluenceLab(){
 const [serie,setSerie]=useState<FluenceSerie|null>(null);
 const [running,setRunning]=useState(false);
 const [timeLeft,setTimeLeft]=useState(FLUENCE_DURATION);
 const [question,setQuestion]=useState<{label:string;answer:number}|null>(null);
 const [value,setValue]=useState("");
 const [score,setScore]=useState(0);
 const [mistakes,setMistakes]=useState(0);
 const [flash,setFlash]=useState<{ok:boolean;expected:number}|null>(null);
 const [best,setBest]=useState<Record<string,number>>({});
 useEffect(()=>{try{setBest(JSON.parse(window.localStorage.getItem("edu-fluence-best")||"{}"));}catch{}},[]);
 const startSerie=(choice:FluenceSerie)=>{setSerie(choice);setRunning(true);setTimeLeft(FLUENCE_DURATION);setScore(0);setMistakes(0);setFlash(null);setValue("");setQuestion(choice.make());};
 useEffect(()=>{if(!running)return;const timer=window.setInterval(()=>setTimeLeft(t=>Math.max(0,t-1)),1000);return()=>window.clearInterval(timer);},[running]);
 useEffect(()=>{if(!running||timeLeft>0||!serie)return;setQuestion(null);setBest(current=>{if(score<=(current[serie.id]??0))return current;const record={...current,[serie.id]:score};try{window.localStorage.setItem("edu-fluence-best",JSON.stringify(record));}catch{}return record;});},[running,timeLeft,serie,score]);
 const submit=(event:FormEvent)=>{event.preventDefault();if(!running||!question||!serie)return;const trimmed=value.trim().replace(",",".");if(trimmed===""||!Number.isFinite(Number(trimmed)))return;const answer=Number(trimmed);if(answer===question.answer)setScore(s=>s+1);else setMistakes(m=>m+1);setFlash({ok:answer===question.answer,expected:question.answer});setValue("");setQuestion(serie.make());};
 const total=score+mistakes,precision=total?Math.round(score*100/total):0,bestScore=serie?(best[serie.id]??0):0;
 return <section className="fluence-lab" aria-labelledby="fluence-title">
  <div className="atelier-section-title"><div><p className="atelier-kicker">Calcul mental chronométré</p><h2 id="fluence-title">Fluence calculatoire</h2></div>{serie&&<button className="text-link" onClick={()=>{setSerie(null);setRunning(false);setQuestion(null);setFlash(null);}}>Choisir une autre série</button>}</div>
  {!serie&&<><p className="fluence-intro">Choisis une série et réponds à un maximum de calculs en {FLUENCE_DURATION} secondes. La réponse se valide avec la touche Entrée : pas de note, juste de l'entraînement et ton meilleur score.</p><div className="fluence-series">{FLUENCE_SERIES.map(s=>{const record=best[s.id]??0;return <button key={s.id} className="fluence-serie" onClick={()=>startSerie(s)}><strong>{s.title}</strong><span>{s.description}</span>{record>0&&<em aria-label={`Meilleur score ${record}`}><Trophy size={15}/>{record}</em>}</button>;})}</div></>}
  {serie&&running&&question&&<div className="fluence-run">
    <div className="fluence-head"><span className="fluence-timer" role="timer" aria-label={`${timeLeft} secondes restantes`}><Timer size={18}/>{timeLeft} s</span><div className="fluence-bar" aria-hidden="true"><span style={{width:`${timeLeft*100/FLUENCE_DURATION}%`}}/></div><span className="fluence-score">{score}<small> justes</small></span></div>
    <p className="fluence-question" aria-live="polite">{question.label} = ?</p>
    <form className="fluence-form" onSubmit={submit}><label htmlFor="fluence-answer" className="sr-only">Ta réponse</label><input id="fluence-answer" key={`${serie.id}-${total}`} autoFocus inputMode="numeric" autoComplete="off" value={value} onChange={e=>setValue(e.target.value)} placeholder="Ta réponse…"/><button>Valider</button></form>
    <p className={`fluence-flash ${flash?(flash.ok?"ok":"ko"):""}`} aria-live="polite">{flash?(flash.ok?`Juste ! ${score} calcul${score>1?"s":""} réussi${score>1?"s":""}.`:`La réponse était ${flash.expected}. Continue !`):"Tape ta réponse puis appuie sur Entrée."}</p>
  </div>}
  {serie&&!running&&<div className="fluence-bilan" aria-live="polite">
    <p className="fluence-bilan-title">Série terminée : {serie.title}</p>
    <div className="fluence-bilan-stats"><p><strong>{score}</strong><span>calculs justes</span></p><p><strong>{total?`${precision} %`:"—"}</strong><span>de réussite</span></p><p><strong>{bestScore}</strong><span>ton record</span></p></div>
    {score>=bestScore&&score>0?<p className="fluence-record">Nouveau record sur cette série. Bravo !</p>:<p>Rejoue la série pour battre ton record de {bestScore}.</p>}
    <div className="fluence-bilan-actions"><button className="text-link" aria-pressed="true" onClick={()=>startSerie(serie)}>Rejouer cette série</button><button className="text-link" onClick={()=>{setSerie(null);setFlash(null);}}>Choisir une autre série</button></div>
  </div>}
  <p className="fluence-links">Pour aller plus loin, les outils libres et gratuits de la coopérative CoopMaths (MathAléa) : <a href="https://fluence.mathalea.fr/" target="_blank" rel="noreferrer">Fluence <ExternalLink size={14}/></a> · <a href="https://www.coopmaths.fr/mathalea.html" target="_blank" rel="noreferrer">Exercices MathAléa <ExternalLink size={14}/></a></p>
 </section>;
}

export function MathLibrary({topics,studentId,refreshKey=0,renderStart}:{topics:Competency[];studentId?:string;refreshKey?:number;renderStart:(topic:Competency)=>ReactNode}){
 const [domain,setDomain]=useState("all"),[query,setQuery]=useState("");
 const progress=useApi<CourseProgress[]>(studentId?`assessment/students/${studentId}/course-progress?subject=mathematiques&cards=${refreshKey}`:null);
 const progressByCompetency=new Map((progress.data??[]).map(row=>[row.competency_id,row]));
 const filtered=topics.filter(t=>(domain==="all"||domainOf(t)?.id===domain)&&fold(t.label+" "+t.description+" "+t.objectives.join(" ")).includes(fold(query)));
 return <div className="french-workshop math-workshop">
 <SubjectBanner subject="mathematiques"/>
 <FluenceLab/>
 <section aria-labelledby="math-domains"><div className="atelier-section-title"><div><p className="atelier-kicker">Choisis ton terrain de découverte</p><h2 id="math-domains">Six façons de raisonner</h2></div><button className="text-link" aria-pressed={domain==="all"} onClick={()=>{setDomain("all");setQuery("");}}>Tout explorer</button></div><div className="atelier-domains">{domains.map(d=>{const Icon=d.icon;return <button key={d.id} className={`atelier-domain math-domain-${d.id} ${domain===d.id?"active":""}`} aria-pressed={domain===d.id} onClick={()=>setDomain(d.id)}><span className="domain-symbol"><Icon size={26}/></span><strong>{d.title}</strong><span>{d.verb}</span><small>{topics.filter(t=>domainOf(t)?.id===d.id).length} leçons</small></button>;})}</div></section>
 <section className="atelier-catalogue" aria-labelledby="math-courses"><div className="atelier-section-title"><div><p className="atelier-kicker">Une situation, une méthode, des essais</p><h2 id="math-courses">{domains.find(d=>d.id===domain)?.title??"Ton carnet de mathématiques"}</h2></div><label className="atelier-search"><Search size={20}/><span className="sr-only">Rechercher une leçon de mathématiques</span><input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Fractions, monnaie, durées…"/></label></div><p className="catalogue-count" aria-live="polite">{filtered.length} leçons disponibles{query?` pour « ${query} »`:""}</p>{filtered.length?<div className="atelier-lessons">{filtered.map(topic=>{const d=domainOf(topic),Icon=d?.icon??Calculator,row=progressByCompetency.get(topic.id);return <article key={topic.id} className={`topic-card atelier-lesson math-domain-${d?.id??"nombres"}`}><div className="lesson-heading"><span className="lesson-stamp"><Icon size={24}/></span><span>{d?.title??"Mathématiques"}</span></div><h3>{topic.label}</h3><p>{topic.description}</p>{row&&<div className="lesson-progress"><div><BarChart3 size={16}/><strong>{statusLabel(row)}</strong><span>{row.progress_percent}%</span></div><span className="lesson-progress-track"><i style={{width:`${row.progress_percent}%`}}/></span></div>}<div className="lesson-route"><span>Observer</span><span>Essayer</span><span>Expliquer</span></div>{renderStart(topic)}</article>;})}</div>:<div className="atelier-empty"><Search size={30}/><h3>Aucune leçon avec ces mots.</h3><p>Essaie « fraction », « mesure » ou un autre domaine.</p><button className="text-link" onClick={()=>{setDomain("all");setQuery("");}}>Retrouver toutes les leçons</button></div>}</section></div>;
}
