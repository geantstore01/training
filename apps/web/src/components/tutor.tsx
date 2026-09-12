"use client";
import {useEffect,useState,useRef} from "react";
import {Send,Volume2} from "lucide-react";
import {Button} from "./ui/button";
import {ErrorBox} from "./common";
import {write,errorText} from "@/lib/client";
import type {TutorTurn} from "@/lib/contracts";
export function Speak({exerciseId}:{exerciseId:string}) {
  const [busy,setBusy]=useState(false),[playing,setPlaying]=useState(false),[error,setError]=useState(""),audio=useRef<HTMLAudioElement|null>(null),url=useRef<string|null>(null);
  function dispose(){setPlaying(false);audio.current?.pause();if(url.current)URL.revokeObjectURL(url.current);url.current=null;}
  useEffect(()=>()=>dispose(),[]);
  return <div><Button type="button" variant="outline" disabled={busy} onClick={async()=>{setBusy(true);setError("");dispose();try{const r=await fetch("/api/speech/synthesize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({exercise_version_id:exerciseId})});if(!r.ok){const b=await r.json();throw new Error(b.detail||"La lecture audio est indisponible.");}url.current=URL.createObjectURL(await r.blob());audio.current=new Audio(url.current);audio.current.onended=dispose;await audio.current.play();setPlaying(true);}catch(e){setError(errorText(e));}finally{setBusy(false);}}}><Volume2 size={18}/>{busy?"Préparation…":"Écouter la consigne"}</Button>{playing&&<Button type="button" variant="ghost" onClick={dispose}>Arrêter la lecture</Button>}{error&&<p role="alert" className="hint-text">{error}</p>}</div>;
}
export function CaptainAvatar() {
  return <span className="captain captain-avatar"><img src="/captain-avatar.png" alt="Capitaine Savoir, ton capitaine guide" width={96} height={96} decoding="async"/></span>;
}
export function Tutor({attemptId,disabled,autoHelp=false}:{attemptId:string;disabled:boolean;autoHelp?:boolean}) {
  const [turns,setTurns]=useState<TutorTurn[]>([]),[message,setMessage]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  useEffect(()=>{setTurns([]);setError("");setMessage("");},[attemptId]);
  const pending=useRef<{signature:string;key:string}|null>(null);
  const autoSent=useRef<string|null>(null);
  async function send(plus=false, explicitMessage?:string){const text=plus?"Peux-tu me donner un indice supplémentaire ?":(explicitMessage??message);if(!text.trim())return;setBusy(true);setError("");try{const signature=JSON.stringify([attemptId,text,plus]);if(pending.current?.signature!==signature)pending.current={signature,key:crypto.randomUUID()};const turn=await write<TutorTurn>("tutor/turns",{attempt_id:attemptId,request_id:pending.current.key,message:text,plus_aide:plus});pending.current=null;setTurns(t=>[...t,turn]);setMessage("");}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  useEffect(()=>{if(autoHelp&&autoSent.current!==attemptId){autoSent.current=attemptId;void send(false,"Je viens de me tromper. Aide-moi à comprendre ma démarche, sans me donner la réponse.");}},[attemptId,autoHelp]);
  return <aside className="tutor-panel" aria-label="Capitaine Savoir"><div className="tutor-heading"><span className="captain-wrap"><CaptainAvatar/><span className="genie-bubble">Une difficulté ? Questionne-moi !</span></span><div><h2>Capitaine Savoir</h2><p>{autoHelp?"On reprend ton raisonnement ensemble.":"On cherche ensemble."}</p></div></div><div className="tutor-messages" role="log" aria-live="polite" aria-relevant="additions"><p className="bubble">{autoHelp?"Ton résultat ne définit pas ce que tu sais. Regardons la méthode, étape par étape.":"Je peux t’aider à comprendre la méthode. Qu’est-ce qui te pose question ?"}</p>{turns.map((t,i)=><div key={i} className="bubble"><span className="eyebrow">{t.safety_status==="safe"?`Aide ${t.niveau_aide} sur ${t.aide_max??6}`:"Un point à vérifier"}</span><p>{t.message_pedagogique}</p>{t.question_suivante&&<p><strong>{t.question_suivante}</strong></p>}</div>)}</div>{error&&<ErrorBox message={error}/>}<form onSubmit={e=>{e.preventDefault();void send();}}><label htmlFor="tutor-message">Ta question</label><textarea id="tutor-message" maxLength={1000} rows={3} value={message} onChange={e=>setMessage(e.target.value)} disabled={disabled||busy} placeholder="Je ne comprends pas…"/><Button disabled={disabled||busy||!message.trim()} type="submit"><Send size={17}/>{busy?"Le capitaine réfléchit…":"Poser ma question"}</Button></form>{turns.length>0&&<Button variant="outline" disabled={disabled||busy||turns.at(-1)!.niveau_aide>=(turns.at(-1)!.aide_max??6)} onClick={()=>void send(true)}>Un peu plus d’aide</Button>}<p className="hint-text">Ne donne pas ton nom, ton adresse ou tes coordonnées. L’aide respecte les réglages de confidentialité.</p></aside>;
}
