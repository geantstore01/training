"use client";
import {useRef,useState} from "react";
import {ArrowRight,FlaskConical,NotebookPen,RotateCcw,Check,Download,Lightbulb} from "lucide-react";
import {write,errorText} from "@/lib/client";
import type {ScienceChapter,ScienceRun} from "@/lib/science";
import {ScienceInstrument} from "./science-instrument";
import "./science-workshop.css";

export function ScienceLab({chapter,onSaved,initialRun}:{chapter:ScienceChapter;onSaved?:()=>void;initialRun?:ScienceRun}) {
  const [setting,setSetting]=useState(initialRun?.setting??chapter.settings[0].id),[hypothesis,setHypothesis]=useState(initialRun?.hypothesis??""),[conclusion,setConclusion]=useState(initialRun?.conclusion??""),[run,setRun]=useState<ScienceRun|null>(initialRun??null),[busy,setBusy]=useState(false),[error,setError]=useState(""),[hint,setHint]=useState(0),[showReference,setShowReference]=useState(false);
  const requestId=useRef<string|null>(null),heading=useRef<HTMLHeadingElement>(null);
  async function observe(){setBusy(true);setError("");try{requestId.current??=crypto.randomUUID();const result=await write<ScienceRun>("assessment/science/runs",{chapter:chapter.chapter,setting,hypothesis,request_id:requestId.current});setRun(result);onSaved?.();heading.current?.focus();}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  async function save(){if(!run)return;setBusy(true);setError("");try{setRun(await write<ScienceRun>(`assessment/science/runs/${run.id}/conclusion`,{text:conclusion}));onSaved?.();}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  function reset(){setRun(null);setHypothesis("");setConclusion("");setHint(0);setShowReference(false);setError("");requestId.current=null;}
  function download(){if(!run)return;const file=new Blob([JSON.stringify({atelier:chapter.experiment.title,source:chapter.source,hypothese:run.hypothesis,reglage:run.result.label,observation:run.result.observation,conclusion:run.conclusion,statut:"À relire avec un enseignant",modele:run.result.model_version},null,2)],{type:"application/json;charset=utf-8"});const url=URL.createObjectURL(file);const a=document.createElement("a");a.href=url;a.download=`carnet-sciences-${chapter.chapter}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  const phase=run?.completed_at?3:run?2:1;
  return <section className="science-lab" aria-label={`Laboratoire : ${chapter.experiment.title}`}>
    <div className="lab-heading"><div><span className="science-kicker"><FlaskConical size={16}/> L’EXPÉRIENCE VIRTUELLE</span><h3>{chapter.experiment.title}</h3></div><span className="lab-mode">Tout se passe à l’écran</span></div>
    <ol className="science-phases" aria-label="Démarche scientifique">{["Je prédis","J’observe","J’explique"].map((name,i)=><li key={name} className={phase===i+1?"active":phase>i+1?"complete":""} aria-current={phase===i+1?"step":undefined}><span>{phase>i+1?<Check size={14}/>:i+1}</span>{name}</li>)}</ol>
    <div className="lab-workbench"><div className="lab-instrument-panel"><div className="instrument-caption"><span>INSTRUMENT {chapter.chapter==="matiere"?"01":chapter.chapter==="digestion"?"02":chapter.chapter==="circuits"?"03":"04"}</span><span>{run?"OBSERVATION OBTENUE":"PRÊT À EXPLORER"}</span></div>
      <ScienceInstrument chapter={chapter.chapter} setting={run?.setting??(chapter.chapter==="terre"?"haut":setting)} after={run?.result.after}/>
      <label htmlFor={`setting-${chapter.chapter}`}>Le réglage à tester</label><select id={`setting-${chapter.chapter}`} value={setting} disabled={!!run||busy} onChange={e=>{setSetting(e.target.value);requestId.current=null;}}>{chapter.settings.map(s=><option value={s.id} key={s.id}>{s.label}</option>)}</select>
      <p className="instrument-limits">{run?.result.limitation??"Un modèle simplifié pour comprendre. Ta prédiction vient avant le résultat."}</p>
    </div><div className="lab-notes">
      <span className="science-kicker"><NotebookPen size={16}/> MON CARNET SCIENTIFIQUE</span>
      {!run?<><h4>Avant d’observer…</h4><label htmlFor={`hypothesis-${chapter.chapter}`}>{chapter.experiment.hypothesis}</label><p>Une hypothèse est une idée à tester. Tu as le droit de te tromper.</p><textarea id={`hypothesis-${chapter.chapter}`} rows={3} maxLength={1000} disabled={busy} value={hypothesis} placeholder="Je pense que… parce que…" onChange={e=>{setHypothesis(e.target.value);requestId.current=null;}}/><button className="science-primary" disabled={busy||hypothesis.trim().length<3} onClick={()=>void observe()}>{busy?"Observation en cours…":"Tester mon hypothèse"}<ArrowRight size={18}/></button></>:<>
        <h4 ref={heading} tabIndex={-1}>Ce que j’observe</h4><p className="lab-observation" aria-live="polite">{run.result.observation}</p>
        <details><summary>Relire mon hypothèse</summary><p>{run.hypothesis}</p></details>
        {!run.completed_at?<><label htmlFor={`conclusion-${chapter.chapter}`}>{chapter.experiment.analysis_question}</label><textarea id={`conclusion-${chapter.chapter}`} rows={3} maxLength={1000} disabled={busy} value={conclusion} placeholder="J’observe que… Cela montre que…" onChange={e=>setConclusion(e.target.value)}/>
          <div className="lab-actions"><button className="science-secondary" disabled={hint>=2} onClick={()=>setHint(h=>h+1)}><Lightbulb size={16}/>Indice {Math.min(hint+1,2)}</button><button className="science-primary" disabled={busy||conclusion.trim().length<3} onClick={()=>void save()}>{busy?"Enregistrement…":"Garder ma conclusion"}<Check size={17}/></button></div>
          {hint>0&&<p className="science-hint">{hint===1?"Relève une différence entre l’état de départ et le résultat. N’ajoute pas une mesure que tu n’as pas faite.":"Complète : « Avec ce réglage, j’observe… Mon hypothèse est confirmée ou à modifier parce que… »"}</p>}
        </>:<><p className="lab-saved"><Check size={18}/>Ton essai est dans le carnet.</p><p>{run.conclusion}</p><p>Ta justification est à relire avec ton enseignant. Aucune note automatique n’est donnée à ce texte.</p><button className="science-secondary" onClick={download}><Download size={16}/> Télécharger mon essai</button></>}
        <button className="science-text-button" onClick={()=>setShowReference(!showReference)}>{showReference?"Masquer la conclusion expliquée":"Comparer avec une conclusion expliquée"}</button>
        {showReference&&<div className="lab-reference"><strong>Conclusion du modèle</strong><p>{run.result.reference_conclusion}</p><p>Compare-la à ton explication. Les mêmes idées peuvent être formulées autrement.</p></div>}
        <button className="science-secondary" disabled={busy} onClick={reset}><RotateCcw size={16}/>Faire une autre observation</button>
        <small>{run.storage==="ephemeral_preview"?"Aperçu local : le carnet disparaît au redémarrage du serveur.":"Carnet chiffré, conservé 30 jours. Tu peux l’effacer depuis ton carnet."}</small>
      </>}{error&&<p role="alert" className="science-error">{error}</p>}
    </div></div>
    <details className="science-protocol"><summary>Matériel, protocole et précautions</summary><p><strong>Objectif :</strong> {chapter.experiment.objective}</p><p>{chapter.experiment.materials.join(" ")}</p><ol>{chapter.experiment.steps.map(s=><li key={s}>{s}</li>)}</ol>{chapter.experiment.safety_rules.map(s=><p key={s}>{s}</p>)}<p>Les résultats sont ceux du modèle affiché, pas des mesures effectuées dans ta classe.</p></details>
    <details className="science-protocol"><summary>Les mots pour comprendre</summary><dl>{chapter.vocabulary.map(w=><div key={w.word}><dt>{w.word}</dt><dd>{w.definition}</dd></div>)}</dl></details>
  </section>;
}
