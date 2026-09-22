import {api,$,init,escapeHTML as e,dateLabel,empty,showError} from './app.js';
async function load(){const user=await init();if(!user)return;try{const data=await api('/dashboard');$('#greeting').textContent=`Hola, ${user.nombre.split(' ')[0]} ☀`;
$('#today-label').textContent=dateLabel(data.hoy,{weekday:'long',day:'numeric',month:'long'});
const stats=[['Tareas pendientes',data.pendientes,'Por avanzar',''],['Pruebas esta semana',data.pruebas_semana,'En los próximos 7 días',''],['Tareas atrasadas',data.atrasadas,'Revisa su fecha','warning'],['Notificaciones nuevas',data.no_leidas,'Tus recordatorios','']];
$('#stats').innerHTML=stats.map(([label,n,detail,cls])=>`<article class="stat ${cls}"><div class="stat-header">${label}</div><p class="stat-value">${n}</p><small>${detail}</small></article>`).join('');
$('#week').innerHTML=data.semana.map((d,i)=>`<div class="day ${i===0?'today':''}">${e(dateLabel(d.fecha,{weekday:'short'}))}<strong>${Number(d.fecha.slice(8,10))}</strong><small>${d.actividades} act.</small></div>`).join('');
$('#upcoming').innerHTML=data.proximos.length?data.proximos.map(x=>`<a class="list-row" href="${x.tipo==='tarea'?'tareas':'evaluaciones'}.html"><div class="date-block">${e(dateLabel(x.fecha,{month:'short'}))}<strong>${Number(x.fecha.slice(8,10))}</strong></div><div class="row-body"><h3>${e(x.nombre)}</h3><p>${e(x.asignatura)} · ${x.tipo==='tarea'?'Tarea':'Prueba'}${x.fecha<data.hoy?' · Atrasada':''}</p></div><span class="tag ${e(x.prioridad)}">${e(x.prioridad)}</span></a>`).join(''):empty('Todo despejado','Agrega tus primeras actividades para verlas aquí.','<a class="text-link" href="tareas.html?nueva=1">Crear una tarea →</a>');
$('#reminders').innerHTML=data.notificaciones.length?data.notificaciones.map(n=>`<div class="list-row"><div class="row-body"><h3>${e(n.titulo)}</h3><p>${e(n.mensaje)}</p></div></div>`).join(''):'<p class="muted">No tienes recordatorios nuevos.</p>';
const total=data.pendientes+data.completadas;$('#progress-label').textContent=`${data.completadas} de ${total}`;$('#progress').max=total||1;$('#progress').value=data.completadas;
}catch(error){showError(error);}}
load();
