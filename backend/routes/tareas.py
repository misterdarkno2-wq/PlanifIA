from fastapi import APIRouter, Depends, HTTPException
from backend.database import query, transaction
from backend.models.schemas import Tarea, Estado
from backend.security import usuario_actual
router=APIRouter(prefix='/api/tareas',tags=['Tareas'])
FIELDS=['asignatura', 'descripcion', 'prioridad', 'dificultad', 'tiempo_estimado', 'titulo', 'fecha_entrega', 'estado']

@router.get('')
def listar(user=Depends(usuario_actual)):
    return query('SELECT * FROM tareas WHERE usuario_id=%s ORDER BY fecha_entrega,id',(user['id'],))

@router.post('',status_code=201)
def crear(data:Tarea,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('INSERT INTO tareas (usuario_id,asignatura,descripcion,prioridad,dificultad,tiempo_estimado,titulo,fecha_entrega,estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (user['id'],)+tuple(getattr(data,f) for f in FIELDS))
        return {'id':cur.lastrowid}

@router.put('/{item_id}')
def editar(item_id:int,data:Tarea,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('SELECT id FROM tareas WHERE id=%s AND usuario_id=%s FOR UPDATE',(item_id,user['id']))
        if not cur.fetchone(): raise HTTPException(404,'Actividad no encontrada.')
        cur.execute('UPDATE tareas SET asignatura=%s,descripcion=%s,prioridad=%s,dificultad=%s,tiempo_estimado=%s,titulo=%s,fecha_entrega=%s,estado=%s WHERE id=%s AND usuario_id=%s',
            tuple(getattr(data,f) for f in FIELDS)+(item_id,user['id']))
        cur.execute('DELETE FROM notificaciones WHERE usuario_id=%s AND clave LIKE %s',(user['id'],'tareas:'+str(item_id)+':%'))
    return {'mensaje':'Actividad actualizada.'}

@router.delete('/{item_id}',status_code=204)
def eliminar(item_id:int,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('DELETE FROM tareas WHERE id=%s AND usuario_id=%s',(item_id,user['id']))
        if not cur.rowcount: raise HTTPException(404,'Actividad no encontrada.')
        cur.execute('DELETE FROM notificaciones WHERE usuario_id=%s AND clave LIKE %s',(user['id'],'tareas:'+str(item_id)+':%'))

@router.patch('/{item_id}/estado')
def estado(item_id:int,data:Estado,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('SELECT id FROM tareas WHERE id=%s AND usuario_id=%s FOR UPDATE',(item_id,user['id']))
        if not cur.fetchone(): raise HTTPException(404,'Tarea no encontrada.')
        cur.execute('UPDATE tareas SET estado=%s WHERE id=%s AND usuario_id=%s',(data.estado,item_id,user['id']))
        cur.execute('DELETE FROM notificaciones WHERE usuario_id=%s AND clave LIKE %s',(user['id'],'tareas:'+str(item_id)+':%'))
    return {'mensaje':'Estado actualizado.'}
