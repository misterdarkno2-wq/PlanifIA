from collections import Counter
from datetime import timedelta
from fastapi import APIRouter,Depends
from backend.config import local_now
from backend.security import usuario_actual
from backend.database import transaction
from backend.services.notification_service import refresh_notifications
router=APIRouter(prefix='/api/dashboard',tags=['Dashboard'])

@router.get('')
def dashboard(user=Depends(usuario_actual)):
    uid=user['id'];today=local_now().date();end=today+timedelta(days=6)
    refresh_notifications(uid)
    with transaction() as cur:
        cur.execute('SELECT titulo,asignatura,fecha_entrega,prioridad,estado FROM tareas WHERE usuario_id=%s ORDER BY fecha_entrega,id',(uid,))
        tasks=cur.fetchall()
        cur.execute('SELECT nombre,asignatura,fecha,prioridad FROM evaluaciones WHERE usuario_id=%s AND fecha>=%s ORDER BY fecha,id',(uid,today))
        exams=cur.fetchall()
        cur.execute('SELECT COUNT(*) AS total FROM notificaciones WHERE usuario_id=%s AND leida=FALSE',(uid,))
        unread=cur.fetchone()['total']
        cur.execute('SELECT titulo,mensaje,fecha_programada FROM notificaciones WHERE usuario_id=%s AND leida=FALSE ORDER BY fecha_programada DESC LIMIT 3',(uid,))
        notifications=cur.fetchall()
    pending=[t for t in tasks if t['estado']=='pendiente']
    upcoming=[dict(tipo='tarea',nombre=t['titulo'],asignatura=t['asignatura'],fecha=t['fecha_entrega'],prioridad=t['prioridad']) for t in pending]
    upcoming += [dict(tipo='evaluacion',nombre=e['nombre'],asignatura=e['asignatura'],fecha=e['fecha'],prioridad=e['prioridad']) for e in exams]
    upcoming.sort(key=lambda x:x['fecha'])
    by_day=Counter(item['fecha'] for item in upcoming)
    return {'usuario':user,'hoy':today,'pendientes':len(pending),'atrasadas':sum(t['fecha_entrega']<today for t in pending),
        'pruebas_semana':sum(e['fecha']<=end for e in exams),'no_leidas':unread,'completadas':len(tasks)-len(pending),
        'proximos':upcoming[:8],'notificaciones':notifications,
        'semana':[{'fecha':day,'actividades':by_day[day]} for day in (today+timedelta(days=i) for i in range(7))]}
