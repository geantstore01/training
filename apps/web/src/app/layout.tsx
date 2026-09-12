import {headers} from "next/headers";
import type { Metadata } from "next";
import "@fontsource/atkinson-hyperlegible/400.css";
import "@fontsource/atkinson-hyperlegible/700.css";
import "@fontsource/nunito/700.css";
import "@fontsource/nunito/800.css";
import "@fontsource/nunito/900.css";
import "./globals.css";
export const metadata:Metadata={title:{default:"BoostClasse · Le plaisir de progresser",template:"%s · BoostClasse"},description:"L’espace d’apprentissage des élèves du CP au CM2.",robots:{index:false,follow:false}};
export default async function Layout({children}:{children:React.ReactNode}){await headers();return <html lang="fr"><head><link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/><link rel="stylesheet" href={"https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap"}/></head><body>{children}</body></html>;}
