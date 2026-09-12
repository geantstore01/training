"use client";
import {useState} from "react";
import {useApi,PageTitle,Loading,ErrorBox} from "./common";
import {Button} from "./ui/button";
import {Card} from "./ui/card";
import {LessonReader} from "./lesson-reader";
import type {Lesson,LessonSummary} from "@/lib/contracts";
export function CourseAdmin(){const courses=useApi<LessonSummary[]>("content/contents?status=approved&kind=lesson&limit=100"),[selected,setSelected]=useState<LessonSummary|null>(null),[query,setQuery]=useState("");const lesson=useApi<Lesson>(selected?`content/contents/${selected.id}/versions/${selected.version}`:null);return <><PageTitle eyebrow="BoostClasse · Administration" title="Les cours de ton site">Les leçons publiées sont accessibles aux élèves dans leur carnet.</PageTitle>{selected?<Card><Button variant="outline" onClick={()=>setSelected(null)}>Revenir aux cours</Button><h2>{selected.title}</h2>{lesson.loading?<Loading/>:lesson.error?<ErrorBox message={lesson.error}/>:lesson.data&&<LessonReader key={selected.id} lesson={lesson.data}/>}</Card>:<><label htmlFor="course-search">Chercher un cours</label><input id="course-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex. attribut, fractions…"/>{courses.loading?<Loading/>:courses.error?<ErrorBox message={courses.error}/>:<div className="mission-grid">{courses.data?.filter(c=>c.title.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr'))).map(c=><Card key={c.id}><h2>{c.title}</h2><Button onClick={()=>setSelected(c)}>Lire le cours</Button></Card>)}</div>}</>}</>;}
