# State — southside-guitars-db
Last updated: 25/04/2026 AEST

## Status
Repo initialized. All core scripts created: `config.py`, `db.py`, `schema.py`.
82 tables confirmed in CWServer via sqlcmd. Initial discovery recorded in DISCOVERIES.md.
GitHub repo created and initial commit pushed.

## Next Step
Run `python schema.py --counts CWServer` to identify the most-used tables by row volume,
then drill into `tblTran` and `tblTranItems` columns to map against PosWiz CSV export fields.

## Open Questions
- [ ] Which SQL Server instance is the active one: MSSQL13 or MSSQL16? (cwserver.mdf confirmed in MSSQL13)
- [ ] Does `tblTran` or `tblSale` serve as the primary POS transaction record?
- [ ] What date range does the live data cover?
- [ ] Is `tblBankFeeds` populated — could it replace ANZ CSV exports?

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
