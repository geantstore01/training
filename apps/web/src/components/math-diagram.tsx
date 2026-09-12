import type {CSSProperties} from "react";
export type MathVisual={kind:"fraction";parts:number;selected:number}|{kind:"grid";rows:number;columns:number};
export function MathDiagram({visual}:{visual:MathVisual}){
  if(visual.kind==="fraction")return <figure className="math-diagram"><div className="math-band" role="img" aria-label={`${visual.selected} parts colorées sur ${visual.parts} parts égales ; la bande entière représente une unité.`} style={{gridTemplateColumns:`repeat(${visual.parts},1fr)`}}>{Array.from({length:visual.parts},(_,i)=><span key={i} className={i<visual.selected?"filled":""}/>)}</div><figcaption>La bande entière représente 1 unité. Les parts sont égales.</figcaption></figure>;
  return <figure className="math-diagram"><div className="math-grid" role="img" aria-label={`Rectangle de ${visual.rows} rangées et ${visual.columns} colonnes ; chaque carré a un côté de 1 cm.`} style={{"--columns":visual.columns} as CSSProperties}>{Array.from({length:visual.rows*visual.columns},(_,i)=><span key={i}/>)}</div><figcaption>{visual.columns} colonnes × {visual.rows} rangées · Un carreau mesure 1 cm de côté.</figcaption></figure>;
}
