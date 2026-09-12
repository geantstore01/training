import type { Role } from "./contracts";
export function home(roles: Role[]) { return roles.includes("student") ? "/eleve" : roles.includes("parent") ? "/parent" : roles.some(r=>r==="school_admin"||r==="sys_admin")?"/administration":"/enseignant"; }
export function mayEnter(roles: Role[], area: string) {
  if(area==="administration")return roles.some(r=>r==="school_admin"||r==="sys_admin");
  if (area === "eleve") return roles.includes("student");
  if (area === "parent") return roles.includes("parent");
  return roles.some(r => ["teacher", "school_admin", "sys_admin"].includes(r));
}
export function allowedPath(service: string, path: string, method: string) {
  const rules: Record<string, RegExp> = {
    curriculum: /^(?:subjects|levels|domains|competencies(?:\/[a-f0-9-]+(?:\/graph)?)?)$/,
    user: /^(accounts|me(?:\/assents)?|students(?:\/[a-f0-9-]+(?:\/(?:preferences|permissions|consents(?:\/withdraw)?))?)?|consent-policy)$/,
    class: /^(classes(?:\/[a-f0-9-]+(?:\/(?:students(?:\/[a-f0-9-]+(?:\/tutor-control)?)?|groups(?:\/[a-f0-9-]+)?|missions(?:\/[a-f0-9-]+\/archive)?))?)?|missions\/today)$/,
    exercise: /^(exercises(?:\/[a-f0-9-]+\/versions\/[0-9]+\/(?:editorial|reviews))?|review-version\/[a-f0-9-]+|published\/[a-f0-9-]+)$/,
    content: /^(?:availability|french\/review-catalogue|history\/(?:review-catalogue|drafts\/prepare)|contents(?:\/[a-f0-9-]+\/versions\/[0-9]+(?:\/reviews)?)?)$/,
    assessment: /^(history\/catalogue|science\/(?:catalogue|runs(?:\/[a-f0-9-]+\/conclusion)?|notebook\/[a-f0-9-]+)|sessions(?:\/[a-f0-9-]+\/complete)?|attempts(?:\/[a-f0-9-]+(?:\/(?:submit|correction|next|hints\/[1-6]))?)?|students\/[a-f0-9-]+\/(?:errors|mastery|attempts|course-progress))$/,
    analytics: /^(dashboard|students\/[a-f0-9-]+\/dashboard|classes\/[a-f0-9-]+\/dashboard)$/,
    tutor: /^(turns|attempts\/[a-f0-9-]+\/history)$/,
    speech: /^synthesize$/,
    notification: /^inbox(?:\/[a-f0-9-]+\/read)?$/,
  };
  if((service==="curriculum"||(service==="user"&&path==="accounts"))&&method!=="GET")return false;
  return ["GET","POST","PUT","DELETE"].includes(method) && !!rules[service]?.test(path);
}
