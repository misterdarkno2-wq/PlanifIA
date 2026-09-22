from fastapi import APIRouter,Depends,HTTPException
from backend.database import query,transaction
from backend.security import usuario_actual
from backend.services.notification_service import refresh_notifications
router=APIRouter(prefix='/api/notificaciones',tags=['Notificaciones'])

@router.get('')
def listar(user=Depends(usuario_actual)):
    refresh_notifications(user['id'])
    items=query('SELECT * FROM notificaciones WHERE usuario_id=%s ORDER BY leida,fecha_programada DESC,id DESC',(user['id'],))
    return {'no_leidas':sum(not n['leida'] for n in items),'items':items}

@router.patch('/{item_id}/leer')
def leer(item_id:int,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('SELECT id FROM notificaciones WHERE id=%s AND usuario_id=%s FOR UPDATE',(item_id,user['id']))
        if not cur.fetchone(): raise HTTPException(404,'Notificación no encontrada.')
        cur.execute('UPDATE notificaciones SET leida=TRUE WHERE id=%s AND usuario_id=%s',(item_id,user['id']))
    return {'mensaje':'Notificación leída.'}
