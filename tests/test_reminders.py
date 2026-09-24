from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.services.mobile_reminders import build_reminders

TZ = ZoneInfo('America/Santiago')


def task(id=1, **values):
    return dict(id=id, titulo='Entregar informe', asignatura='Historia',
                fecha_entrega=date(2026, 9, 26), estado='pendiente') | values


def test_dates_are_local_mornings_with_explicit_utc_offset():
    items = build_reminders([task()], [], None, datetime(2026, 9, 24, 12, tzinfo=TZ))
    assert [item['at'] for item in items] == ['2026-09-25T12:00:00+00:00', '2026-09-26T12:00:00+00:00']
    winter = build_reminders([task(fecha_entrega=date(2026, 7, 3))], [], None,
                             datetime(2026, 7, 1, 12, tzinfo=TZ))
    assert winter[0]['at'] == '2026-07-02T13:00:00+00:00'


def test_past_completed_and_distant_tasks_produce_no_alarms():
    rows = [task(estado='completada'), task(2, fecha_entrega=date(2026, 9, 23)),
            task(3, fecha_entrega=date(2026, 12, 1))]
    assert build_reminders(rows, [], None, datetime(2026, 9, 24, 12, tzinfo=TZ)) == []


def test_study_alarms_skip_rest_and_missing_or_completed_activities():
    block = dict(fecha='2026-09-24', inicio='17:00', tipo='tarea', actividad_id=1,
                 asignatura='Historia', actividad='Repasar')
    plan = dict(id=7, contenido={'bloques': [block, block | {'tipo': 'descanso'},
                                           block | {'actividad_id': 999}]})
    items = build_reminders([task()], [], plan, datetime(2026, 9, 24, 16, tzinfo=TZ))
    assert items[0]['at'] == '2026-09-24T19:50:00+00:00'
    assert items[0]['key'] == 'plan:7:0'
    items = build_reminders([task()], [], plan, datetime(2026, 9, 24, 16, 55, tzinfo=TZ))
    assert items[0]['at'] == '2026-09-24T20:00:00+00:00'
    assert build_reminders([task(estado='completada')], [], plan, datetime(2026, 9, 24, 16, tzinfo=TZ)) == []


def test_exam_reminders_and_bounded_repeatable_result():
    exam = dict(id=1, nombre='Álgebra', asignatura='Matemática', fecha=date(2026, 9, 25))
    now = datetime(2026, 9, 24, 12, tzinfo=TZ)
    items = build_reminders([], [exam], None, now)
    assert len(items) == 1 and items[0]['title'] == 'Prueba hoy'
    rows = [task(i) for i in range(100)]
    a = build_reminders(rows, [exam], None, now)
    assert len(a) == 64
    assert a == build_reminders(list(reversed(rows)), [exam], None, now)


def test_endpoint_requires_session():
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        assert client.get('/api/notificaciones/programadas').status_code == 401
