import {describe,it,expect} from "vitest";
import {mayEnter,allowedPath} from "../src/lib/access";
import {initialJourney,journeyReducer,moveItem} from "../src/lib/journey";
describe("frontières des espaces",()=>{
  it("ouvre les carnets scientifiques sans exposer les brouillons IA",()=>{expect(allowedPath("assessment","science/runs","POST")).toBe(true);expect(allowedPath("assessment","science/notebook/abcdef","GET")).toBe(true);expect(allowedPath("assessment","science/notebook/abcdef","DELETE")).toBe(true);expect(allowedPath("assessment","science/drafts","POST")).toBe(false);});
  it("ne confond pas parent, élève et enseignant",()=>{expect(mayEnter(["student"],"enseignant")).toBe(false);expect(mayEnter(["parent"],"eleve")).toBe(false);expect(mayEnter(["school_admin"],"enseignant")).toBe(true);});
  it("refuse les routes privées, traversées et méthodes non prévues",()=>{expect(allowedPath("ai-router","plan","POST")).toBe(false);expect(allowedPath("exercise","exercises/id/versions/1/editorial","GET")).toBe(false);expect(allowedPath("user","../auth/login","POST")).toBe(false);expect(allowedPath("class","classes","TRACE")).toBe(false);expect(allowedPath("class","classes","GET")).toBe(true);});
});
describe("parcours et manipulation",()=>{
  it("déplace sans perdre ni dupliquer les cartes",()=>{expect(moveItem(["a","b","c"],2,0)).toEqual(["c","a","b"]);expect(moveItem(["a"],0,-1)).toEqual(["a"]);});
  it("conserve les essais lors d'une erreur réseau",()=>{const s=journeyReducer(initialJourney,{type:"answer",id:"q",value:"12"});const failed=journeyReducer(s,{type:"error",error:"Interruption"});expect(failed.answers.q).toBe("12");expect(failed.busy).toBe(false);});
  it("efface les réponses lorsqu'un autre exercice commence",()=>{const state=journeyReducer({...initialJourney,answers:{q:"secret"}},{type:"load",exercise:{id:"e",kind:"short_text",prompt:{instruction:"Calcule",parts:[]}},attempt:{id:"a",session_id:"s",exercise_version_id:"e",submitted_at:null,result:null},sessionId:"s",stage:4});expect(state.answers).toEqual({});expect(state.stage).toBe(4);});
});
