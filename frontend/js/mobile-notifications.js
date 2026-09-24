import {isNative,invoke,request,getServer} from './connection.js';
import {createReminderController} from './reminder-controller.js';

export const supportsMobileNotifications=isNative&&/Android/i.test(globalThis.navigator?.userAgent||'');
export const mobileReminders=supportsMobileNotifications?createReminderController({
 bridge:invoke,request,storage:localStorage,
 onChange:state=>document.dispatchEvent(new CustomEvent('reminderschange',{detail:state}))
}):null;

export async function startReminders(user){
 if(!mobileReminders)return;
 const sync=()=>{if(!document.hidden)mobileReminders.sync().catch(()=>{});};
 document.addEventListener('visibilitychange',sync);
 setInterval(sync,5*60*1000);
 await mobileReminders.attach((await getServer())+'#'+user.id);
}
