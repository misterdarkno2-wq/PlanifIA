"""Una transacción por operación. Nunca se concatenan datos dentro del SQL."""
from contextlib import contextmanager
import socket
import pymysql
from backend.config import DB, DB_IPV4

TABLES=('usuarios','sesiones','tareas','evaluaciones','disponibilidad','planes_estudio','notificaciones','mascotas')


def connect(**overrides):
    options=dict(DB,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor,
                 autocommit=False,connect_timeout=5,read_timeout=10,write_timeout=10)
    options.update(overrides)
    if DB_IPV4:
        try:
            options['host']=socket.gethostbyname(options['host'])
        except socket.gaierror as error:
            raise pymysql.err.OperationalError(2003,'No se pudo resolver el host MySQL por IPv4.') from error
    return pymysql.connect(**options)


def check_schema(cursor):
    cursor.execute('SELECT TABLE_NAME AS nombre FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()')
    existing={row['nombre'] for row in cursor.fetchall()}
    missing=set(TABLES)-existing
    if missing:
        raise pymysql.err.ProgrammingError(1146,'Faltan tablas de PlanifIA: '+', '.join(sorted(missing)))

@contextmanager
def transaction():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def query(sql, params=(), *, one=False):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone() if one else cursor.fetchall()

def execute(sql, params=()):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid
