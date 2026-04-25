# State — southside-guitars-db
Last updated: 25/04/2026 AEST

## Status
Column exploration complete for 6 priority tables: tblSale, tblSaleItem, tblTran, tblTranItems,
tblPayments, tblReceiptInfo. Two-subsystem architecture fully documented.
DISCOVERIES.md and TECHNICAL_SPEC.md updated with full column maps and lookup tables.

## Next Step (new session)
Load parsers.py from ssg-reconciliation to cross-reference PosWiz CSV field names against
tblSale/tblSaleItem columns. Confirm PayType integer → payment method mapping.

## Open Questions
- [ ] `RefType = X` (1,068 payments, 1,299 receipts) — what transaction type?
- [ ] `RefType = L` (238/236) — Layby separate from tblSale.Settled=0? Or Loan (tblTran)?
- [ ] PayType 0,2,3,4,6,7,8,9 exact identities — needs PosWiz CSV cross-reference [?]
- [ ] `tblDodgy` (19 rows) — what triggers a record here?
- [ ] `tblSaleItem.RefNo` — different from SaleNo, unknown purpose

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
