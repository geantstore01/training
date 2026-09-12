// Double HTTP explicite de recette UI. Jamais lancé par le Dockerfile ou en production.
import {createServer} from "node:http";
const uid=n=>`00000000-0000-4000-8000-${String(n).padStart(12,"0")}`;
const student={id:uid(2),user_id:uid(1),school_id:uid(9),pseudonym:"Camille",level:"CM1",accessibility_preferences:{text_size:"normal",dyslexic_font:false,voice_instructions:false}};
const account=role=>({id:uid(1),school_id:uid(9),login:role,roles:[role],student_id:role==="student"?uid(2):null,teacher_id:role==="teacher"?uid(3):null});
const choice={id:"choice",question:"Quelle fraction représente la moitié ?",competency_id:uid(8),response_type:"choice",options:[{id:"half",label:"Un demi"},{id:"third",label:"Un tiers"}]};
const parts=[choice,{id:"number",question:"Combien font 6 + 6 ?",competency_id:uid(8),response_type:"number",options:[]},{id:"word",question:"Complète : un demi est une ____.",competency_id:uid(8),response_type:"text",options:[]}];
const exercises=[{id:uid(4),kind:"fill_blanks",prompt:{instruction:"Observe les parts et complète les trois réponses.",parts}},{id:uid(5),kind:"timeline",prompt:{instruction:"Replace les événements sur la frise.",parts:[{id:"order",question:"Du plus ancien au plus récent",competency_id:uid(8),response_type:"ordering",options:[{id:"b",label:"Deuxième événement"},{id:"a",label:"Premier événement"},{id:"c",label:"Troisième événement"}]}]}}];
exercises.splice(1,0,{...exercises[0],id:uid(40)});
const mission={id:uid(6),class_id:uid(7),title:"Des parts à partager",day:new Date().toISOString().slice(0,10),group_id:null,status:"published",exercise_version_ids:exercises.map(e=>e.id)};
const progress={student_id:uid(2),competences_acquises:4,competences_a_retravailler:1,competences_en_apprentissage:3,minutes_session_estimees:22,tentatives_terminees:5,message:"Chaque séance permet d’avancer à son rythme."};
let requests=[],attempts=new Map(),control={student_id:uid(2),enabled:true,max_help:6,revision:0};
createServer(async(req,res)=>{let raw="";for await(const chunk of req)raw+=chunk;const body=raw?JSON.parse(raw):{};const u=new URL(req.url,"http://localhost"),path=u.pathname.replace(/^\/services\/([a-z-]+)-service/,'/$1');const role=(req.headers.authorization||"Bearer access-student").replace("Bearer access-","");requests.push({path,method:req.method,body});
 const send=(v,status=200)=>{res.writeHead(status,{"Content-Type":"application/json"});res.end(JSON.stringify(v));};
 if(path==="/__stats")return send(requests);
 if(path==="/auth/login")return body.password==="test-password"?send({access_token:`access-${body.login}`,refresh_token:`refresh-${body.login}`,expires_in:1}):send({detail:"Accès refusé"},401);
 if(path==="/auth/refresh")return send({access_token:body.refresh_token.replace("refresh-","access-"),refresh_token:body.refresh_token,expires_in:300});
 if(path==="/auth/logout")return send({});
 if(path==="/user/me")return send(account(role));
 if(path==="/user/students")return send([student]);
 if(path===`/user/students/${student.id}`)return send(student);
 if(path.endsWith("/preferences"))return send({...student,accessibility_preferences:body});
 if(path.endsWith("/permissions"))return send({ai_local:true,ai_cloud:true,voice:false});
 if(path==="/user/consent-policy")return send({version:"2026-09-v1",purposes:{ai_local:"Aide sur le serveur de l’école.",ai_cloud:"Aide externe après filtrage.",voice:"Lire les consignes à voix haute."},child_notice:"Tu peux dire oui ou non.",withdrawal:"Les choix peuvent être retirés à tout moment."});
 if(path.endsWith("/consents"))return send(req.method==="GET"?[]:{id:uid(20),...body});
 if(path==="/user/me/assents")return send({id:uid(21),...body});
 if(path==="/class/missions/today"||path.endsWith("/missions"))return send(req.method==="GET"?[mission]:{...mission,...body},req.method==="GET"?200:201);
 if(path==="/class/classes")return send([{id:uid(7),name:"CM1 · Les explorateurs",academic_year:2026}]);
 if(path.endsWith("/tutor-control")){if(req.method==="PUT")control={student_id:uid(2),enabled:body.enabled,max_help:body.max_help,revision:control.revision+1};return send(control);}
 if(path.match(/^\/class\/classes\/[^/]+\/students$/))return send([student]);
 if(path.endsWith("/groups"))return send(req.method==="GET"?[]:{id:uid(25),...body});
 if(path==="/exercise/exercises")return send(exercises);
 if(path.startsWith("/exercise/published/"))return send(exercises.find(x=>path.endsWith(x.id))||exercises[0]);
 if(path==="/content/contents")return send([{id:uid(10),version:1,title:"Partager en parts égales"}]);
 if(path.startsWith("/content/contents/"))return send({title:"Partager en parts égales",body:{summary:"Découvrir comment partager en parts égales.",objectives:["Reconnaître une moitié."],blocks:[{kind:"paragraph",text:"Pour obtenir deux moitiés, les deux parts doivent être égales."}],steps:[]}});
 if(path==="/assessment/sessions")return send({id:uid(11)},201);
 if(path.endsWith("/complete"))return send({id:uid(11),status:"completed"});
 if(path==="/assessment/attempts"){const attempt={id:uid(30+attempts.size),session_id:uid(11),exercise_version_id:body.exercise_version_id,submitted_at:null,result:null};attempts.set(attempt.id,attempt);return send(attempt,201);}
 if(path.endsWith("/submit")){const id=path.split('/')[3],a=attempts.get(id);return send({...a,submitted_at:new Date().toISOString(),result:{message:"Tu as terminé cet essai.",feedback:Object.keys(body.answers).map(part_id=>({part_id,outcome:"réussi",message:"La démarche est comprise.",error_code:null}))}});}
 if(path==="/tutor/turns")return send({message_pedagogique:"Observe les parts. Ont-elles la même taille ?",type:"questionnement",niveau_aide:body.plus_aide?1:0,question_suivante:"Comment pourrais-tu le vérifier ?",erreur_detectee:"non_determinee",action_recommandee:"identifier",safety_status:"safe"});
 if(path.startsWith("/analytics/"))return send(path.includes('/classes/')?[progress]:progress);
 if(path.endsWith("/mastery"))return send([{competency_id:uid(8),level:"en_cours"}]);
 if(path.startsWith("/curriculum/competencies/"))return send({label:"Reconnaître et représenter une moitié"});
 if(path.endsWith("/errors"))return send([{competency_id:uid(8),error_code:"CALCULATION_ERROR",recurring:true,message:"Reprendre le calcul avec une représentation concrète."}]);
 if(path==="/notification/inbox")return send([{id:uid(12),student_id:uid(2),kind:"weekly_report",period:"2026-09-07",body:progress,read_at:null}]);
 if(path.endsWith("/read"))return send({id:uid(12)});
 if(path==="/speech/synthesize")return send({detail:"La lecture audio nécessite les accords du parent et de l’enfant."},403);
 return send({detail:`Route de recette non prévue : ${path}`},404);
}).listen(19091,"127.0.0.1",()=>console.log("Double HTTP de recette sur 19091"));
