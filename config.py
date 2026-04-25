from dataclasses import dataclass


@dataclass
class DbConfig:
    instance: str
    database: str
    driver: str
    windows_auth: bool


def default_config() -> DbConfig:
    return DbConfig(
        instance=r".\SQLEXPRESS",
        database="CWServer",
        driver="ODBC Driver 17 for SQL Server",
        windows_auth=True,
    )
