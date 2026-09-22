"""Crea las tablas de PlanifIA en DB_NAME con las credenciales de .env."""
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import pymysql
from backend.config import DB
from backend.database import check_schema, connect


def initialize(create_database=False):
    with connect(database=None if create_database else DB['database'],
                 autocommit=True,read_timeout=30,write_timeout=30) as connection:
        with connection.cursor() as cursor:
            if create_database:
                name='`'+DB['database'].replace('`','``')+'`'
                cursor.execute(f'CREATE DATABASE IF NOT EXISTS {name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
                connection.select_db(DB['database'])
            for statement in (ROOT/'database'/'planifia.sql').read_text(encoding='utf8').split(';'):
                if statement.strip():
                    cursor.execute(statement)
            check_schema(cursor)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crear-base',action='store_true',help='Crear también DB_NAME si no existe; requiere permiso CREATE DATABASE.')
    args=parser.parse_args()
    try:
        initialize(args.crear_base)
    except pymysql.MySQLError as error:
        code=error.args[0] if error.args else 'desconocido'
        if code in (1044,1045,1142,1143):
            detail='Revisa las credenciales y los permisos CREATE y REFERENCES sobre DB_NAME.'
        elif code==1049:
            detail='DB_NAME no existe. Usa una base asignada o ejecuta con --crear-base si tienes permiso.'
        else:
            detail='Revisa la conexión y la estructura existente antes de repetir el comando.'
        raise SystemExit(f'No se pudieron preparar las tablas (MySQL {code}). {detail}')
    print('Tablas de PlanifIA listas en la base configurada en DB_NAME. Los datos existentes se conservan.')


if __name__=='__main__':
    main()
