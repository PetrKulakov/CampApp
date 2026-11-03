from datetime import datetime, time
import psycopg
from psycopg.rows import dict_row
from threading import Thread
from typing import Dict, Any
import csv
import json
import os


def check_connection(config: dict) -> tuple[bool, str]:
    try:
        full_config = config.copy()
        full_config["connect_timeout"] = 3
        with psycopg.connect(**full_config) as conn:
            return True, ""
    except Exception as e:
        return False, str(e)

def query(sql: str, config: Dict) -> Dict[str, Any]:
    with psycopg.connect(**config, row_factory=dict_row) as conn:
        with conn.cursor() as curr:
            curr.execute(sql)
            return curr.fetchall()

def export_to_csv(sql: str, filename: str, db_config: Dict) -> int:
    data = query(sql, config=db_config)
    if not data:
        return 0
    headers = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    return len(data)

def export_to_json(sql: str, filepath: str, db_config: Dict) -> int:
    data = query(sql, db_config)
    if not data:
        return 0
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)
    
    return len(data)

def backup_to_csv(filepath: str, db_config: Dict) -> int:
    count_rows = 0
    sql = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_catalog = '{db_config["dbname"]}';
        """
    table_namess = [row["table_name"] for row in query(sql, db_config)]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_path = f"{filepath}/{db_config['dbname']}_backup_{timestamp}"
    os.makedirs(dir_path, exist_ok=True)
    for table in table_namess:
        sql = f'SELECT * FROM {table}'
        full_filepath = f"{dir_path}/{table}.csv"
        count_rows += export_to_csv(sql, filename=full_filepath, db_config=db_config)
    return count_rows

def backup_to_json(filepath: str, db_config: Dict) -> int:
    count_rows = 0
    sql = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_catalog = '{db_config["dbname"]}';
        """
    table_namess = [row["table_name"] for row in query(sql, db_config)]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_path = f"{filepath}/{db_config['dbname']}_backup_{timestamp}"
    os.makedirs(dir_path, exist_ok=True)
    for table in table_namess:
        sql = f'SELECT * FROM {table}'
        full_filepath = f"{dir_path}/{table}.json"
        count_rows += export_to_json(sql, filepath=full_filepath, db_config=db_config)
    return count_rows
