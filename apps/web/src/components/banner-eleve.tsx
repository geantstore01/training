"use client";
import {useEffect,useRef,useState} from "react";
import {BookOpen,LogOut,Sparkles,Volume2,VolumeX} from "lucide-react";
import {api} from "@/lib/client";

/* Sons rétro en WebAudio, sans dépendance (port du prototype de bannière élève). */
let audioCtx:AudioContext|null=null;
function blip(freq:number,at:number,dur:number,type:OscillatorType="square",vol=0.05){
	try{const C=window.AudioContext,a=(C&&(window as unknown as {webkitAudioContext?:typeof AudioContext}).webkitAudioContext)??C;if(!audioCtx)audioCtx=new (a as typeof AudioContext)();
	const c=audioCtx,o=c.createOscillator(),g=c.createGain();o.type=type;o.frequency.value=freq;
	g.gain.setValueAtTime(vol,c.currentTime+at);g.gain.exponentialRampToValueAtTime(0.0001,c.currentTime+at+dur);
	o.connect(g).connect(c.destination);o.start(c.currentTime+at);o.stop(c.currentTime+at+dur);}catch{/* audio indisponible : on reste silencieux */}
}
const buttonClickSound=()=>{blip(600,0,0.07);blip(880,0.06,0.09,"square",0.04);};
const xpGainSound=()=>{blip(523,0,0.09);blip(659,0.08,0.09);blip(784,0.16,0.12,"square",0.06);};

/* Mini-confettis plein écran, sans dépendance. */
function confettiBurst(x:number,y:number,count:number){
	const canvas=document.createElement("canvas"),dpr=window.devicePixelRatio||1;
	canvas.width=window.innerWidth*dpr;canvas.height=window.innerHeight*dpr;
	canvas.style.cssText="position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:9999";
	document.body.appendChild(canvas);
	const c=canvas.getContext("2d");if(!c){canvas.remove();return;}
	c.scale(dpr,dpr);
	const colors=["#f2c64e","#e8623c","#7ac74f","#4aa9e8","#ffffff","#f9a8d4"];
	const parts=Array.from({length:count},()=>({x,y,vx:(Math.random()-.5)*7,vy:-2-7*Math.random(),s:3+5*Math.random(),r:Math.random()*Math.PI,vr:(Math.random()-.5)*.3,color:colors[Math.floor(Math.random()*colors.length)],life:1}));
	let n=0;
	(function frame(){n++;c.clearRect(0,0,window.innerWidth,window.innerHeight);
		for(const p of parts){p.x+=p.vx;p.y+=p.vy;p.vy+=.22;p.r+=p.vr;p.life-=.012;
			c.save();c.globalAlpha=Math.max(p.life,0);c.translate(p.x,p.y);c.rotate(p.r);c.fillStyle=p.color;c.fillRect(-p.s/2,-p.s/2,p.s,p.s);c.restore();}
		if(n<90)requestAnimationFrame(frame);else canvas.remove();})();
}

const QUOTES=["Pika-Boost ! Prêt pour les devoirs !","Apprendre, c’est comme monter de niveau !","Super élève ! +20 XP de savoir !","En route vers les meilleures notes !","Pika-Savoir en action !"];
const STARS=[{top:"22%",left:"26%"},{top:"38%",left:"14%"},{top:"48%",left:"16%"},{top:"32%",left:"42%"},{top:"46%",left:"43%"}];

export function BannerEleve({missionsCount=0}:{missionsCount?:number}){
	const [soundOn,setSoundOn]=useState(true),[clicks,setClicks]=useState(0),[bubble,setBubble]=useState<string|null>(null),[quitting,setQuitting]=useState(false);
	const bubbleTimer=useRef<number>(0);
	useEffect(()=>()=>window.clearTimeout(bubbleTimer.current),[]);
	const onCharacter=(e:React.MouseEvent)=>{if(soundOn)xpGainSound();setClicks(n=>n+1);setBubble(QUOTES[clicks%QUOTES.length]);confettiBurst(e.clientX,e.clientY,35);window.clearTimeout(bubbleTimer.current);bubbleTimer.current=window.setTimeout(()=>setBubble(null),2600);};
	const onStar=(e:React.MouseEvent)=>{if(soundOn)xpGainSound();confettiBurst(e.clientX,e.clientY,18);};
	const onBook=(e:React.MouseEvent)=>{if(soundOn)xpGainSound();confettiBurst(e.clientX,e.clientY,25);};
	const onMissions=()=>{if(soundOn)buttonClickSound();(document.querySelector(".optional-missions")??document.querySelector(".choice-section"))?.scrollIntoView({behavior:"smooth",block:"start"});};
	const onQuit=async()=>{if(soundOn)buttonClickSound();if(quitting)return;setQuitting(true);try{await api("session",{method:"DELETE"});}catch{/* la session expire côté serveur : on redirige quand même */}window.location.assign("/connexion");};
	return <section className="banner-eleve" aria-label="Tableau de bord BoostClasse">
		<div className="be-stage">
			<img src="/banner-eleve.webp" alt="Un monde Minecraft en plein ciel où Pikachu et ses amis partent à la découverte du savoir" width={1376} height={768} draggable={false}/>
			<button type="button" className="be-character" onClick={onCharacter} title="Clique sur le Pika-Élève pour l’animer et gagner de l’XP !">
				<span className="be-halo"/>
				{bubble&&<span className="be-bubble" role="status">⭐ {bubble}</span>}
			</button>
			{STARS.map((pos,i)=><button key={i} type="button" className="be-star" style={pos} onClick={onStar} title="Étoile de réussite ! Clique pour une étincelle !" aria-label={`Étoile de réussite ${i+1}`}><Sparkles size={26}/></button>)}
			<div className="be-title"><h1>BoostClasse</h1><p className="be-slogan">Apprendre ensemble !</p></div>
			<div className="be-actions">
				<button type="button" className="be-book" onClick={onBook} title="Livre de savoir BoostClasse" aria-label="Livre de savoir BoostClasse">
					<BookOpen size={26}/>
					<Sparkles className="be-book-spark" size={14}/>
				</button>
				<div className="be-btn-row">
					<button type="button" className="be-btn be-btn-missions" onClick={onMissions}>
						<BookOpen size={16}/>
						<span>Mes missions</span>
						{missionsCount>0&&<span className="be-count" title="Activités proposées aujourd’hui">{missionsCount}</span>}
					</button>
					<button type="button" className="be-btn be-btn-quit" onClick={onQuit} disabled={quitting}>
						<LogOut size={16}/>
						<span>{quitting?"À bientôt…":"Quitter"}</span>
					</button>
				</div>
			</div>
			<div className="be-top">
				<button type="button" className="be-sound" aria-pressed={soundOn} title={soundOn?"Sons activés":"Sons coupés"} aria-label={soundOn?"Couper les sons":"Activer les sons"} onClick={()=>{buttonClickSound();setSoundOn(v=>!v);}}>
					{soundOn?<Volume2 size={17}/>:<VolumeX size={17}/>}
				</button>
			</div>
		</div>
	</section>;
}
