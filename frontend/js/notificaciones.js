import {api,$,init,escapeHTML as e,empty,showError,clearError,toast} from './app.js';
import {mobileReminders} from './mobile-notifications.js';

if(mobileReminders){
 const panel=document.createElement('section');panel.className='card mobile-reminders';
 panel.setAttribute('aria-labelledby','mobile-reminder-title');
 panel.innerHTML='<p class="eyebrow">EN TU TELÉFONO</p><h2 id="mobile-reminder-title">Que no se te pase</h2><p>Recibe avisos en la bandeja de Android, incluso con la app cerrada.</p><p class="muted">Entregas y pruebas: a las 9:00 del día anterior y del mismo día. Estudio: 10 minutos antes, según la zona horaria del planificador.</p><p id="reminder-status" role="status" aria-live="polite">Cargando preferencias…</p><div class="actions"><button id="enable-reminders" disabled>Activar avisos</button><button id="test-reminders" class="secondary" disabled>Probar aviso</button><button id="disable-reminders" class="ghost" disabled>Desactivar</button></div><p class="muted reminder-note">Abre la app para sincronizar los cambios de otros dispositivos. Android puede retrasar avisos por ahorro de batería; forzar la detención impide recibirlos hasta volver a abrirla.</p>';
 $('.page-heading').after(panel);
 let busy=false;
 const render=()=>{
  const state=mobileReminders.status();
  $('#reminder-status').textContent=state.error||(state.enabled?(state.lastSync?`${state.count} ${state.count===1?'aviso programado':'avisos programados'} · Actualizado ${new Date(state.lastSync).toLocaleString('es-CL')}`:'Activados. Falta sincronizar los próximos avisos.'):'Los avisos del teléfono están desactivados.');
  $('#enable-reminders').textContent=state.enabled?'Sincronizar avisos':'Activar avisos';
  $('#enable-reminders').disabled=busy||!state.owner;
  $('#test-reminders').disabled=busy||!state.enabled;
  $('#disable-reminders').disabled=busy||!state.enabled;
 };
 const run=async operation=>{busy=true;render();try{await operation();}catch(error){toast(String(error?.message||error),true);}finally{busy=false;render();}};
 $('#enable-reminders').onclick=()=>run(()=>mobileReminders.status().enabled?mobileReminders.sync():mobileReminders.enable());
 $('#disable-reminders').onclick=()=>run(()=>mobileReminders.stop());
 $('#test-reminders').onclick=()=>run(async()=>{await mobileReminders.test();toast('Aviso de prueba programado en unos 10 segundos. Puedes dejar la app en segundo plano.');});
 document.addEventListener('reminderschange',render);
}
async function load(){clearError();try{const data=await api('/notificaciones');$('#bell-count').textContent=data.no_leidas;$('#notification-title').textContent=`${data.no_leidas} sin leer`;$('#notifications').innerHTML=data.items.length?data.items.map(n=>`<article class="notification ${n.leida?'':'unread'}"><span aria-hidden="true">${n.tipo==='plan'?'✧':'◷'}</span><div class="row-body"><h3>${e(n.titulo)}</h3><p>${e(n.mensaje)}</p><small>${e(n.fecha_programada.replace('T',' ').slice(0,16))} · ${n.leida?'Leída':'Sin leer'}</small></div>${n.leida?'':`<button class="small secondary" data-id="${n.id}">Marcar como leída</button>`}</article>`).join(''):empty('Sin recordatorios por ahora','Tus entregas y pruebas cercanas aparecerán aquí.');}catch(error){showError(error);}}
$('#refresh').onclick=load;$('#notifications').onclick=async event=>{const button=event.target.closest('button[data-id]');if(!button)return;button.disabled=true;try{await api('/notificaciones/'+button.dataset.id+'/leer',{method:'PATCH'});toast('Notificación leída.');await load();}catch(error){showError(error);button.disabled=false;}};
(async()=>{if(await init({notifications:false})){await load();setInterval(()=>{if(!document.hidden)load();},60000);}})();
