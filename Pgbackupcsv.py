import psycopg
import csv
import os
from typing import Dict, Any
from datetime import datetime
from psycopg.rows import dict_row

DB_CONFING = {
    "host": "localhost",
    "user": "postgres",
    "port": 5432,
    "dbname": "name_of_your_database",
    "password": "your_password"
}

def query(sql: str) -> Dict[str, Any]:
    with psycopg.connect(**DB_CONFING, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


#Экспорт данных таблицы в csv файл
def export_to_csv(table_name, filename: str) -> int:
    sql = f'SELECT * FROM {table_name};'
    data = query(sql)
    if not data:
        return 0
    headers = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    return len(data)



#Экспорт все БД в csv файлы, каждый файл соответствует одной таблице
def export_all_db_csv(db_config: Dict[str, Any], timestamp: str, path_: str) -> int:
    DB_CONFING.update(db_config)
    dir_name = f'{DB_CONFING["dbname"]}_export_csv_{timestamp}'
    dir_path = os.path.join(path_, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    
    sql = f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_catalog = '{DB_CONFING["dbname"]}';
    """
    tables = query(sql)
    total_rows = 0
    for table in tables:
        table_name = table['table_name']
        filename = f"{table_name}.csv"
        full_filepath = os.path.join(dir_path, filename)
        rows_exported = export_to_csv(table_name, full_filepath)
        total_rows += rows_exported
        print(f"Exported {rows_exported} rows from {table_name} to {filename}")
    return total_rows
