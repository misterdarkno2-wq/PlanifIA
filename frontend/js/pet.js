import {api,escapeHTML as e,toast} from './app.js';


// Ilustración original en SVG: cinco siluetas, sin descargas ni imágenes externas.
export function portrait(stage){
 const s=Math.max(1,Math.min(5,Number(stage)||1));
 return `<svg viewBox="0 0 260 220" aria-hidden="true" class="lumi-art">
 <ellipse cx="130" cy="192" rx="76" ry="12" fill="#c3e2d5"/>
 <circle cx="130" cy="105" r="87" fill="#e2f4e9"/>
 <g class="lumi-sparks" fill="#e7b354"><path d="m44 65 3-9 3 9 9 3-9 3-3 9-3-9-9-3Z"/><path d="m213 131 2-7 2 7 7 2-7 2-2 7-2-7-7-2Z"/></g>
 <g class="lumi-body">
 ${s>=4?'<path d="M88 130Q22 70 38 157Q48 180 87 164M172 130Q238 70 222 157Q212 180 173 164" fill="#56b59b" stroke="#247c6a" stroke-width="3"/>':''}
 ${s>=2?`<path d="M83 98Q${s>=3?'44 20 101 65':'59 44 106 76'}L112 106M177 98Q${s>=3?'216 20 159 65':'201 44 154 76'}L148 106" fill="#53b39c" stroke="#247c6a" stroke-width="3"/>`:''}
 ${s===5?'<path d="m98 51-8-24 25 12 15-23 15 23 25-12-8 24Z" fill="#f2c568" stroke="#b67e26" stroke-width="3"/><circle cx="130" cy="42" r="5" fill="#fff3ca"/>':''}
 <path d="M73 138C67 90 90 65 130 65S193 90 187 138L180 161C175 189 85 189 80 161Z" fill="${s>=4?'#2e9b85':'#77cdb0'}" stroke="#247c6a" stroke-width="3"/>
 <ellipse cx="130" cy="146" rx="38" ry="32" fill="#d8f3d8"/>
 ${s>=3?'<path d="M125 151l5 5 10-13" fill="none" stroke="#278773" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>':''}
 <g class="lumi-eyes" fill="#163e3b"><ellipse cx="107" cy="108" rx="6" ry="9"/><ellipse cx="153" cy="108" rx="6" ry="9"/><circle cx="109" cy="105" r="2" fill="white"/><circle cx="155" cy="105" r="2" fill="white"/></g>
 <ellipse cx="93" cy="123" rx="10" ry="5" fill="#ecaaa2"/><ellipse cx="167" cy="123" rx="10" ry="5" fill="#ecaaa2"/>
 <path class="lumi-smile" d="M120 122q10 12 20 0" fill="none" stroke="#163e3b" stroke-width="3" stroke-linecap="round"/>
 ${s===1?'<path d="m73 139 19-10 16 13 19-11 18 12 19-14 23 10-6 31q-8 33-51 28-43 5-51-28Z" fill="#fff4db" stroke="#ceb98b" stroke-width="3"/><path d="m110 160 9 7-6 11" fill="none" stroke="#dbc79e" stroke-width="3"/>':'<ellipse cx="95" cy="179" rx="19" ry="10" fill="#247c6a"/><ellipse cx="165" cy="179" rx="19" ry="10" fill="#247c6a"/>'}
 ${s>=2&&s<5?`<path d="M130 68V46M130 57Q102 56 110 35Q132 35 130 57${s>=3?'M130 53Q151 26 159 43Q152 61 130 57':''}" fill="#b0db7e" stroke="#4b8d57" stroke-width="3" stroke-linecap="round"/>`:''}
 </g></svg>`;
}

export function mountPet(user){
 const host=document.querySelector('#pet');
 if(!host)return {apply:()=>false,reload:()=>{}};
 let pet=null,request=0,animationTimer;
 const key=`planifia-pet-event-${user.id}`;
 function render(){
  const p=pet,maximum=p.currentLevel===p.maxLevel;
  host.classList.remove('pet-loading');host.setAttribute('aria-busy','false');
  host.innerHTML=`<div class="pet-portrait">${portrait(p.evolutionStage)}</div><div class="pet-info">
   <p class="eyebrow">TU COMPAÑERA DE ESTUDIO</p><div class="pet-title"><h2>${e(p.name)}</h2><span class="pet-level">Nivel ${p.currentLevel}</span></div>
   <p class="pet-stage">${e(p.stageName)} <span>· ${p.totalXp} XP en total</span></p>
   <div class="pet-xp-label"><span>${maximum?'Evolución final alcanzada':`${p.levelXp} / ${p.nextLevelXp} XP`}</span><span>${maximum?'Nivel máximo':`Nivel ${p.currentLevel+1}`}</span></div>
   <progress aria-label="Experiencia para el siguiente nivel" max="${maximum?1:p.nextLevelXp}" value="${maximum?1:p.levelXp}"></progress>
   <p class="pet-message" role="status">${p.totalXp===0?'Cada comienzo cuenta. Completa una tarea y creceremos juntos.':'A tu ritmo, cada paso cuenta. Aquí seguimos juntos.'}</p>
   </div><div class="pet-journey"><p>UN POCO MÁS LEJOS, JUNTOS</p><ol>${p.evolutions.map(({level:l,name},i)=>`<li class="${p.currentLevel>=l?'reached':''}" ${p.evolutionStage===i+1?'aria-current="step"':''}><span>${p.currentLevel>=l?'✓':l}</span><small>${e(name)}</small><em>Nv. ${l}</em></li>`).join('')}</ol></div>`;
 }
 function animate(change){
  const evolving=change.stagesGained?.length>0,leveling=change.levelsGained?.length>0;
  const message=evolving?`¡Nueva evolución: ${pet.stageName}! Alcanzaste el nivel ${pet.currentLevel}.`:leveling?`¡Nivel ${pet.currentLevel}! ${pet.name} crece contigo.`:`¡Bien hecho! +${change.xpDelta} XP para ${pet.name}.`;
  host.querySelector('.pet-message').textContent=message;
  host.classList.remove('pet-happy','pet-evolving','pet-level-up');
  void host.offsetWidth;
  host.classList.add(evolving?'pet-evolving':leveling?'pet-level-up':'pet-happy');
  clearTimeout(animationTimer);
  animationTimer=setTimeout(()=>host.classList.remove('pet-happy','pet-evolving','pet-level-up'),1800);
  toast(message);
 }
 async function reload(){
  const version=++request;host.setAttribute('aria-busy','true');
  try{
   const result=await api('/mascota');if(version!==request)return;
   pet=result;render();
   if(document.body.dataset.page==='dashboard'){
    try{const saved=JSON.parse(sessionStorage.getItem(key));sessionStorage.removeItem(key);
     if(saved&&Date.now()-saved.time<60000&&saved.change.pet.totalXp===pet.totalXp)animate(saved.change);
    }catch{}
   }
  }catch(error){
   if(version!==request)return;
   host.setAttribute('aria-busy','false');
   host.innerHTML='<div class="pet-unavailable"><h2>Lumi te espera</h2><p>Ahora no pudimos cargar su progreso. Tus tareas siguen disponibles.</p><button class="secondary" type="button">Volver a intentar</button></div>';
   host.querySelector('button').onclick=reload;
  }
 }
 function apply(change){
  if(!change?.pet){reload();return false;}
  ++request;pet=change.pet;render();
  try{sessionStorage.removeItem(key);}catch{}
  if(change.xpDelta>0){
   try{sessionStorage.setItem(key,JSON.stringify({change,time:Date.now()}));}catch{}
   animate(change);return true;
  }
  if(change.xpDelta<0){toast(`Tarea reabierta: se ajustaron ${-change.xpDelta} XP. Puedes retomarla cuando quieras.`);return true;}
  return false;
 }
 reload();
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)reload();});
 return {apply,reload};
}
