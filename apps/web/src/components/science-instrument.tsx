import type {ChapterKey} from "@/lib/science";

/** Conceptual diagrams only. Accessible text carries every observation outside SVG. */
export function ScienceInstrument({chapter,setting,after}:{chapter:ChapterKey;setting:string;after?:string}) {
  const lit=after==="on";
  return <svg className={`science-instrument instrument-${chapter}`} viewBox="0 0 520 320" role="img" aria-label={chapter==="circuits"?`Circuit à une boucle. ${after?lit?"Lampe allumée.":"Lampe éteinte.":"Prépare ton hypothèse avant d’observer."}`:chapter==="matiere"?`Modèle de l’eau. ${after?`État observé : ${after}.`:"Observation à lancer."}`:chapter==="digestion"?"Schéma simplifié du trajet digestif, de la bouche à l’intestin grêle.":"Bâton et ombre sous une source lumineuse. Schéma sans échelle."}>
    <defs><pattern id={`grid-${chapter}`} width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="currentColor" opacity=".08"/></pattern><radialGradient id="lampGlow"><stop stopColor="#ffd17a" stopOpacity=".45"/><stop offset="1" stopColor="#ffd17a" stopOpacity="0"/></radialGradient></defs>
    <rect width="520" height="320" rx="20" fill={`url(#grid-${chapter})`}/>
    {chapter==="circuits"?<g><path d="M100 90H235 M285 90H420V230H117 M83 230H100V90" fill="none" stroke={lit?"#ffd17a":"#7595b9"} strokeWidth="5" strokeLinecap="round"/>
      <circle cx="235" cy="90" r="6" fill="#64e3f4"/><circle cx="285" cy="90" r="6" fill="#64e3f4"/>
      <path d={setting==="ouvert"?"M235 90L279 60":"M235 90H285"} stroke="#64e3f4" strokeWidth="6" strokeLinecap="round"/>
      {setting==="debranche"&&<><path d="M352 230H388" stroke="#10264a" strokeWidth="10"/><path d="M345 230L375 211" stroke="#7595b9" strokeWidth="5"/></>}
      <path d="M83 211V249 M117 217V243" stroke="#64e3f4" strokeWidth="7"/><text x="75" y="278">PILE</text><text x="194" y="42">INTERRUPTEUR</text>
      {lit&&<circle cx="420" cy="160" r="100" fill="url(#lampGlow)"/>}<circle cx="420" cy="160" r="34" fill={lit?"#ffd17a":"#10264a"} stroke={lit?"#ffd17a":"#7595b9"} strokeWidth="4"/><path d="M402 143L438 177M438 143L402 177" stroke={lit?"#10264a":"#7595b9"} strokeWidth="4"/>
      <text x="380" y="280">LAMPE</text><text x="200" y="168" className="instrument-result">{after?lit?"ALLUMÉE":"ÉTEINTE":"À TESTER"}</text>
    </g>:chapter==="matiere"?<g>
      <path d="M160 72V255Q160 270 175 270H345Q360 270 360 255V72" stroke="#a9c8e6" strokeWidth="4" fill="none"/>
      <path d="M155 72H190M330 72H365" stroke="#a9c8e6" strokeWidth="5"/>
      {after==="liquide"||(!after&&setting!=="fondre")?<path d="M165 198Q210 185 260 198T355 198V254Q355 265 342 265H178Q165 265 165 254Z" fill="#64e3f4" opacity=".8"/>:after==="gazeux"?<g><path d="M165 245H355V258Q355 265 345 265H175Q165 265 165 258Z" fill="#64e3f4"/><text x="173" y="155">GAZ INVISIBLE</text><text x="168" y="180" className="instrument-note">dans l’air autour du verre</text></g>:<g transform="translate(212 169) rotate(-9 47 47)"><rect width="94" height="83" rx="14" fill="#a4f0fa" fillOpacity=".8" stroke="#d7fbff" strokeWidth="3"/><path d="M16 17H61M16 17V50" fill="none" stroke="#fff" strokeWidth="5"/></g>}
      <text x="165" y="306">{after?`ÉTAT ${after.toLocaleUpperCase("fr")}`:"EAU · MODÈLE VIRTUEL"}</text>
    </g>:chapter==="digestion"?<g>
      <path d="M220 34Q258 15 291 40L282 79L251 91V145Q320 117 330 156Q345 196 296 210H241Q218 209 218 230H312Q334 234 311 253H240Q213 257 233 278H285" fill="none" stroke="#9cb3cd" strokeWidth="18" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M220 47H264" stroke={setting==="bouche"?"#ffd17a":"#64e3f4"} strokeWidth="10"/>
      <circle cx={setting==="bouche"?241:setting==="estomac"?301:271} cy={setting==="bouche"?47:setting==="estomac"?170:246} r="27" fill="#ffd17a" opacity={after?".7":".2"}/>
      <path d="M160 47H210M260 111H363M345 172H390M120 252H208" stroke="#64e3f4" strokeWidth="2"/>
      <text x="76" y="52">BOUCHE</text><text x="368" y="115">ŒSOPHAGE</text><text x="390" y="197">ESTOMAC</text><text x="18" y="241">INTESTIN GRÊLE</text>
      {after==="nutriments"&&<g><path d="M313 246H378" stroke="#ffd17a" strokeWidth="3" strokeDasharray="5 6"/><text x="370" y="272">VERS LE SANG</text></g>}
    </g>:<g>
      <path d="M70 252H460" stroke="#9cb3cd" strokeWidth="3"/><path d={`M260 253H${setting==="haut"?315:430}`} stroke="#030f24" strokeWidth="10" strokeLinecap="round"/>
      <path d="M260 251V159" stroke="#a4f0fa" strokeWidth="8"/>
      <circle cx={setting==="haut"?196:81} cy={setting==="haut"?35:107} r="25" fill="#ffd17a"/>
      <path d={setting==="haut"?"M196 35L315 253":"M81 107L430 253"} stroke="#ffd17a" strokeWidth="2" strokeDasharray="6 7"/>
      <text x="223" y="144">BÂTON</text><text x="300" y="282">OMBRE</text><text x="28" y={setting==="haut"?35:62}>LUMIÈRE</text>
    </g>}
  </svg>;
}
