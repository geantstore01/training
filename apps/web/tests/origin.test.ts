import {expect,it} from "vitest";
import {allowedOrigin} from "../src/lib/origin";
const origins="http://127.0.0.1:18088, https://boostclasse.com, https://www.boostclasse.com";
const request=(origin:string,site="same-origin")=>new Request("http://web:3000/api/session",{headers:{origin,"sec-fetch-site":site}});
it("accepte le domaine public derrière le proxy et l’accès local configuré",()=>{for(const origin of ["https://boostclasse.com","https://www.boostclasse.com","http://127.0.0.1:18088"])expect(allowedOrigin(request(origin),origins)).toBe(true);});
it("refuse les origines absentes, voisines, HTTP public et les requêtes intersites",()=>{for(const origin of ["","https://boostclasse.com.evil.example","https://evil.example","http://boostclasse.com"])expect(allowedOrigin(request(origin),origins)).toBe(false);expect(allowedOrigin(request("https://boostclasse.com","cross-site"),origins)).toBe(false);});
