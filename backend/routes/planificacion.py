import json
from threading import Lock
from fastapi import APIRouter,Depends,HTTPException
from backend.config import local_now
from backend.database import query,execute,transaction
from backend.models.schemas import Disponibilidad
from backend.security import usuario_actual
from backend.services import ollama_service
router=APIRouter(prefix='/api',tags=['Planificación IA'])
_busy=set();_lock=Lock()

@router.get('/disponibilidad')
def obtener_disponibilidad(user=Depends(usuario_actual)):
    row=query('SELECT datos FROM disponibilidad WHERE usuario_id=%s',(user['id'],),one=True)
    return json.loads(row['datos']) if row else None

@router.put('/disponibilidad')
def guardar_disponibilidad(data:Disponibilidad,user=Depends(usuario_actual)):
    execute('INSERT INTO disponibilidad (usuario_id,datos) VALUES (%s,%s) ON DUPLICATE KEY UPDATE datos=%s',
        (user['id'],data.model_dump_json(),data.model_dump_json()))
    return {'mensaje':'Disponibilidad guardada.'}

@router.post('/planes/generar',status_code=201)
def generar(user=Depends(usuario_actual)):
    uid=user['id']
    with _lock:
        if uid in _busy: raise HTTPException(409,'Ya estamos generando tu plan. Espera un momento.')
        _busy.add(uid)
    try:
        row=query('SELECT datos FROM disponibilidad WHERE usuario_id=%s',(uid,),one=True)
        if not row: raise HTTPException(422,'Guarda primero tu disponibilidad de estudio.')
        availability=Disponibilidad.model_validate_json(row['datos'])
        tasks=query("SELECT id,titulo,asignatura,descripcion,fecha_entrega,prioridad,dificultad,tiempo_estimado FROM tareas WHERE usuario_id=%s AND estado='pendiente' ORDER BY fecha_entrega,id",(uid,))
        exams=query('SELECT id,nombre,asignatura,descripcion,fecha,prioridad,dificultad,tiempo_estimado FROM evaluaciones WHERE usuario_id=%s AND fecha>=%s ORDER BY fecha,id',(uid,local_now().date()))
        content,model=ollama_service.generate(availability,tasks,exams)
        pid=execute('INSERT INTO planes_estudio (usuario_id,contenido,modelo) VALUES (%s,%s,%s)',(uid,json.dumps(content,ensure_ascii=False),model))
        return {'id':pid,'contenido':content,'modelo':model,'guardado':False}
    finally:
        with _lock:_busy.discard(uid)

@router.get('/planes')
def listar(user=Depends(usuario_actual)):
    rows=query('SELECT id,modelo,fecha_generacion FROM planes_estudio WHERE usuario_id=%s AND guardado=TRUE ORDER BY id DESC',(user['id'],))
    return rows

@router.get('/planes/{plan_id}')
def obtener(plan_id:int,user=Depends(usuario_actual)):
    row=query('SELECT * FROM planes_estudio WHERE id=%s AND usuario_id=%s',(plan_id,user['id']),one=True)
    if not row: raise HTTPException(404,'Plan no encontrado.')
    row['contenido']=json.loads(row['contenido']);return row

@router.post('/planes/{plan_id}/guardar')
def guardar(plan_id:int,user=Depends(usuario_actual)):
    with transaction() as cur:
        cur.execute('SELECT id,guardado FROM planes_estudio WHERE id=%s AND usuario_id=%s FOR UPDATE',(plan_id,user['id']))
        row=cur.fetchone()
        if not row: raise HTTPException(404,'Plan no encontrado.')
        if not row['guardado']:
            cur.execute('UPDATE planes_estudio SET guardado=TRUE WHERE id=%s AND usuario_id=%s',(plan_id,user['id']))
            cur.execute("DELETE FROM notificaciones WHERE usuario_id=%s AND tipo='plan'",(user['id'],))
    return {'mensaje':'Plan guardado. Puedes consultarlo cuando quieras.'}
