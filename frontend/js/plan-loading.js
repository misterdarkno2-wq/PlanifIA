import {portrait} from './pet.js';

export function startPlanLoading(host,{dias,minutos_diarios,descansos},stage=2){
 const started=performance.now();
 host.setAttribute('aria-busy','true');
 host.innerHTML=`<section class="plan-loading" aria-labelledby="plan-loading-title">
  <div class="plan-loading-top"><span class="plan-loading-badge"><span></span> Preparando tu semana</span><span class="plan-loading-time" aria-hidden="true">0:00</span></div>
  <div class="plan-loading-lumi" aria-hidden="true">${portrait(stage)}<span class="plan-loading-spark">✧</span></div>
  <h3 id="plan-loading-title">Un espacio para cada pendiente</h3>
  <p class="plan-loading-description">Estamos preparando objetivos de estudio que encajen con tus horarios. Lumi te acompaña mientras tanto.</p>
  <div class="plan-loading-chips"><span class="loading-days"></span><span class="loading-minutes"></span><span class="loading-breaks"></span></div>
  <div class="plan-loading-track" role="progressbar" aria-label="Generando tu plan de estudio"><span></span></div>
  <ol class="plan-loading-steps"><li class="done"><span>✓</span>Horarios guardados</li><li class="active" aria-current="step"><span>✧</span>Preparando el plan</li><li><span>3</span>Listo para revisar</li></ol>
  <div class="plan-loading-preview" aria-hidden="true"><div><i></i><b></b><b></b></div><div><i></i><b></b><b></b></div><div><i></i><b></b><b></b></div></div>
  <p class="plan-loading-note" role="status">La primera vez puede tardar un poco más. Mantén esta pantalla abierta.</p>
 </section>`;
 host.querySelector('.loading-days').textContent=`${dias.length} ${dias.length===1?'día disponible':'días disponibles'}`;
 host.querySelector('.loading-minutes').textContent=`${minutos_diarios} min al día`;
 host.querySelector('.loading-breaks').textContent=descansos?'Con pausas':'A tu ritmo';
 const elapsed=host.querySelector('.plan-loading-time'),note=host.querySelector('.plan-loading-note');
 let slow=false;
 const timer=setInterval(()=>{
  const seconds=Math.floor((performance.now()-started)/1000);
  elapsed.textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
  if(seconds>=45&&!slow){slow=true;note.textContent='Está tardando un poco más. Seguimos esperando tu plan; no necesitas volver a pulsar Generar.';}
 },1000);
 return ()=>{clearInterval(timer);host.setAttribute('aria-busy','false');};
}
