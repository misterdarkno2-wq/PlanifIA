"""Recordatorios futuros para programar en Android, sin modificar la bandeja web."""
import json
from datetime import datetime, time, timedelta, timezone

from backend.config import TIMEZONE
from backend.database import transaction

HORIZON_DAYS = 30
MAX_REMINDERS = 64
MORNING = time(9)
STUDY_LEAD_MINUTES = 10


def build_reminders(tasks, exams, plan, now=None):
    now = now or datetime.now(TIMEZONE)
    now = now.astimezone(TIMEZONE)
    end = now + timedelta(days=HORIZON_DAYS)
    items = []

    def add(key, title, body, at):
        if now < at <= end:
            items.append(dict(key=key, title=title, body=body,
                              at=at.astimezone(timezone.utc).isoformat()))

    pending = [row for row in tasks if row['estado'] == 'pendiente']
    for kind, rows, field, name in [('tarea', pending, 'fecha_entrega', 'titulo'),
                                     ('evaluacion', exams, 'fecha', 'nombre')]:
        for row in rows:
            for days, label in [(1, 'mañana'), (0, 'hoy')]:
                at = datetime.combine(row[field] - timedelta(days=days), MORNING, TIMEZONE)
                title = 'Entrega ' + label if kind == 'tarea' else 'Prueba ' + label
                add(f'{kind}:{row["id"]}:{at.date()}', title,
                    f'{row["asignatura"]}: {row[name]}', at)

    # Un plan guardado puede contener actividades que se completaron o eliminaron después.
    available = {('tarea', row['id']) for row in pending}
    available.update(('evaluacion', row['id']) for row in exams)
    if plan:
        content = json.loads(plan['contenido']) if isinstance(plan['contenido'], str) else plan['contenido']
        for i, block in enumerate(content['bloques']):
            if (block['tipo'], block.get('actividad_id')) not in available:
                continue
            start = datetime.fromisoformat(block['fecha'] + 'T' + block['inicio']).replace(tzinfo=TIMEZONE)
            at = start - timedelta(minutes=STUDY_LEAD_MINUTES)
            at = start if at <= now else at
            add(f'plan:{plan["id"]}:{i}', 'Tu sesión de estudio',
                f'{block["inicio"][:5]} · {block["asignatura"]}: {block["actividad"]}', at)
    return sorted(items, key=lambda item: (item['at'], item['key']))[:MAX_REMINDERS]


def scheduled_reminders(uid):
    with transaction() as cur:
        cur.execute("SELECT id,titulo,asignatura,fecha_entrega,estado FROM tareas WHERE usuario_id=%s AND estado='pendiente'", (uid,))
        tasks = cur.fetchall()
        cur.execute('SELECT id,nombre,asignatura,fecha FROM evaluaciones WHERE usuario_id=%s', (uid,))
        exams = cur.fetchall()
        cur.execute('SELECT id,contenido FROM planes_estudio WHERE usuario_id=%s AND guardado=TRUE ORDER BY id DESC LIMIT 1', (uid,))
        plan = cur.fetchone()
    return {'timezone': str(TIMEZONE), 'items': build_reminders(tasks, exams, plan)}
