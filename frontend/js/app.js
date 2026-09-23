import {isNative,request} from './connection.js';
export const $=(q,root=document)=>root.querySelector(q);
if(isNative){
 document.documentElement.classList.add('native');
 const slot=$('.topbar-title')||$('.auth-small');
 if(slot){const link=document.createElement('a');link.href='servidor.html';link.className='text-link connection-link';link.textContent='Conexión';slot.append(document.createElement('br'),link);}
}
export const escapeHTML=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function dateLabel(value,options={day:'numeric',month:'short'}) {return new Intl.DateTimeFormat('es-CL',options).format(new Date(String(value).slice(0,10)+'T12:00:00'));}
export async function api(path,options={}) {
 const {status,data}=await request(path,options);
 if(status<200||status>=300){if(status===401&&!path.startsWith('/auth/'))location.href='login.html';const error=new Error(data?.detail||'No pudimos completar la solicitud. Inténtalo nuevamente.');error.status=status;throw error;}
 return data;
}
export function showError(error,selector='#page-error'){const el=$(selector);if(el){el.textContent=error.message;el.hidden=false;}else toast(error.message,true);}
export function clearError(selector='#page-error'){const el=$(selector);if(el)el.hidden=true;}
let toastTimer;
export function toast(text,error=false){const el=$('#toast');if(!el)return;clearTimeout(toastTimer);el.textContent=text;el.className='toast'+(error?' error-toast':'');el.hidden=false;toastTimer=setTimeout(()=>el.hidden=true,5000);}
const paths={grid:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',check:'M9 11l3 3 8-9 M20 13v7H4V4h11',book:'M12 5v15 M3 4c4-1 7 0 9 2 2-2 5-3 9-2v15c-4-1-7 0-9 2-2-2-5-3-9-2z',spark:'M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z',bell:'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M9 21h6'};
export function icons(){document.querySelectorAll('[data-icon]').forEach(el=>{el.innerHTML=`<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[el.dataset.icon]||paths.grid}"/></svg>`;});}
export async function bell(){try{const n=await api('/notificaciones');$('#bell-count').textContent=n.no_leidas;return n;}catch(error){showError(error);}}
export async function init({notifications=true}={}){icons();try{const user=await api('/auth/me');$('#user-name').textContent=user.nombre;$('#avatar').textContent=user.nombre.slice(0,1).toUpperCase();const logout=async()=>{try{await api('/auth/logout',{method:'POST'});location.href='login.html';}catch(e){showError(e);}};$('#logout').onclick=logout;$('#logout-mobile').onclick=logout;if(notifications){bell();setInterval(()=>{if(!document.hidden)bell();},60000);}return user;}catch(error){if(error.status===401)location.href='login.html';else showError(error);return null;}}
export function empty(title,text,link=''){return `<div class="empty"><h3>${escapeHTML(title)}</h3><p>${escapeHTML(text)}</p>${link}</div>`;}
export function confirmAction(message){
 return new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='confirm-dialog';
  dialog.innerHTML='<form method="dialog"><h2>Eliminar actividad</h2><p></p><div class="actions"><button value="cancel" class="secondary" autofocus>Cancelar</button><button value="delete" class="danger">Eliminar</button></div></form>';
  $('p',dialog).textContent=message;dialog.addEventListener('close',()=>{const accepted=dialog.returnValue==='delete';dialog.remove();resolve(accepted);},{once:true});
  document.body.append(dialog);dialog.showModal();
 });
}
