import React from "react";
import {createRoot} from "react-dom/client";
import {StudentSpace} from "../../src/components/student";
import "@fontsource/atkinson-hyperlegible/400.css";
import "@fontsource/nunito/800.css";
import "../../src/app/globals.css";
createRoot(document.getElementById("root")!).render(<><header className="reading-bar"><strong>Recette locale du parcours CM2</strong><span> · Contenus à relire · Corrections contrôlées · Sans IA distante · Essais éphémères</span></header><main className="main-content"><StudentSpace initialSubject={new URLSearchParams(window.location.search).get("subject")??undefined} account={{id:"preview",login:"preview",roles:["student"],school_id:"preview",student_id:"preview",teacher_id:null}}/></main></>);
