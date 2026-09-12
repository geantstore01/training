"use client";
import {useState} from "react";
import type {Lesson} from "@/lib/contracts";
import {Button} from "./ui/button";
import {HistoryExplorer} from "./history-explorer";
import {ScienceLab} from "./science-lab";

export function LessonReader({lesson}:{lesson:Lesson}) {
  const [index,setIndex]=useState(0);
  const course=lesson.body.cm2;
  if(!course)return <div className="lesson-text">{lesson.body.blocks.filter(b=>b.kind!=="activity").map((b,i)=><p key={i} className={b.kind==="example"?"example":""}>{b.text}</p>)}</div>;
  const paras=(s:string)=>s.split(/\n+/).filter(Boolean);
  const pages=[
    {title:"Ce que tu dois déjà savoir",lines:course.prerequisites},
    {title:"Découverte avec un exemple concret",lines:paras(course.discovery)},
    {title:"Explication simple",lines:paras(course.explanation)},
    {title:"Méthode en étapes",lines:course.method},
    {title:"Exemple résolu",lines:course.worked_example},
    {title:"Erreurs fréquentes",lines:course.common_errors},
  ];
  const page=pages[index];
  return <section className="lesson-text" aria-label="Leçon étape par étape">
    {course.history&&<HistoryExplorer chapter={course.history}/>}
    {course.science&&<ScienceLab chapter={course.science}/>}
    <p><strong>Objectif :</strong> {course.objective}</p>
    <p className="hint-text">Une idée à la fois · {index+1} sur {pages.length}</p>
    <div aria-live="polite"><h3>{page.title}</h3>{page.lines.map((line,i)=><p key={i} className={index===4?"example":""}>{index===3?`${i+1}. `:""}{line}</p>)}</div>
    <div><Button variant="outline" disabled={index===0} onClick={()=>setIndex(i=>i-1)}>Revenir</Button>{index<pages.length-1&&<Button onClick={()=>setIndex(i=>i+1)}>{index===3?"Voir l’exemple résolu":"Continuer la découverte"}</Button>}</div>
  </section>;
}
