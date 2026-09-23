"""El saldo y la recompensa se actualizan con el mismo cursor que la tarea."""
from backend import pet_config as config
from backend.config import local_now


def progression(total):
    level, floor = 1, 0
    while level < config.MAX_LEVEL:
        required = config.FIRST_LEVEL_XP + (level - 1) * config.LEVEL_INCREMENT
        if total < floor + required:
            break
        floor += required
        level += 1
    stage = max(i for i, (minimum, _) in enumerate(config.STAGES) if level >= minimum)
    required = None if level == config.MAX_LEVEL else config.FIRST_LEVEL_XP + (level - 1) * config.LEVEL_INCREMENT
    return {'currentLevel': level, 'evolutionStage': stage + 1,
            'stageName': config.STAGES[stage][1], 'levelXp': total - floor,
            'nextLevelXp': required, 'maxLevel': config.MAX_LEVEL}


def reward(priority, deadline, today):
    return config.BASE_XP[priority] + (config.EARLY_BONUS if today < deadline else 0)


def lock_pet(cursor, uid):
    # El mismo orden de bloqueo serializa las tareas de una cuenta.
    cursor.execute('INSERT INTO mascotas (usuario_id,nombre) VALUES (%s,%s) ON DUPLICATE KEY UPDATE id=id', (uid, config.DEFAULT_NAME))
    cursor.execute('SELECT * FROM mascotas WHERE usuario_id=%s FOR UPDATE', (uid,))
    return cursor.fetchone()


def public_pet(row):
    return {'id': row['id'], 'userId': row['usuario_id'], 'name': row['nombre'],
            'totalXp': row['total_xp'], 'createdAt': row['created_at'], 'updatedAt': row['updated_at'],
            'evolutions': [{'level': level, 'name': name} for level, name in config.STAGES],
            **progression(row['total_xp'])}


def apply_transition(cursor, pet, task, target):
    before = progression(pet['total_xp'])
    delta = 0
    if task['estado'] != target:
        if target == 'completada' and not task['xp_activa']:
            # Conserva el primer importe aunque se editen prioridad o fecha después.
            amount = task['xp_otorgada'] or reward(task['prioridad'], task['fecha_entrega'], local_now().date())
            cursor.execute('UPDATE tareas SET xp_otorgada=%s,xp_activa=TRUE,xp_otorgada_en=COALESCE(xp_otorgada_en,CURRENT_TIMESTAMP),xp_revocada_en=NULL WHERE id=%s', (amount, task['id']))
            delta = amount
        elif target == 'pendiente' and task['xp_activa']:
            cursor.execute('UPDATE tareas SET xp_activa=FALSE,xp_revocada_en=CURRENT_TIMESTAMP WHERE id=%s', (task['id'],))
            delta = -task['xp_otorgada']
    if delta:
        pet['total_xp'] += delta
        cursor.execute('UPDATE mascotas SET total_xp=%s WHERE usuario_id=%s', (pet['total_xp'], pet['usuario_id']))
    cursor.execute('SELECT * FROM mascotas WHERE usuario_id=%s', (pet['usuario_id'],))
    result = public_pet(cursor.fetchone())
    return {'xpDelta': delta, 'pet': result,
            'levelsGained': list(range(before['currentLevel'] + 1, result['currentLevel'] + 1)),
            'stagesGained': list(range(before['evolutionStage'] + 1, result['evolutionStage'] + 1))}
