from contextlib import contextmanager

import pymysql
import pytest
from fastapi.testclient import TestClient

from backend import main, database
from backend.database import TABLES, check_schema


@pytest.mark.parametrize('code,status,message',[
    (1146,503,'faltan tablas'),
    (1054,503,'estructura'),
    (1142,503,'permisos'),
    (1049,503,'DB_NAME'),
    (2003,503,'conectar'),
    (1064,500,'operación'),
])
def test_error_mysql_identifica_la_causa_sin_exponer_datos(monkeypatch,code,status,message):
    @contextmanager
    def fail():
        raise pymysql.err.ProgrammingError(code,'detalle privado del servidor')
        yield

    monkeypatch.setattr(main,'transaction',fail)
    with TestClient(main.app) as client:
        response=client.get('/api/health')
    assert response.status_code==status
    assert message in response.json()['detail']
    assert 'detalle privado' not in response.text


def test_comprobacion_detecta_base_sin_tablas_de_la_app():
    class Cursor:
        def execute(self,sql):
            pass

        def fetchall(self):
            return [{'nombre':name} for name in self.tables]

    cursor=Cursor()
    cursor.tables=['otra_aplicacion']
    with pytest.raises(pymysql.err.ProgrammingError) as error:
        check_schema(cursor)
    assert error.value.args[0]==1146
    assert 'usuarios' in error.value.args[1]
    cursor.tables=[*TABLES,'otra_aplicacion']
    check_schema(cursor)


def test_ipv4_resuelve_el_host_sin_cambiar_la_configuracion(monkeypatch):
    original_host=database.DB['host']
    monkeypatch.setattr(database,'DB_IPV4',True)
    monkeypatch.setattr(database.socket,'gethostbyname',lambda host:'192.0.2.1')
    monkeypatch.setattr(database.pymysql,'connect',lambda **options:options)
    options=database.connect(database=None,autocommit=True)
    assert options['host']=='192.0.2.1'
    assert options['database'] is None
    assert options['autocommit'] is True
    assert database.DB['host']==original_host


def test_ipv4_informa_fallo_de_dns_como_error_de_conexion(monkeypatch):
    monkeypatch.setattr(database,'DB_IPV4',True)
    def fail(host):
        raise database.socket.gaierror('fallo de resolución')
    monkeypatch.setattr(database.socket,'gethostbyname',fail)
    with pytest.raises(pymysql.err.OperationalError) as error:
        database.connect()
    assert error.value.args[0]==2003
