"use client";
import {useState} from "react";
import {useApi,ErrorBox,Loading} from "./common";
import {HistoryExplorer} from "./history-explorer";
import type {HistoryChapter} from "@/lib/history";
type Draft={chapter:string;title:string;discovery:string;explanation:string;history:HistoryChapter;tasks:{question:string;options:{id:string;label:string}[];rule:{expected:string|string[];solution_steps:string[]}}[]};
export function HistoryEditorial(){
  const [opened,setOpened]=useState(false),[chosen,setChosen]=useState("ferry"),data=useApi<{courses:Draft[]}>(opened?"content/history/review-catalogue":null);
  const course=data.data?.courses.find(c=>c.chapter===chosen);
  return <section className="card" style={{marginBottom:24}}><button className="history-read" onClick={()=>setOpened(v=>!v)}>{opened?"Fermer":"Relire les nouveaux dossiers d’histoire"}</button>{opened&&<><h2>Dossiers d’histoire à valider</h2><p>Ces propositions sont des brouillons. La consultation ne vaut pas validation. Les contenus sensibles restent réservés à la relecture adulte avant publication par le circuit éditorial.</p>{data.loading?<Loading/>:data.error?<ErrorBox message={data.error} retry={data.reload}/>:<><label htmlFor="history-editorial-chapter">Chapitre à relire</label><select id="history-editorial-chapter" value={chosen} onChange={e=>setChosen(e.target.value)}>{data.data?.courses.map(c=><option key={c.chapter} value={c.chapter}>{c.title}</option>)}</select>{course&&<div key={course.chapter}><h3>{course.title}</h3><p>{course.discovery}</p><p>{course.explanation}</p><HistoryExplorer chapter={course.history}/><h3>Exercices et corrections — relecture adulte</h3>{course.tasks.map((task,i)=><details key={i}><summary>{i+1}. {task.question}</summary><ul>{task.options.map(o=><li key={o.id}>{o.label}</li>)}</ul>{task.rule.solution_steps.map((step,j)=><p key={j}>{step}</p>)}</details>)}</div>}</>}</>}</section>;
}
