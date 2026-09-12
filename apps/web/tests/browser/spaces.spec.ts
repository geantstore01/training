import {test,expect,type Page} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
async function login(page:Page,role:string){await page.goto("/connexion");await page.getByLabel("Ta classe").selectOption("CM1");await page.getByLabel("Ton identifiant").fill(role);await page.getByLabel("Ton mot de passe").fill("test-password");await page.getByRole("button",{name:"Entrer dans mon espace"}).click();await expect(page).toHaveURL(new RegExp(role==="student"?"/eleve":role==="teacher"?"/enseignant":"/parent"));}
test.afterEach(async({page})=>{await page.request.delete("/api/session",{headers:{Origin:"http://127.0.0.1:3000"}});});
test("connexion accessible, session opaque et protection des espaces",async({page,context,request})=>{
 await page.goto('/connexion');await expect(page.getByRole('heading',{name:'Prêt pour la suite ?'})).toBeVisible();
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 await page.screenshot({path:'test-results/connexion-desktop.png',fullPage:true});await login(page,'student');
 const cookies=await context.cookies();const session=cookies.find(c=>c.name==='edu_session');expect(session?.httpOnly).toBe(true);expect(session?.value).toMatch(/^[a-f0-9]{64}$/);
 expect(await page.evaluate(()=>Object.keys(localStorage))).toEqual([]);
 await page.goto('/enseignant');await expect(page).toHaveURL('/acces-interdit');
 const csrf=await request.post('/api/session',{headers:{Origin:'https://evil.example'},data:{}});expect(csrf.status()).toBe(403);
});
test("mission complète : choix, texte, nombre, tuteur, frise au clavier et correction",async({page})=>{
 await login(page,'student');await expect(page.getByText('Des parts à partager')).toBeVisible();
 await page.screenshot({path:'test-results/eleve-desktop.png',fullPage:true});
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 await page.getByRole('button',{name:'L’ouvrir'}).click();await page.getByRole('button',{name:'Voir mon cours'}).click();await page.getByRole('button',{name:'Je fais un premier essai'}).click();
 await page.getByLabel('Un demi',{exact:true}).check();await page.getByLabel(/Ta réponse numérique/).fill('12');await page.getByLabel(/Ta réponse :/).fill('moitié');
 await page.getByRole('button',{name:'Vérifier mon premier essai'}).click();await page.getByRole('button',{name:'Passer au premier exercice progressif'}).click();await page.getByLabel('Ta question',{exact:true}).fill('Comment reconnaître une moitié ?');await page.getByRole('button',{name:'Demander un indice'}).click();await expect(page.getByText('Comment pourrais-tu le vérifier ?')).toBeVisible();
 await page.getByLabel('Un demi',{exact:true}).check();await page.getByLabel(/Ta réponse numérique/).fill('12');await page.getByLabel(/Ta réponse :/).fill('moitié');
 await page.screenshot({path:'test-results/tuteur-desktop.png',fullPage:true});
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 await page.getByRole('button',{name:'Vérifier mon travail'}).click();await page.getByRole('button',{name:'Essayer le deuxième exercice'}).click();
 await page.getByRole('button',{name:'Monter Premier événement'}).focus();await page.keyboard.press('Enter');await expect(page.getByRole('status')).toContainText('position 1');
 await page.getByRole('button',{name:'Vérifier mon travail'}).click();await expect(page.getByRole('heading',{name:'Tu as pris le temps d’apprendre.'})).toBeVisible();await page.getByRole('button',{name:'Terminer ma séance'}).click();await expect(page.getByRole('button',{name:'L’ouvrir'})).toBeVisible();
});
test("parent : indicateurs, rapport et consentement explicite",async({page})=>{
 await login(page,'parent');await expect(page.getByRole('heading',{name:'Temps d’apprentissage estimé'})).toBeVisible();await page.screenshot({path:'test-results/parent-desktop.png',fullPage:true});
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 await page.getByRole('button',{name:'Rapports hebdomadaires'}).click();await expect(page.getByRole('button',{name:'Marquer comme lu'})).toBeVisible();
 await page.getByRole('button',{name:'Confidentialité & audio'}).click();await expect(page.getByRole('button',{name:'Autoriser',exact:true}).first()).toBeDisabled();await page.getByLabel('J’ai compris cet usage facultatif.').first().check();await page.getByRole('button',{name:'Autoriser',exact:true}).first().click();await expect(page.getByText('Ton choix a été enregistré.')).toBeVisible();
});
test("enseignant : besoins collectifs, mission, groupe et limite d’aide",async({page})=>{
 await login(page,'teacher');await expect(page.getByText('Reprendre le calcul avec une représentation concrète.')).toBeVisible();await page.screenshot({path:'test-results/enseignant-desktop.png',fullPage:true});
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 await page.getByRole('button',{name:'Missions du jour',exact:true}).click();await page.getByLabel('Titre de la mission').fill('Mission de recette');await page.getByRole('checkbox').first().check();await page.getByRole('button',{name:'Publier la mission'}).click();await expect(page.getByText('Mission publiée pour les élèves concernés.')).toBeVisible();
 await page.getByRole('button',{name:'Élèves & groupes'}).click();await page.getByLabel('Nom du groupe').fill('Atelier guidé');await page.getByRole('checkbox',{name:'Camille'}).check();await page.getByRole('button',{name:'Enregistrer le groupe'}).click();await expect(page.getByText('Groupe enregistré.')).toBeVisible();
 await page.getByRole('button',{name:'Réglages de l’aide'}).click();await page.getByLabel('Accompagnement IA autorisé').uncheck();await page.getByRole('button',{name:'Appliquer',exact:true}).click();await expect(page.getByText('Réglage appliqué.')).toBeVisible();
});
test("mobile : pas de débordement, cibles et contenu accessibles",async({page})=>{
 await page.setViewportSize({width:390,height:844});await login(page,'student');await expect(page.getByRole('heading',{name:'Bonjour, Camille !'})).toBeVisible();await page.screenshot({path:'test-results/eleve-mobile.png',fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
 for(const role of ['parent','teacher']){await login(page,role);await expect(page.getByRole('heading').first()).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);}
});
