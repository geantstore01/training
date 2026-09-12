"use client";
import {useEffect,useRef,useState} from "react";
import Link from "next/link";
import "./landing.css";

/* ---------- données de la page (contenu BoostClasse, structure kresco) ---------- */
const showcaseSteps=[
  {title:"Cours",desc:"Une leçon claire pour poser les bases.",mock:"lesson"},
  {title:"Atelier",desc:"Manipule les mots dans un atelier interactif.",mock:"workshop"},
  {title:"Guide",desc:"Pose ta question au guide quand ça bloque.",mock:"guide"},
  {title:"Quiz",desc:"Vérifie tes acquis avec des questions ciblées.",mock:"quiz"},
  {title:"Résumés",desc:"Garde l’essentiel dans une fiche express.",mock:"sheet"},
  {title:"Exercices",desc:"Mets tes méthodes à l’épreuve, étape par étape.",mock:"drill"},
  {title:"Lecture",desc:"Ouvre tes leçons, surligne et garde le fil.",mock:"reader"},
  {title:"Bilan CM2",desc:"Termine le parcours avec un bilan complet.",mock:"final"},
];
const features=[
  {title:"La leçon montre le raisonnement.",text:"Schémas, exemples et vocabulaire construisent l’intuition avant de te demander de retenir une règle. Tu vois pourquoi ça marche, pas seulement comment.",chips:["Leçons CM2","Exemples guidés","Schémas","Vocabulaire"],mock:"reason"},
  {title:"Pas un seul format d’exercice.",text:"QCM, textes à trous, mots à remettre en ordre, vrai ou faux : chaque notion a son format. Tu ne t’habitues jamais à répondre sans réfléchir.",chips:["QCM","Texte à trous","Ordre des mots","Vrai / Faux"],mock:"formats",flip:true},
  {title:"L’atelier répond à chaque geste.",text:"Déplace un mot, change une phrase, observe le résultat. L’atelier d’écriture réagit à chaque geste pour que tu voies ce qui change.",chips:["Phrases à construire","Mots à déplacer","Effet immédiat"],mock:"workshop2"},
  {title:"Le guide garde la question ouverte.",text:"Quand ça bloque, il ne donne jamais la réponse : il pose la bonne question, puis offre une piste, puis une méthode. Tu trouves — et ça reste.",chips:["Indice 1 · un mot","Indice 2 · une piste","Indice 3 · une méthode","Jamais la réponse"],mock:"hints",flip:true},
  {title:"Ton parcours avance sans te perdre.",text:"Missions du jour, prochaine étape, progression : tu sais toujours où tu en es et ce qui t’attend demain.",chips:["Missions du jour","Prochaine étape","Ta progression"],mock:"trail"},
  {title:"Le bilan devient familier.",text:"Quiz, exercices et corrections te montrent précisément où ton raisonnement a bifurqué — et quoi réviser en priorité.",chips:["Format bilan","Points forts","Révisions ciblées"],mock:"report",flip:true},
];
const rythme=[
  {title:"La notion devient visible.",text:"Leçons, schémas et exemples construisent l’intuition avant de te demander de retenir une règle."},
  {title:"Tu changes, tu vois ce qui suit.",text:"Déplace un mot, règle une phrase, observe l’effet immédiat sur ta copie."},
  {title:"Le feedback arrive pendant que tu réfléchis.",text:"Quiz et corrections te montrent précisément où ton raisonnement a bifurqué."},
  {title:"Ta prochaine mission commence au bon endroit.",text:"Progression, missions et rappels gardent le fil jusqu’au CM2."},
];
const offers=[
  {name:"Découverte",tag:"Gratuit",pitch:"Explore l’espace réel et ses activités de démonstration, sans créer de compte.",feats:["Leçons en aperçu","Quiz de démonstration","Aucun compte requis"],style:"ghost"},
  {name:"Élève",tag:"Populaire 🚀",pitch:"Le socle complet pour apprendre, s’entraîner et suivre ta progression.",feats:["Leçons complètes","Exercices à indices","Quiz, ateliers et lectures","Mes missions du jour"],style:"hero"},
  {name:"Parent",tag:"Inclus",pitch:"Tout Espace élève, avec le suivi et les réglages pour la famille.",feats:["Suivi des missions","Réglages de l’aide IA","Confidentialité de l’élève"],style:"plain"},
  {name:"Enseignant",tag:"Inclus",pitch:"Tout Espace parent, avec les outils pour la classe.",feats:["Cours du programme","Missions du jour","Suivi et accompagnement"],style:"plain"},
];
const tableRows=[
  ["Leçons & chapitres","Aperçu","✓","✓","✓"],
  ["Exercices à indices","Aperçu","✓","—","✓"],
  ["Ateliers & lectures","Aperçu","✓","—","✓"],
  ["Quiz & corrections","Aperçu","✓","—","✓"],
  ["Missions du jour","—","✓","—","✓"],
  ["Suivi de progression","—","✓","✓","✓"],
  ["Réglages de l’aide IA","—","—","✓","✓"],
  ["Mes choix de confidentialité","✓","✓","✓","✓"],
];
const faq=[
  {q:"BoostClasse, c’est quoi ?",a:"L’espace d’apprentissage des élèves du CP au CM2 : leçons, exercices, quiz et ateliers en français, mathématiques, histoire et sciences."},
  {q:"Est-ce que BoostClasse remplace mes cours ?",a:"Non. BoostClasse accompagne ce que tu fais en classe : tu retrouves ton programme, tu révises à ton rythme et tu t’entraînes avec des indices."},
  {q:"L’aide IA donne-t-elle les réponses ?",a:"Jamais. Elle te guide avec des indices, un par un, pour que tu trouves la réponse toi-même. C’est la règle d’or de BoostClasse."},
  {q:"Puis-je commencer gratuitement ?",a:"Oui : l’espace de démonstration se visite sans compte. Pour ton propre parcours, ton enseignant ou l’école crée ton accès."},
  {q:"Comment mon espace est-il configuré ?",a:"Ta classe à la connexion, puis ta matière et tes missions. Tes parents ont leur espace, ton enseignant garde le cap."},
  {q:"Puis-je utiliser BoostClasse sur mon téléphone ?",a:"Oui, sur ordinateur, tablette ou téléphone. Ta progression te suit partout, au même endroit."},
  {q:"Comment puis-je contacter mon enseignant ?",a:"Depuis l’espace classe : les échanges suivent tes missions, sans jamais comparer les élèves entre eux."},
];
const builderSteps=[
  {key:"classe",label:"Ta classe",options:["CP","CE1","CE2","CM1","CM2"],continue:"Choisir la matière"},
  {key:"matiere",label:"Ta matière",options:["Français","Mathématiques","Histoire","Sciences"],continue:"Choisir le rythme"},
  {key:"rythme",label:"Ton rythme",options:["Doux · 2 missions / semaine","Régulier · 4 missions / semaine","À fond · 6 missions / semaine"],continue:"Voir ma route"},
];

/* ---------- petites briques ---------- */
function useReveal(){const ref=useRef<HTMLDivElement>(null);useEffect(()=>{const root=ref.current;if(!root)return;const items=Array.from(root.querySelectorAll("[data-reveal]"));if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){items.forEach(el=>el.classList.add("bc-on"));return;}const io=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add("bc-on");io.unobserve(e.target);}},{threshold:.12});items.forEach(el=>io.observe(el));return()=>io.disconnect();},[]);return ref;}
function InfinityCounter(){const [phase,setPhase]=useState(0);const ref=useRef<HTMLParagraphElement>(null);useEffect(()=>{const el=ref.current;if(!el)return;if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){setPhase(5);return;}let io:IntersectionObserver;const t:number[]=[];io=new IntersectionObserver(entries=>{if(!entries.some(e=>e.isIntersecting))return;io.disconnect();[700,1250,1750,2200,2650].forEach((ms,i)=>t.push(window.setTimeout(()=>setPhase(i+1),ms)));},{threshold:.6});io.observe(el);return()=>{io.disconnect();t.forEach(id=>window.clearTimeout(id));};},[]);return <p className="bc-counter" ref={ref} aria-label="Infinies façons de comprendre"><b>{["0","3","9","27","81","∞"][phase]}</b><span>façons de<br/>comprendre</span></p>;}
function GuideAvatar({size=34,flip}:{size?:number;flip?:boolean}){return <img src="/landing-mascot-head.png" alt="Ton guide BoostClasse" width={size} height={Math.round(size*232/300)} className={flip?"bc-flipx":""} style={{width:size,height:"auto"}}/>;}

/* ---------- maquettes produit (vignettes façon kresco) ---------- */
function Mock({kind}:{kind:string}){
  if(kind==="lesson")return <div className="bc-mock-body"><p className="bc-mock-tag">📘 Leçon · Les fractions</p><div className="bc-frac"><span className="bc-frac-top">3</span><span className="bc-frac-bar"/><span>4</span></div><p className="bc-frac-note">Trois parts égales sur quatre.</p><div className="bc-lesson-line w90"/><div className="bc-lesson-line w70"/><p className="bc-keep">📌 À retenir : le dénominateur compte les parts.</p></div>;
  if(kind==="workshop")return <div className="bc-mock-body"><p className="bc-mock-tag">✍️ Atelier · La phrase</p><div className="bc-tiles"><span className="bc-tile bc-tile-ok">Le</span><span className="bc-tile bc-tile-ok">chat</span><span className="bc-tile bc-tile-ok"> dort</span><span className="bc-tile bc-tile-ok">.</span><span className="bc-tile bc-tile-drag">doucement</span></div><p className="bc-mock-hint">Glisse « doucement » au bon endroit.</p></div>;
  if(kind==="guide")return <div className="bc-mock-body bc-chat"><p className="bc-msg bc-msg-student">Je bloque : les 3/4 de 20 ?</p><div className="bc-msg bc-msg-guide"><GuideAvatar/><div><p><b>Indice 2 :</b> combien de quarts dans 20 ? 🧭</p></div></div><p className="bc-msg-encourage">💡 Tu y es presque, continue !</p></div>;
  if(kind==="quiz")return <div className="bc-mock-body"><p className="bc-mock-tag">⚡ Quiz · Vocabulaire</p><p className="bc-quiz-q">Quel mot est un synonyme de « rapide » ?</p><div className="bc-quiz-opts"><span>vaste</span><span className="bc-quiz-sel">rapide comme l’éclair ✓</span><span>lent</span><span>triste</span></div></div>;
  if(kind==="sheet")return <div className="bc-mock-body"><p className="bc-mock-tag">🗂 Fiche express · Les fractions</p><ul className="bc-sheet"><li>¼ = une part sur quatre</li><li>½ = deux parts sur quatre</li><li>Comparer : même dénominateur</li></ul></div>;
  if(kind==="drill")return <div className="bc-mock-body"><p className="bc-mock-tag">🎯 Exercice guidé</p><ol className="bc-drill"><li><span>1</span>Je lis la consigne</li><li><span>2</span>J’essaie tout seul</li><li><span>3</span>Je demande un indice si besoin</li></ol></div>;
  if(kind==="reader")return <div className="bc-mock-body"><p className="bc-mock-tag">📖 Lecture · Le secret du moulin</p><p className="bc-reader">Il poussa la porte <mark>avec précaution</mark> : un bruit étrange venait de l’étage…</p><p className="bc-mock-hint">Surligné : « avec précaution » — prudence.</p></div>;
  if(kind==="final")return <div className="bc-mock-body bc-final"><p className="bc-final-score">18<span>/20</span></p><p className="bc-mock-tag">🏅 Bilan · Fractions et lecture</p><p className="bc-final-note">Points forts : comparaison, vocabulaire.<br/>À revoir : les durées.</p></div>;
  if(kind==="reason")return <div className="bc-mock-body"><p className="bc-mock-tag">Pourquoi ça marche</p><div className="bc-frac-demo"><div className="bc-frac-demo-row"><i style={{width:"75%"}}/><span>3/4 de 20 → <b>15</b></span></div><div className="bc-frac-demo-row"><i style={{width:"25%"}}/><span>1/4 de 20 → <b>5</b></span></div><div className="bc-frac-demo-row"><i style={{width:"100%"}}/><span>4/4 de 20 → <b>20</b></span></div></div></div>;
  if(kind==="formats")return <div className="bc-mock-body bc-formats"><div><p className="bc-mock-tag">QCM</p><div className="bc-quiz-opts bc-mini"><span className="bc-quiz-sel">un mot ✓</span><span>une phrase</span></div></div><div><p className="bc-mock-tag">À trous</p><p className="bc-fillin">Le chat ___ sur le toit.</p></div><div><p className="bc-mock-tag">Ordre</p><div className="bc-tiles bc-mini"><span className="bc-tile bc-tile-ok">demain</span><span className="bc-tile bc-tile-drag">ici</span></div></div></div>;
  if(kind==="workshop2")return <div className="bc-mock-body"><p className="bc-mock-tag">✍️ Atelier</p><p className="bc-workshop-before">Le chat  dort .</p><p className="bc-workshop-arrow">↓ tu déplaces « doucement »</p><p className="bc-workshop-after">Le chat dort <b>doucement</b>.</p></div>;
  if(kind==="hints")return <div className="bc-mock-body bc-chat"><div className="bc-msg bc-msg-guide"><GuideAvatar/><div><p><b>Indice 1 :</b> relis la consigne. Quel mot est important ?</p></div></div><div className="bc-msg bc-msg-guide"><GuideAvatar/><div><p><b>Indice 2 :</b> commence par compter les parts égales.</p></div></div><div className="bc-msg bc-msg-guide"><GuideAvatar/><div><p><b>Indice 3 :</b> la méthode : divise, puis multiplie. Tu y es ! 🎉</p></div></div></div>;
  if(kind==="trail")return <div className="bc-mock-body"><p className="bc-mock-tag">🗺 Ma progression</p><div className="bc-trail"><span className="bc-dot bc-dot-done">✓</span><span className="bc-dot bc-dot-done">✓</span><span className="bc-dot bc-dot-now">3</span><span className="bc-dot">4</span><span className="bc-dot">5</span></div><p className="bc-mock-hint">Prochaine étape : le quiz des fractions.</p></div>;
  if(kind==="report")return <div className="bc-mock-body"><p className="bc-mock-tag">🏅 Mon bilan</p><ul className="bc-sheet"><li>✓ Comparer des fractions</li><li>✓ Lire un texte long</li><li>↻ Revoir : les durées</li></ul><p className="bc-msg-encourage">🎯 Révision ciblée prête !</p></div>;
  return null;
}

/* ---------- carrousel produit interactif (8 étapes) ---------- */
function Showcase(){
  const [active,setActive]=useState(0),[paused,setPaused]=useState(false);
  useEffect(()=>{if(paused)return;const id=window.setInterval(()=>setActive(a=>(a+1)%showcaseSteps.length),5200);return()=>window.clearInterval(id);},[paused]);
  return <div className="bc-showcase" onMouseEnter={()=>setPaused(true)} onMouseLeave={()=>setPaused(false)}>
    <div className="bc-showcase-list" role="tablist" aria-label="Les étapes du parcours">
      {showcaseSteps.map((s,i)=><button key={s.title} role="tab" aria-selected={i===active} className={`bc-showcase-step${i===active?" bc-on":""}`} onClick={()=>setActive(i)}><span>{String(i+1).padStart(2,"0")}</span><div><strong>{s.title}</strong><small>{s.desc}</small></div></button>)}
    </div>
    <div className="bc-showcase-stage" data-reveal>
      <div className="bc-mock"><div className="bc-mock-head">{showcaseSteps[active].title}<span className="bc-live"><i/><i/><i/></span></div><Mock kind={showcaseSteps[active].mock}/></div>
      <div className="bc-showcase-dots" aria-hidden="true">{showcaseSteps.map((s,i)=><i key={s.title} className={i===active?"bc-on":""}/>)}</div>
    </div>
  </div>;
}

/* ---------- simulateur « Construis ta route » ---------- */
function Builder(){
  const [step,setStep]=useState(0),[picks,setPicks]=useState<string[]>([]);
  const done=step>=builderSteps.length;
  const choose=(opt:string)=>{const next=[...picks];next[step]=opt;setPicks(next);};
  return <div className="bc-builder" data-reveal>
    {builderSteps.map((s,i)=>{
      return <div key={s.key} className={`bc-builder-item${i===step?" bc-open":""}`}>
        <button className="bc-builder-trigger" aria-expanded={i===step} onClick={()=>setStep(i)}>
          <b>{i+1}</b>{s.label}{picks[i]?<em>{picks[i]}</em>:<em className="bc-empty">à choisir</em>}
        </button>
        {(i===step)&&<div className="bc-builder-panel">
          <div className="bc-builder-opts">{s.options.map(o=><button key={o} className={picks[i]===o?"bc-on":""} onClick={()=>choose(o)}>{o}</button>)}</div>
          <button className="bc-builder-continue" disabled={!picks[i]} onClick={()=>setStep(i+1)}>{s.continue} →</button>
        </div>}
      </div>;
    })}
    {done&&<div className="bc-builder-result"><img src="/landing-mascot-sm.png" alt="" width={54} height={54}/><div><p><b>Ta route est prête :</b> {picks.filter(Boolean).join(" · ")}. Ta première mission t’attend !</p><Link className="bc-btn bc-btn-primary" href="/connexion">Commencer ma route →</Link></div></div>}
  </div>;
}

/* ---------- FAQ accordéon ---------- */
function Faq(){const [open,setOpen]=useState<number>(0);return <div className="bc-faq">{faq.map((f,i)=><div key={f.q} className={`bc-faq-item${open===i?" bc-open":""}`}><button aria-expanded={open===i} onClick={()=>setOpen(open===i?-1:i)}>{f.q}<i/></button><div className="bc-faq-a"><div><p>{f.a}</p></div></div></div>)}</div>;}

/* ---------- page ---------- */
export function Landing(){
  const ref=useReveal(),[scrolled,setScrolled]=useState(false);
  useEffect(()=>{const onScroll=()=>setScrolled(window.scrollY>8);onScroll();window.addEventListener("scroll",onScroll,{passive:true});return()=>window.removeEventListener("scroll",onScroll);},[]);
  return <div className="bc-landing" ref={ref}>
    <header className={`bc-nav${scrolled?" bc-scrolled":""}`}>
      <div className="bc-nav-inner">
        <Link className="bc-brand" href="/"><img src="/landing-mascot-sm.png" alt="" width={36} height={36}/>BoostClasse</Link>
        <nav className="bc-nav-links" aria-label="Découvrir BoostClasse">
          <a href="#parcours">Comment ça marche</a><a href="#matieres">Les matières</a><a href="#offres">Les offres</a><a href="#faq">FAQ</a>
        </nav>
        <div className="bc-nav-cta">
          <Link href="/connexion">Se connecter</Link>
          <Link className="bc-btn bc-btn-primary" href="/connexion">On y va !</Link>
        </div>
      </div>
    </header>

    <section className="bc-hero">
      <div className="bc-shell bc-promise">
        <div className="bc-promise-copy">
          <p className="bc-badge"><span className="bc-dot"/>Le compagnon d’apprentissage · CP → CM2</p>
          <h1>Apprends par toi-même.<br/><span>Tout est à ta portée.</span></h1>
          <p className="bc-hero-sub">Leçons claires, exercices, quiz et indices : BoostClasse ne donne jamais la réponse — il t’apprend à la trouver.</p>
          <div className="bc-hero-actions">
            <a className="bc-btn bc-btn-ghostw" href="#parcours">Explorer gratuitement</a>
            <Link className="bc-btn bc-btn-white" href="/connexion">Créer mon compte</Link>
          </div>
          <InfinityCounter/>
        </div>
        <div className="bc-hero-mascot" data-reveal>
          <img src="/landing-mascot.png" alt="Ton guide BoostClasse, prêt à explorer avec toi" width={560} height={560}/>
          <p className="bc-speech">On commence ? 🚀</p>
        </div>
      </div>
    </section>

    <section className="bc-guide-band">
      <div className="bc-shell bc-guide-grid">
        <img className="bc-guide-mascot" src="/landing-mascot.png" alt="" width={560} height={560} data-reveal/>
        <div data-reveal>
          <span className="bc-eyebrow">Ton guide</span>
          <h2 className="bc-h2">Pose ta question,<br/>garde le fil.</h2>
          <p className="bc-lead">Quand ça bloque, le guide ne lâche pas la question : il te répond avec des indices, jusqu’à ce que la lumière vienne de toi.</p>
          <div className="bc-chips"><span>Il pose la bonne question</span><span>Il donne une piste</span><span>Il applaudit à la fin</span></div>
        </div>
      </div>
    </section>

    <section className="bc-section" id="parcours">
      <div className="bc-shell">
        <div className="bc-head" data-reveal>
          <span className="bc-eyebrow">Comment ça marche</span>
          <h2 className="bc-h2">Ta route vers la réussite.</h2>
          <p className="bc-lead">Leçons, ateliers, guide et entraînement s’enchaînent comme une quête. Chaque étape prépare la suivante.</p>
        </div>
        <Showcase/>
      </div>
    </section>

    {features.map((f,i)=><section className={`bc-section bc-feature-sec${f.flip?" bc-flip":""}`} key={f.title} id={i===3?"methode":undefined}>
      <div className="bc-shell bc-feature">
        <div className="bc-feature-copy" data-reveal>
          <h2 className="bc-h2">{f.title}</h2>
          <p className="bc-lead">{f.text}</p>
          <div className="bc-chips">{f.chips.map(c=><span key={c}>{c}</span>)}</div>
        </div>
        <div className="bc-mock" data-reveal aria-hidden="true"><div className="bc-mock-head">{f.title}<span className="bc-live"><i/><i/><i/></span></div><Mock kind={f.mock}/></div>
      </div>
    </section>)}

    <section className="bc-section bc-midcta">
      <div className="bc-shell" data-reveal>
        <img src="/landing-mascot-sm.png" alt="" width={72} height={72}/>
        <div><h2 className="bc-h2">Une idée ? Essaie-la<br/>tout de suite.</h2></div>
        <Link className="bc-btn bc-btn-primary" href="/connexion">Commencer une mission →</Link>
      </div>
    </section>

    <section className="bc-section bc-rythme">
      <div className="bc-shell">
        <div className="bc-head" data-reveal>
          <span className="bc-eyebrow">Le rythme</span>
          <h2 className="bc-h2">Un rythme construit autour de ce que tu fais.</h2>
          <p className="bc-lead">Le CM2 ne se prépare pas avec une pile de pages ouvertes. BoostClasse garde chaque action reliée à la suivante.</p>
        </div>
        <div className="bc-rythme-grid">
          {rythme.map((r,i)=><article className="bc-rythme-card" key={r.title} data-reveal style={{transitionDelay:`${i*70}ms`}}><b>0{i+1}</b><h3>{r.title}</h3><p>{r.text}</p></article>)}
        </div>
      </div>
    </section>

    <section className="bc-section" id="offres">
      <div className="bc-shell">
        <div className="bc-head" data-reveal>
          <span className="bc-eyebrow">Les offres</span>
          <h2 className="bc-h2">Tout le programme.<br/>Une seule plateforme.</h2>
        </div>
        <div id="matieres" className="bc-matieres" data-reveal>
          <a href="#offres">📖 Français</a><a href="#offres">🔢 Mathématiques</a><a href="#offres">🏛 Histoire</a><a href="#offres">🔬 Sciences</a>
        </div>
        <p className="bc-promo" data-reveal>📣 Rentrée 2026 · Les classes du CP au CM2 sont ouvertes — les comptes sont créés par ton école.</p>
        <div className="bc-cards">
          {offers.map((o,i)=><article className={`bc-card bc-card-${o.style}`} key={o.name} data-reveal style={{transitionDelay:`${i*70}ms`}}>
            {o.tag&&<span className="bc-card-tag">{o.tag}</span>}
            <h3>{o.name}</h3>
            <p className="bc-card-pitch">{o.pitch}</p>
            <ul>{o.feats.map(f=><li key={f}>{f}</li>)}</ul>
            <Link className={`bc-btn ${o.style==="hero"?"bc-btn-primary":"bc-btn-plain"}`} href="/connexion">{o.style==="ghost"?"Explorer":o.style==="hero"?"Entrer":"Découvrir"}</Link>
          </article>)}
        </div>
        <div className="bc-compare" data-reveal>
          <h3 className="bc-h3">Compare ce qui est inclus.</h3>
          <div className="bc-table-wrap">
            <table>
              <thead><tr><th>Fonctionnalité</th><th>Découverte</th><th>Élève</th><th>Parent</th><th>Enseignant</th></tr></thead>
              <tbody>{tableRows.map(r=><tr key={r[0]}><th>{r[0]}</th>{r.slice(1).map((c,j)=><td key={j} className={c==="✓"?"bc-yes":c==="Aperçu"?"bc-trial":""}>{c}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </div>
        <div className="bc-head" data-reveal>
          <span className="bc-eyebrow">Simulateur</span>
          <h2 className="bc-h2">Construis ta route.</h2>
        </div>
        <Builder/>
      </div>
    </section>

    <section className="bc-section" id="faq" style={{paddingTop:0}}>
      <div className="bc-shell">
        <div className="bc-head" data-reveal>
          <span className="bc-eyebrow">FAQ</span>
          <h2 className="bc-h2">Avant de commencer.</h2>
        </div>
        <Faq/>
      </div>
    </section>

    <section className="bc-section" style={{paddingTop:0}}>
      <div className="bc-shell">
        <div className="bc-question-band" data-reveal>
          <img className="bc-flipx" src="/landing-mascot.png" alt="" width={560} height={560}/>
          <div>
            <h2 className="bc-h2">Encore une petite<br/>question ?</h2>
            <p className="bc-lead">Regarde la FAQ, ou demande à ton enseignant — ici, aucune question n’est bête.</p>
            <div className="bc-hero-actions"><a className="bc-btn bc-btn-primary" href="#faq">Revoir la FAQ</a></div>
          </div>
        </div>
      </div>
    </section>

    <section className="bc-section" style={{paddingTop:0}}>
      <div className="bc-shell">
        <div className="bc-final-cta" data-reveal>
          <h2 className="bc-h2">Prends une notion.<br/>Apprivoise-la.</h2>
          <p className="bc-lead">Explore l’espace réel et ses activités de démonstration avant de créer ton compte.</p>
          <div className="bc-hero-actions">
            <a className="bc-btn bc-btn-ghostw" href="#parcours">Explorer gratuitement</a>
            <Link className="bc-btn bc-btn-white" href="/connexion">Créer mon compte</Link>
          </div>
          <p className="bc-final-note">Déjà un compte ? <Link href="/connexion">Se connecter</Link></p>
        </div>
      </div>
    </section>

    <footer className="bc-footer">
      <div className="bc-shell">
        <div className="bc-footer-grid">
          <div className="bc-footer-brand">
            <Link className="bc-brand" href="/"><img src="/landing-mascot-sm.png" alt="" width={36} height={36}/>BoostClasse</Link>
            <p>L’espace d’apprentissage des élèves du CP au CM2. Le plaisir de progresser, un indice à la fois.</p>
          </div>
          <div><h3>Découvrir</h3><ul><li><a href="#parcours">Comment ça marche</a></li><li><a href="#matieres">Les matières</a></li><li><a href="#offres">Les offres</a></li><li><a href="#faq">FAQ</a></li></ul></div>
          <div><h3>Accès</h3><ul><li><Link href="/connexion">Se connecter</Link></li><li><Link href="/connexion">Espace élève</Link></li><li><Link href="/connexion">Espace parent</Link></li><li><Link href="/connexion">Espace enseignant</Link></li></ul></div>
        </div>
        <div className="bc-footer-bottom"><span>© 2026 BoostClasse</span><span>Fait avec soin pour les élèves du CP au CM2.</span></div>
      </div>
    </footer>
  </div>;
}
