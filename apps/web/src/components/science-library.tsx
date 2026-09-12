"use client";
import {useState,type ReactNode} from "react";
import {ArrowDown,Atom,Orbit,Zap,Droplets,BookOpen,ExternalLink,Trash2,NotebookPen} from "lucide-react";
import type {Competency} from "@/lib/contracts";
import type {ChapterKey,ScienceChapter,ScienceRun} from "@/lib/science";
import {useApi,ErrorBox,Loading} from "./common";
import {api,errorText} from "@/lib/client";
import {ScienceLab} from "./science-lab";
import {SubjectBanner} from "./subject-banner";
import "./science-workshop.css";

const labels:Record<ChapterKey,{name:string;tag:string;description:string;icon:typeof Atom}>={
  matiere:{name:"Métamorphoses de l’eau",tag:"MATIÈRE",description:"La glace fond. L’eau disparaît-elle vraiment ?",icon:Droplets},
  digestion:{name:"À l’intérieur du vivant",tag:"LE CORPS HUMAIN",description:"Suis les aliments, de la bouche aux nutriments.",icon:Atom},
  circuits:{name:"Que la lumière soit !",tag:"OBJETS & ÉNERGIE",description:"Une pile, une lampe. À toi de comprendre la boucle.",icon:Zap},
  terre:{name:"Notre planète sous la lumière",tag:"TERRE & ESPACE",description:"Observe les ombres et questionne les saisons.",icon:Orbit},
};

export function ScienceLibrary({topics,renderStart,studentId}:{topics:Competency[];renderStart:(topic:Competency)=>ReactNode;studentId?:string}) {
  const catalogue=useApi<ScienceChapter[]>("assessment/science/catalogue"),[selected,setSelected]=useState<ChapterKey>("circuits"),[filter,setFilter]=useState("tous"),[resume,setResume]=useState<ScienceRun|undefined>(),[revision,setRevision]=useState(0);
  const chapters=catalogue.data??[],current=chapters.find(c=>c.chapter===selected),topic=topics.find(t=>t.code===current?.code);
  return <div className="science-station">
    <SubjectBanner subject="sciences"/>
    <section id="science-missions" className="science-missions"><div className="science-section-heading"><div><span className="science-kicker">CHOISIS UNE QUESTION À EXPLORER</span><h2>Quatre portes sur le monde.</h2></div><label>Mon domaine<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="tous">Tous les domaines</option>{Object.entries(labels).map(([key,value])=><option key={key} value={key}>{value.tag}</option>)}</select></label></div>
    {catalogue.loading?<Loading/>:catalogue.error?<ErrorBox message={catalogue.error} retry={catalogue.reload}/>:<div className="science-mission-grid">{chapters.filter(c=>filter==="tous"||filter===c.chapter).map((c)=>{const info=labels[c.chapter],Icon=info.icon;return <button key={c.chapter} className={`science-mission ${selected===c.chapter?"selected":""}`} aria-pressed={selected===c.chapter} onClick={()=>{setSelected(c.chapter);setResume(undefined);document.getElementById("science-active")?.scrollIntoView({behavior:"instant",block:"start"});}}><span className="science-card-top"><Icon size={27}/><span>{String(chapters.indexOf(c)+1).padStart(2,"0")}</span></span><span className="science-kicker">{info.tag}</span><strong>{info.name}</strong><span>{info.description}</span><span className="science-mission-footer">{selected===c.chapter?"Laboratoire ouvert":"Ouvrir le laboratoire"}<ArrowDown size={17}/></span></button>;})}</div>}</section>
    {current&&<div id="science-active" className="science-active"><ScienceLab key={current.chapter+(resume?.id??"")} chapter={current} initialRun={resume?.chapter===current.chapter?resume:undefined} onSaved={()=>setRevision(r=>r+1)}/><div className="science-after-lab"><section><BookOpen size={24}/><div><h3>Comprendre, puis s’entraîner</h3><p>{current.objective}</p>{topic?renderStart(topic):<p>La leçon est en préparation dans ton école. Le laboratoire reste disponible.</p>}</div></section><section><div><h3>D’où vient ce cours ?</h3><p>Leçon originale fondée sur le programme de 2023, applicable au CM2 en 2026–2027.</p><a href={`${current.source.pdf_url}#page=${current.source.page}`} target="_blank" rel="noopener noreferrer">Programme · annexe page {current.source.page}<ExternalLink size={15}/></a><p className="science-source-detail">{current.source.section}</p>{selected==="circuits"&&<a href="https://phet.colorado.edu/sims/html/circuit-construction-kit-dc/latest/circuit-construction-kit-dc_all.html?locale=fr" target="_blank" rel="noopener noreferrer">Explorer aussi avec PhET · site externe<ExternalLink size={15}/></a>}</div></section></div></div>}
    {studentId&&<ScienceNotebook key={revision} studentId={studentId} onResume={row=>{setSelected(row.chapter);setResume(row);document.getElementById("science-active")?.scrollIntoView({block:"start"});}}/>}
  </div>;
}

export function ScienceNotebook({studentId,readOnly=false,onResume}:{studentId:string;readOnly?:boolean;onResume?:(row:ScienceRun)=>void}) {
  const notebook=useApi<ScienceRun[]>(`assessment/science/notebook/${studentId}`),[error,setError]=useState("");
  async function erase(){try{await api(`assessment/science/notebook/${studentId}`,{method:"DELETE"});notebook.reload();}catch(e){setError(errorText(e));}}
  return <section className="science-notebook"><div className="science-section-heading"><h3><NotebookPen size={22}/>{readOnly?"Carnet scientifique de l’élève":"Mon carnet d’observations"}</h3><button className="science-secondary" onClick={notebook.reload}>Actualiser le carnet</button></div><p>Les conclusions sont des essais à discuter. Elles ne donnent pas automatiquement un niveau de maîtrise.</p>{notebook.error?<ErrorBox message={notebook.error} retry={notebook.reload}/>:notebook.data?.length?<>{notebook.data.map(row=><details key={row.id}><summary>{labels[row.chapter].tag} · {row.result.label} · {row.completed_at?"Conclusion écrite":"À poursuivre"}</summary><p><strong>Hypothèse :</strong> {row.hypothesis}</p><p><strong>Observation :</strong> {row.result.observation}</p><p><strong>Conclusion :</strong> {row.conclusion||"Pas encore écrite."}</p>{onResume&&<button className="science-secondary" onClick={()=>onResume(row)}>{row.completed_at?"Relire cet essai":"Reprendre cet essai"}</button>}</details>)}{!readOnly&&<button className="science-text-button" onClick={()=>void erase()}><Trash2 size={15}/>Effacer mon carnet</button>}</>:<p>Les observations apparaîtront ici après un premier essai.</p>}{error&&<p role="alert">{error}</p>}</section>;
}
