import json
from datetime import datetime
from backend.config import local_now
from backend.database import transaction

def refresh_notifications(uid):
    """Recalcula al consultar: el navegador consulta cada minuto mientras está abierto.
    La clave única evita duplicados; cada vencimiento produce un aviso por día.
    """
    now=local_now(); today=now.date()
    with transaction() as cur:
        cur.execute("SELECT id,titulo,fecha_entrega FROM tareas WHERE usuario_id=%s AND estado='pendiente'",(uid,))
        tasks=cur.fetchall()
        cur.execute('SELECT id,nombre,fecha FROM evaluaciones WHERE usuario_id=%s AND fecha>=%s',(uid,today))
        exams=cur.fetchall()
        for table,rows,name,dt,kind in [('tareas',tasks,'titulo','fecha_entrega','tarea'),('evaluaciones',exams,'nombre','fecha','evaluacion')]:
            for row in rows:
                days=(row[dt]-today).days
                if days>2: continue
                when='está atrasada' if days<0 else ('vence hoy' if days==0 else ('vence mañana' if days==1 else 'vence en 2 días'))
                title='Tarea atrasada' if days<0 else ('Prueba cercana' if kind=='evaluacion' else 'Entrega cercana')
                insert(cur,uid,f'{table}:{row["id"]}:{today}',title,f'{row[name]} {when}.',kind,now)
        cur.execute('SELECT id,contenido FROM planes_estudio WHERE usuario_id=%s AND guardado=TRUE ORDER BY id DESC LIMIT 1',(uid,))
        plan=cur.fetchone()
        if plan:
            for i,block in enumerate(json.loads(plan['contenido'])['bloques']):
                if block['fecha']!=today.isoformat() or block['tipo']=='descanso': continue
                scheduled=datetime.fromisoformat(block['fecha']+'T'+block['inicio'])
                if scheduled<=now:
                    insert(cur,uid,f'plan:{plan["id"]}:{i}','Sesión de estudio',block['asignatura']+': '+block['actividad'],'plan',scheduled)

def insert(cur,uid,key,title,message,kind,scheduled):
    cur.execute('INSERT INTO notificaciones (usuario_id,clave,titulo,mensaje,tipo,fecha_programada) VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE id=id',
        (uid,key,title,message,kind,scheduled))
