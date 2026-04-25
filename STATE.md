# State — southside-guitars-db
Last updated: 25/04/2026 AEST

## Status
Session 2 complete. PayType codes cross-referenced against parsers.py and paypal_sales_v2.csv.
RefType=X and RefType=L resolved. tblSaleItem.RefNo purpose identified. Data migration boundary
documented. DISCOVERIES.md and TECHNICAL_SPEC.md updated.

## What Was Confirmed This Session
- PayType 0 = Cash [V] — Tendered column always populated
- PayType 2 = EFTPos/Card (all types) [V] — Tendered=NULL
- PayType 8 = ALL online "(PayPal)" orders [V] — confirmed via paypal_sales_v2.csv cross-ref
  (PayPal AND Shopify Payments both map to PayType 8; in-DB gateway disambiguation not possible)
- PayType 6 = Direct Bank Transfer/EFT [R] — max $11K, appears on loans and refunds
- PayType 5 = Gift Voucher [R] — count matches tblVoucher (99)
- RefType='X' → tblRefund.RefNo [V] — refund payout payments
- RefType='L' → tblTran.RefNo (loan records) [V]
- tblSaleItem.RefNo = item provenance: 'INV'=supplier stock, 'B######'=bought-in s/h [V]
- Data migration boundary = August 2020 (pre-2020 data imported from old system) [V]

## Open Questions
- [ ] PayType 3 = which in-store BNPL? (Afterpay or Zip; active Sep 2020–Aug 2025, now discontinued)
- [ ] PayType 7 = which in-store BNPL? (the other of Afterpay/Zip; active Mar 2022–present)
- [ ] PayType 4 (3 rows, Dec 2020 only) and PayType 9 (3 rows) — identity unknown [?]
- [ ] tblDodgy (19 rows) — what triggers a record here?
- [ ] Pre-2020 StockID=NULL rows in tblSaleItem (8,869 rows) — confirm these are migration artefacts

## Next Step (new session)
Ask user: which in-store BNPL methods does Southside Guitars accept (Afterpay and/or Zip)?
When was each activated? This will close PayType 3 vs 7 identity.
Then: explore tblDodgy and pre-2020 StockID=NULL rows if needed.

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication (PowerShell only — Bash shell fails with Named Pipes error)
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
