"""Schema explorer for the CWServer database."""
import argparse
import sys
from tabulate import tabulate
from db import get_connection, query_df
from config import default_config, DbConfig


def list_databases(conn) -> None:
    df = query_df(conn, "SELECT name, create_date, state_desc FROM sys.databases ORDER BY name")
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def list_tables(conn, database: str) -> None:
    sql = f"""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM [{database}].INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_TYPE, TABLE_SCHEMA, TABLE_NAME
    """
    df = query_df(conn, sql)
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def describe_columns(conn, db_table: str) -> None:
    if "." not in db_table:
        print(f"Error: expected DB.TABLE, got '{db_table}'", file=sys.stderr)
        sys.exit(1)
    database, table = db_table.split(".", 1)
    sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               IS_NULLABLE, COLUMN_DEFAULT
        FROM [{database}].INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """
    df = query_df(conn, sql, params=[table])
    if df.empty:
        print(f"No columns found for '{db_table}'. Check database and table name.")
        return
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def row_counts(conn, database: str) -> None:
    sql = f"""
        SELECT
            t.TABLE_SCHEMA,
            t.TABLE_NAME,
            p.rows AS row_count
        FROM [{database}].INFORMATION_SCHEMA.TABLES t
        JOIN [{database}].sys.tables st
            ON t.TABLE_NAME = st.name
        JOIN [{database}].sys.partitions p
            ON st.object_id = p.object_id AND p.index_id IN (0, 1)
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY p.rows DESC, t.TABLE_NAME
    """
    df = query_df(conn, sql)
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def search_schema(conn, term: str) -> None:
    sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME LIKE ? OR COLUMN_NAME LIKE ?
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    like = f"%{term}%"
    df = query_df(conn, sql, params=[like, like])
    if df.empty:
        print(f"No matches for '{term}'.")
        return
    print(tabulate(df, headers="keys", tablefmt="simple", showindex=False))


def main():
    parser = argparse.ArgumentParser(description="CWServer schema explorer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--databases", action="store_true", help="List all databases on the instance")
    group.add_argument("--tables", metavar="DB", help="List tables in database DB")
    group.add_argument("--columns", metavar="DB.TABLE", help="Describe columns in DB.TABLE")
    group.add_argument("--counts", metavar="DB", help="Row counts for all tables in DB")
    group.add_argument("--search", metavar="TERM", help="Search table/column names for TERM")
    args = parser.parse_args()

    cfg = default_config()
    conn = get_connection(cfg)

    if args.databases:
        list_databases(conn)
    elif args.tables:
        list_tables(conn, args.tables)
    elif args.columns:
        describe_columns(conn, args.columns)
    elif args.counts:
        row_counts(conn, args.counts)
    elif args.search:
        search_schema(conn, args.search)

    conn.close()


if __name__ == "__main__":
    main()
