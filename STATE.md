# State — southside-guitars-db
Last updated: 26/04/2026 AEST

## Status
Session 3 complete. PayType codes fully resolved. All payment types now identified.

## PayType Code Map (tblPayments)
- PayType 0 = Cash [V] — Tendered column always populated
- PayType 2 = EFTPOS/Card (all brands) [V] — Tendered=NULL; single integrated disbursement
- PayType 3 = AMEX button in PosWiz [V] — used by untrained staff; settles in same eftpos batch as PayType 2 (integrated provider since ~2021); treat as PayType 2 for reconciliation
- PayType 4 = Unknown (3 rows, Dec 2020 only) [?]
- PayType 5 = Credit note / gift voucher — pre-Jul 2021 [V] (98 rows; superseded by PayType 7)
- PayType 6 = Direct bank transfer / other EFT [R] — max $11K, loans and refunds
- PayType 7 = Credit note / gift voucher — Mar 2022–present [V] (89 rows; same function as PayType 5, PosWiz button reconfigured)
- PayType 8 = ALL online orders [V] — PayPal + Shopify Payments + Afterpay + ZipPay all route through the single "PayPal" button in PosWiz; no gateway granularity in DB
- PayType 9 = Unknown (3 rows) [?]

## What Was Confirmed This Session
- PayType 3 = AMEX (confirmed via sale S25H267 lookup in PosWiz) [V]
- PayType 7 = credit note / gift voucher (confirmed via sale S26C249 lookup) [V]
- PayType 5 and 7 are same function — non-overlapping date ranges are a staff behaviour artefact (high turnover period), not a system reconfiguration; both buttons have always existed in PosWiz
- PayType 3 settles in same eftpos batch as PayType 2 — integrated provider, no separate AMEX disbursement [V]
- PayType 8 = all online payments (PayPal, Shopify, Afterpay, Zip) through single "PayPal" button [V]
- No descriptor/lookup table for POS PayTypes — codes are hardcoded in PosWiz application [V]
- tblDDRPayMethods is CashNet loan repayment methods only (bitmask encoded), not POS payment types [V]

## Previously Confirmed (Session 2)
- PayType 6 = Direct Bank Transfer/EFT [R] — max $11K, appears on loans and refunds
- RefType='X' → tblRefund.RefNo [V] — refund payout payments
- RefType='L' → tblTran.RefNo (loan records) [V]
- tblSaleItem.RefNo = item provenance: 'INV'=supplier stock, 'B######'=bought-in s/h [V]
- Data migration boundary = August 2020 [V] — pre-2020 data migrated from PawnIt system (2013–Jul/Aug 2020); CWServer/PosWiz/CashNet (ProCreate vendor) live from Aug 2020 onwards

## Open Questions
- [ ] PayType 4 (3 rows, Dec 2020 only) — identity unknown [?]
- [ ] PayType 9 (3 rows) — identity unknown [?]
- [ ] tblDodgy (19 rows) — what triggers a record here?
- [ ] Pre-2020 StockID=NULL rows in tblSaleItem (8,869 rows) — confirm these are migration artefacts

## Next Step (new session)
Explore tblDodgy and pre-2020 StockID=NULL rows if needed.
PayType 4 and 9 are low-count edge cases — investigate opportunistically or leave as unknown.

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication (PowerShell only — Bash shell fails with Named Pipes error)
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
