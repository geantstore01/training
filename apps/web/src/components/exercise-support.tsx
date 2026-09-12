"use client";
import {useState} from "react";
import {api,write,errorText} from "@/lib/client";
import {Button} from "./ui/button";
import {ErrorBox} from "./common";
export function ExerciseHints({attemptId,disabled=false}:{attemptId:string;disabled?:boolean}) {
  const [hints,setHints]=useState<string[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function next(){setBusy(true);setError("");try{const hint=await api<{text:string}>(`assessment/attempts/${attemptId}/hints/${hints.length+1}`);setHints(x=>[...x,hint.text]);}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  return <section aria-label="Indices progressifs">{hints.map((hint,i)=><div className="reflection" key={i}><p><strong>Indice {i+1}</strong> · {hint}</p></div>)}{hints.length<2&&<Button variant="outline" disabled={busy||disabled} onClick={()=>void next()}>Indice {hints.length+1}</Button>}{error&&<ErrorBox message={error}/>}</section>;
}
export function DetailedCorrection({attemptId,explicit=false}:{attemptId:string;explicit?:boolean}) {
  const [parts,setParts]=useState<{part_id:string;steps:string[];answer:string|null;is_example?:boolean}[]|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function show(){setBusy(true);setError("");try{setParts(await (explicit?write(`assessment/attempts/${attemptId}/correction`,{explicit:true}):api(`assessment/attempts/${attemptId}/correction`)));}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  return <section>{!parts&&<Button variant="outline" disabled={busy} onClick={()=>void show()}>{explicit?"Demander la correction":"Comprendre la correction de mon essai"}</Button>}{parts&&<div aria-live="polite"><h3>Correction détaillée</h3>{parts.map((part,i)=><div key={part.part_id}><h4>Question {i+1}{part.is_example?" · Exemple possible, à comparer avec ton texte":""}</h4><ol>{part.steps.map((step,j)=><li key={j}>{step}</li>)}</ol>{part.answer!==null&&<p><strong>{part.is_example?"Exemple":"Réponse"} : {part.answer}</strong></p>}</div>)}<p>Explique maintenant la méthode avec tes mots, puis essaie un autre exercice.</p></div>}{error&&<ErrorBox message={error}/>}</section>;
}
