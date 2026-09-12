// Recette opérateur explicite : accès lus sur stdin, jamais enregistrés dans les captures.
import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
let raw="";for await(const chunk of process.stdin)raw+=chunk;
const credentials=JSON.parse(raw),base=process.env.LOGIN_TEST_ORIGIN||"http://127.0.0.1:18088";
const browser=await chromium.launch({channel:"msedge",headless:true});
try {
 for(const login of ["eleve1","admin"]) {
  const context=await browser.newContext();const page=await context.newPage();
  const errors=[];page.on("pageerror",e=>errors.push(e.message));
  await page.goto(base+"/connexion");
  assert.equal(await page.locator('input[name="school_id"]').count(),0);
  assert.match(await page.title(),/BoostClasse/);
  assert.equal(await page.locator(".boost-mark").count(),1);
  assert.deepEqual(await page.locator('#level option').allTextContents(),["CP","CE1","CE2","CM1","CM2"]);
  await page.getByLabel("Ta classe").selectOption("CM2");
  await page.getByLabel("Ton identifiant").fill(login);
  await page.getByLabel("Ton mot de passe").fill(credentials.find(x=>x.login===login).password);
  await page.getByRole("button",{name:"Entrer dans mon espace"}).click();
  await page.waitForURL(base+(login==="eleve1"?"/eleve":"/enseignant"));
  const me=await context.request.get(base+"/api/session");assert.equal(me.status(),200);assert.equal((await me.json()).login,login);
  assert.deepEqual(errors,[]);
  if(base.startsWith("https:"))assert.equal((await context.cookies()).find(c=>c.name==="edu_session")?.secure,true);
  await context.request.delete(base+"/api/session",{headers:{Origin:base}});
  await context.close();console.log(login+": profil et session vérifiés");
 }
 const context=await browser.newContext();
 const student=credentials.find(x=>x.login==="eleve1");
 let r=await context.request.post(base+"/api/session",{headers:{Origin:base},data:{...student,level:"CE1"}});
 assert.equal(r.status(),403);assert.equal((await context.request.get(base+"/api/session")).status(),401);
 console.log("Classe incorrecte : refusée sans session");
 r=await context.request.post(base+"/api/session",{headers:{Origin:base},data:{login:"eleve1",password:"invalid-password",level:"CM2"}});
 assert.equal(r.status(),401);console.log("Mot de passe incorrect : refusé");
 for(const login of ["prof.master","review.cm2"]) {
  r=await context.request.post(base+"/api/session",{headers:{Origin:base},data:{...credentials.find(x=>x.login===login),level:"CM2"}});
  assert.equal(r.status(),200);const me=await context.request.get(base+"/api/session");assert.equal((await me.json()).login,login);
  await context.request.delete(base+"/api/session",{headers:{Origin:base}});console.log(login+": accès vérifié");
 }
 r=await context.request.post(base+"/api/session",{headers:{Origin:"https://evil.example"},data:{...student,level:"CM2"}});assert.equal(r.status(),403);console.log("Origine étrangère : refusée");
 const page=await context.newPage();await page.goto(base+"/connexion");
 await page.screenshot({path:"test-results/connexion-classes-vps.png",fullPage:true});
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await context.close();
} finally {await browser.close();}
