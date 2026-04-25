import os
import pyodbc
import pandas as pd
from config import DbConfig, default_config


def get_connection(cfg: DbConfig = None) -> pyodbc.Connection:
    cfg = cfg or default_config()
    if cfg.windows_auth:
        conn_str = (
            f"DRIVER={{{cfg.driver}}};"
            f"SERVER={cfg.instance};"
            f"DATABASE={cfg.database};"
            "Trusted_Connection=yes;"
        )
    else:
        uid = os.environ["CWSERVER_UID"]
        pwd = os.environ["CWSERVER_PWD"]
        conn_str = (
            f"DRIVER={{{cfg.driver}}};"
            f"SERVER={cfg.instance};"
            f"DATABASE={cfg.database};"
            f"UID={uid};PWD={pwd};"
        )
    return pyodbc.connect(conn_str)


def query_df(conn: pyodbc.Connection, sql: str, params=None) -> pd.DataFrame:
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=columns)


def execute(conn: pyodbc.Connection, sql: str, params=None) -> None:
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    conn.commit()
