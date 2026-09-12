"use client";
import type {ReactNode} from "react";
import {Calculator,FlaskConical,Languages} from "lucide-react";
import "./subject-banner.css";

const banners={
  francais:{image:"/banner-francais.jpg",Icon:Languages,kicker:"Français · CM2",title:"Les mots, ça se comprend en jouant.",tagline:"28 leçons pour démonter les phrases, faire voyager les verbes et trouver les bons accords — avec des indices à chaque étape.",steps:["Découvrir","Essayer","Comprendre"],alt:"Classe de français imagée : une mascotte verte explore la conjugaison au tableau, le dictionnaire et le globe."},
  mathematiques:{image:"/banner-mathematiques.jpg",Icon:Calculator,kicker:"Mathématiques · CM2",title:"Les maths prennent forme.",tagline:"32 ateliers pour comparer, calculer, mesurer et raisonner.",steps:["Observer","Essayer","Expliquer"],alt:"Classe de mathématiques imagée : une mascotte verte travaille les équations et les figures au tableau."},
  sciences:{image:"/banner-sciences.jpg",Icon:FlaskConical,kicker:"Sciences · CM2",title:"Observe, questionne, vérifie.",tagline:"Quatre laboratoires pour prédire, manipuler et observer : l’eau, le vivant, la lumière et la Terre. Puis trouver les mots pour expliquer.",steps:["Prédire","Manipuler","Observer"],alt:"Laboratoire de sciences imagé : une mascotte verte observe les fioles colorées et le microscope."},
} as const;

export type BannerSubject=keyof typeof banners;

export function SubjectBanner({subject}:{subject:BannerSubject}){
  const {image,Icon,kicker,title,tagline,steps,alt}=banners[subject];
  return <section className={`subject-banner subject-banner-${subject}`} aria-label={`Bannière ${kicker}`}>
    <div className="subject-banner-copy">
      <p className="subject-banner-kicker"><Icon size={18}/>{kicker}</p>
      <h2>{title}</h2>
      <p>{tagline}</p>
      <ol className="subject-banner-steps" aria-label="Le fil de chaque leçon">{steps.map((step,i)=><li key={step}><span>0{i+1}</span>{step}</li>)}</ol>
    </div>
    <div className="subject-banner-figure"><img src={image} alt={alt} width={1400} height={700} loading="lazy"/></div>
  </section>;
}
