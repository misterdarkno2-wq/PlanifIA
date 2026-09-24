import {api,$,init,escapeHTML as e,dateLabel,empty,showError,clearError,toast} from './app.js';
import {startPlanLoading} from './plan-loading.js';
const form=$('#availability-form');let current=null;let generating=false;let petStage=2;
function values(){const data=Object.fromEntries(new FormData(form));return {dias:[...form.querySelectorAll('[name=dias]:checked')].map(x=>Number(x.value)),llegada:data.llegada,hasta:data.hasta,minutos_diarios:Number(data.minutos_diarios),descansos:form.elements.descansos.checked,asignaturas_dificiles:data.asignaturas_dificiles};}
function validate(data){if(!data.dias.length)throw new Error('Selecciona al menos un día.');const min=t=>Number(t.slice(0,2))*60+Number(t.slice(3,5));if(min(data.hasta)-min(data.llegada)<data.minutos_diarios)throw new Error('El tiempo diario no cabe entre tu hora de inicio y término.');}
async function saveAvailability(){if(!form.reportValidity())throw new Error('Completa tu disponibilidad.');const data=values();validate(data);await api('/disponibilidad',{method:'PUT',body:data});return data;}
form.onsubmit=async event=>{event.preventDefault();clearError('#form-error');const button=$('button[type=submit]',form);button.disabled=true;try{await saveAvailability();toast('Disponibilidad guardada.');}catch(error){showError(error,'#form-error');}finally{button.disabled=false;}};
function renderPlan(plan){current=plan;const c=plan.contenido;const days=[...new Set(c.bloques.map(x=>x.fecha))];$('#plan').innerHTML=`<p>${e(c.resumen)}</p>${c.advertencias.length?`<div class="advice"><strong>Ten en cuenta</strong><ul>${c.advertencias.map(x=>`<li>${e(x)}</li>`).join('')}</ul></div>`:''}${days.map(day=>`<section class="plan-day"><h3>${e(dateLabel(day,{weekday:'long',day:'numeric',month:'long'}))}</h3>${c.bloques.filter(x=>x.fecha===day).map(b=>`<div class="plan-block ${b.tipo==='descanso'?'rest':''}"><div class="plan-time">${e(b.inicio.slice(0,5))} – ${e(b.fin.slice(0,5))}</div><div><strong>${b.tipo==='descanso'?'Descanso':e(b.asignatura)}</strong><p>${e(b.actividad)}</p></div></div>`).join('')}</section>`).join('')}<p class="legend">Modelo: ${e(plan.modelo)}. Revisa el plan antes de seguirlo.</p>`;$('#plan-actions').hidden=!!plan.guardado;}
async function history(){const rows=await api('/planes');$('#history').innerHTML=rows.length?rows.map(p=>`<button class="history-item" data-id="${p.id}"><span>Plan #${p.id}<br><span class="muted">${e(dateLabel(p.fecha_generacion,{day:'numeric',month:'long',year:'numeric'}))}</span></span><span>→</span></button>`).join(''):'<p class="muted">Aquí aparecerán los planes que guardes.</p>';}
$('#generate').onclick=async()=>{
 if(generating)return;
 generating=true;clearError();clearError('#form-error');
 const button=$('#generate');button.disabled=true;button.textContent='Guardando horarios…';
 $('#save-plan').disabled=true;$('#history').querySelectorAll('button').forEach(b=>b.disabled=true);
 let stopLoading=null;
 try{
  const saving=saveAvailability();
  [...form.elements].forEach(element=>element.disabled=true);
  let availability;
  try{availability=await saving;}catch(error){showError(error,'#form-error');return;}
  $('#plan-actions').hidden=true;button.textContent='Preparando tu plan…';
  stopLoading=startPlanLoading($('#plan'),availability,petStage);
  const plan=await api('/planes/generar',{method:'POST'});
  stopLoading();renderPlan(plan);toast('Tu plan está listo. Revísalo y guárdalo.');
 }catch(error){
  if(current)renderPlan(current);else $('#plan').innerHTML=empty('No pudimos generar tu plan','Tu disponibilidad sigue guardada. Puedes intentarlo nuevamente.');
  showError(error);
 }finally{
  stopLoading?.();generating=false;button.disabled=false;button.textContent='✧ Generar plan';
  [...form.elements].forEach(element=>element.disabled=false);
  $('#save-plan').disabled=false;$('#history').querySelectorAll('button').forEach(b=>b.disabled=false);
 }
};
$('#save-plan').onclick=async()=>{if(!current)return;const button=$('#save-plan');button.disabled=true;try{await api('/planes/'+current.id+'/guardar',{method:'POST'});current.guardado=true;$('#plan-actions').hidden=true;toast('Plan guardado.');await history();}catch(error){showError(error);}finally{button.disabled=false;}};
$('#history').onclick=async event=>{const button=event.target.closest('button[data-id]');if(!button||generating)return;clearError();try{renderPlan(await api('/planes/'+button.dataset.id));}catch(error){showError(error);}};
(async()=>{if(!await init())return;api('/mascota').then(pet=>{petStage=pet.evolutionStage;}).catch(()=>{});try{const data=await api('/disponibilidad');if(data){for(const key of ['llegada','hasta','minutos_diarios','asignaturas_dificiles'])form.elements[key].value=data[key];form.elements.descansos.checked=data.descansos;form.querySelectorAll('[name=dias]').forEach(x=>x.checked=data.dias.includes(Number(x.value)));}await history();}catch(error){showError(error);}})();
