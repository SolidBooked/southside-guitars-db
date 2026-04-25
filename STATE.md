# State — southside-guitars-db
Last updated: 25/04/2026 AEST

## Status
Repo initialized and pushed to GitHub: https://github.com/SolidBooked/southside-guitars-db
Row counts run across all 82 tables. Key active tables identified and documented.
DISCOVERIES.md and TECHNICAL_SPEC.md updated with count data.

## Next Step
Run `python schema.py --columns CWServer.tblSale` and `--columns CWServer.tblSaleItem`
to map columns against known PosWiz CSV export fields.

## Open Questions
- [ ] `tblTran` (4,533 rows) — what transaction type does it represent? (not POS sales — too few rows)
- [ ] `tblReceiptInfo` (57,197 rows) — is this one record per payment method per sale?
- [ ] What date range does the live data cover?
- [ ] `tblDodgy` (19 rows) — what triggers a record to land here?

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
