from contextlib import contextmanager
from datetime import datetime, timedelta

from backend.routes import dashboard as route


def test_dashboard_cuenta_todos_los_avisos_y_muestra_solo_tres(monkeypatch):
    today=datetime(2026,9,11).date()
    task={'titulo':'Informe','asignatura':'Historia','fecha_entrega':today,'prioridad':'alta','estado':'pendiente'}
    exam={'nombre':'Prueba','asignatura':'Historia','fecha':today+timedelta(days=1),'prioridad':'media'}
    preview=[{'titulo':f'Aviso {i}','mensaje':'Mensaje','fecha_programada':datetime(2026,9,11)} for i in range(3)]

    class Cursor:
        def execute(self,sql,params):
            self.sql=sql

        def fetchall(self):
            if 'FROM tareas' in self.sql: return [task]
            if 'FROM evaluaciones' in self.sql: return [exam]
            return preview

        def fetchone(self):
            return {'total':5}

    @contextmanager
    def fake_transaction():
        yield Cursor()

    monkeypatch.setattr(route,'local_now',lambda:datetime(2026,9,11))
    monkeypatch.setattr(route,'refresh_notifications',lambda uid:None)
    monkeypatch.setattr(route,'transaction',fake_transaction)
    result=route.dashboard(user={'id':1,'nombre':'Estudiante'})
    assert result['no_leidas']==5
    assert len(result['notificaciones'])==3
    assert result['pendientes']==1
    assert result['pruebas_semana']==1
    assert result['semana'][0]['actividades']==1
    assert result['semana'][1]['actividades']==1
