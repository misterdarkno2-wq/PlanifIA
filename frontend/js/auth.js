import {api,$,showError,clearError} from './app.js';
const register=document.body.dataset.page==='register';
// Si existe sesión, la entrada lleva directamente a la semana del usuario.
api('/auth/me').then(()=>location.href='dashboard.html').catch(()=>{});
if(!register&&new URLSearchParams(location.search).has('registrado')){const e=$('#form-error');e.className='success';e.textContent='Cuenta creada. Inicia sesión para comenzar.';e.hidden=false;}
$('#auth-form').addEventListener('submit',async event=>{
 event.preventDefault();clearError('#form-error');$('#form-error').className='error';
 const form=event.currentTarget;const fields=Object.fromEntries(new FormData(form));
 if(register&&fields.password!==fields.confirmar){showError(new Error('Las contraseñas no coinciden.'),'#form-error');return;}
 delete fields.confirmar;const button=$('button[type=submit]',form);button.disabled=true;
 try{await api(register?'/auth/registro':'/auth/login',{method:'POST',body:fields});location.href=register?'login.html?registrado=1':'dashboard.html';}
 catch(error){showError(error,'#form-error');}finally{button.disabled=false;}
});
