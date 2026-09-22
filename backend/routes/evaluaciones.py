from fastapi import APIRouter, Depends, HTTPException
from backend.database import query, transaction
from backend.models.schemas import Evaluacion
from backend.security import usuario_actual
router=APIRouter(prefix='/api/evaluaciones',tags=['Evaluaciones'])
FIELDS=['asignatura', 'descripcion', 'prioridad', 'dificultad', 'tiempo_estimado', 'nombre', 'fecha']

@router.get('')
def listar(user=Depends(usuario_actual)):
    return query('SELECT * FROM evaluaciones WHERE usuario_id=%s ORDER BY fecha,id',(user['id'],))

@router.post('',status_code=201)
def crear(data:Evaluacion,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('INSERT INTO evaluaciones (usuario_id,asignatura,descripcion,prioridad,dificultad,tiempo_estimado,nombre,fecha) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            (user['id'],)+tuple(getattr(data,f) for f in FIELDS))
        return {'id':cur.lastrowid}

@router.put('/{item_id}')
def editar(item_id:int,data:Evaluacion,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('SELECT id FROM evaluaciones WHERE id=%s AND usuario_id=%s FOR UPDATE',(item_id,user['id']))
        if not cur.fetchone(): raise HTTPException(404,'Actividad no encontrada.')
        cur.execute('UPDATE evaluaciones SET asignatura=%s,descripcion=%s,prioridad=%s,dificultad=%s,tiempo_estimado=%s,nombre=%s,fecha=%s WHERE id=%s AND usuario_id=%s',
            tuple(getattr(data,f) for f in FIELDS)+(item_id,user['id']))
        cur.execute('DELETE FROM notificaciones WHERE usuario_id=%s AND clave LIKE %s',(user['id'],'evaluaciones:'+str(item_id)+':%'))
    return {'mensaje':'Actividad actualizada.'}

@router.delete('/{item_id}',status_code=204)
def eliminar(item_id:int,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('DELETE FROM evaluaciones WHERE id=%s AND usuario_id=%s',(item_id,user['id']))
        if not cur.rowcount: raise HTTPException(404,'Actividad no encontrada.')
        cur.execute('DELETE FROM notificaciones WHERE usuario_id=%s AND clave LIKE %s',(user['id'],'evaluaciones:'+str(item_id)+':%'))
