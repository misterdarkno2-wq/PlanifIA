import {isNative,invoke} from './connection.js';
import {$,showError,clearError} from './app.js';

const button=$('#connect'),status=$('#connection-status');
if(isNative){
 invoke('get_server').then(server=>{$('#server-url').value=server;button.disabled=false;status.textContent='Puedes comprobar la conexión o cambiar de servidor.';})
 .catch(error=>{status.textContent='No se pudo leer la configuración.';showError(new Error(String(error)),'#form-error');});
}else{status.textContent='En el navegador ya estás conectado al servidor de esta página.';$('#server-url').disabled=true;}
$('#server-form').addEventListener('submit',async event=>{
 event.preventDefault();if(!isNative)return;clearError('#form-error');button.disabled=true;status.textContent='Comprobando la conexión…';
 try{await invoke('set_server',{server:$('#server-url').value});sessionStorage.clear();status.textContent='Conectado. Abriendo tu cuenta…';location.replace('login.html');}
 catch(error){status.textContent='Se ha conservado tu conexión anterior.';showError(new Error(String(error)),'#form-error');}
 finally{button.disabled=false;}
});
