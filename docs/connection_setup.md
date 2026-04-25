# Connection Setup — CWServer

## Prerequisites

1. **Windows Authentication** — no username/password needed; your Windows login must have access to the SQL Server instance.
2. **ODBC Driver 17 for SQL Server** — already installed at:
   `C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\`
3. **Python 3.x** with packages from `requirements.txt`

---

## Verify the SQL Server Instance

Confirm the SQLEXPRESS service is running:
```
services.msc → look for "SQL Server (SQLEXPRESS)"
```
Or in PowerShell:
```powershell
Get-Service | Where-Object { $_.Name -like "*SQL*" }
```

---

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Test the Connection via sqlcmd

sqlcmd is not on the default PATH. Use the full path:

```cmd
"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE" ^
  -S .\SQLEXPRESS -d CWServer -E -Q "SELECT TOP 1 * FROM INFORMATION_SCHEMA.TABLES"
```

---

## Test via Python

```python
from db import get_connection
conn = get_connection()
print("Connected:", conn)
conn.close()
```

---

## Run Schema Explorer

```bash
# List all databases on the instance
python schema.py --databases

# List tables in CWServer
python schema.py --tables CWServer

# Describe columns in a table
python schema.py --columns CWServer.tblTran

# Row counts for all tables
python schema.py --counts CWServer

# Search for a keyword across table/column names
python schema.py --search payment
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `InterfaceError: ('IM002', ...)` | ODBC driver name mismatch | Check driver name in `config.py` matches installed drivers via ODBC Data Source Administrator |
| `OperationalError: Login failed` | Windows Auth not configured | Ensure your Windows user has SQL Server login rights |
| `pyodbc.Error: [08001]` | Instance not found or not running | Start the SQL Server (SQLEXPRESS) service |
