"use client";
import {Button} from "@/components/ui/button";
export default function Error({reset}:{reset:()=>void}){return <main className="main-content"><h1>L’espace est momentanément indisponible.</h1><p>Ton travail déjà envoyé reste enregistré.</p><Button onClick={reset}>Réessayer</Button></main>;}
