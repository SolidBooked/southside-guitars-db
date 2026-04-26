# State — southside-guitars-db
Last updated: 26/04/2026 AEST

## Status
Session 4 complete. PayType map fully corrected — all 10 codes now [V]. All open questions closed.

## PayType Code Map (tblPayments)
- PayType 0 = Cash [V] — Tendered column always populated
- PayType 1 = Cheque [V] — legacy button; 2 rows total; almost never used
- PayType 2 = EFTPOS/Card (all brands) [V] — Tendered=NULL; single integrated disbursement via First Data (FDSMA)
- PayType 3 = AMEX button in PosWiz [V] — used by untrained staff; settles in same EFTPOS batch as PayType 2; treat as PayType 2 for reconciliation
- PayType 4 = VISA [V] — pre-EFTPOS-integration only; 3 rows Dec 2020; card brands consolidated under PayType 2 from mid-2021
- PayType 5 = MasterCard [V] — pre-EFTPOS-integration only; 98 rows pre-Jul 2021; consolidated under PayType 2 from mid-2021
- PayType 6 = Direct bank transfer / EFT [V] — max $11K; appears on loans and refunds
- PayType 7 = Credit note / gift voucher [V] — Mar 2022–present; 102 rows; no bank movement; Xero account 808
- PayType 8 = ALL online orders [V] — PayPal + Shopify Payments + Afterpay + ZipPay all route through single "PayPal" button in PosWiz; no gateway granularity in DB
- PayType 9 = Other credit card [V] — 3 rows total

**EFTPOS integration timeline:** Pre-mid-2021, VISA (PayType 4), MasterCard (PayType 5), and AMEX (PayType 3) had separate PosWiz buttons. After First Data (FDSMA) integrated provider was enabled, all card brands settled through one batch. PayType 4 and 5 stopped being used; PayType 3 (AMEX) persisted due to staff habit but routes through same settlement.

**Correction note (Session 4):** PayType 5 was recorded as "credit note/gift voucher [V]" in Sessions 2–3. That was an inference from the PayType 7 lookup — never directly verified. Corrected to MasterCard [V] based on PosWiz UI button order confirmed by store owner.

## What Was Confirmed This Session (Session 4)
- tblDodgy = inter-store customer watchlist/notes system [V] — ProCreate network feature for flagging customers across stores; SSG uses loosely; NOT transaction anomaly data; no reconciliation impact
- Pre-2020 StockID=NULL rows in tblSaleItem = confirmed PawnIt migration artefact [V] — ~11,000 s/h items duplicated to ~22,000 on import; one copy got numerical StockID (correct), other got INV-prefix StockID (incorrectly typed as new supplier stock)
- PayType 1 = Cheque [V] — confirmed from PosWiz UI button order
- PayType 4 = VISA [V] — confirmed from PosWiz UI button order; pre-integration only
- PayType 5 = MasterCard [V] — confirmed from PosWiz UI button order; corrects prior session error
- PayType 6 = Bank transfer / direct deposit [V] — confirmed from PosWiz UI (upgrade from [R])
- PayType 9 = Other credit card [V] — confirmed from PosWiz UI button order

## Previously Confirmed (Sessions 1–3)
- PayType 0 = Cash [V] — Tendered always populated
- PayType 2 = EFTPOS/Card [V] — Tendered=NULL
- PayType 3 = AMEX (confirmed via sale S25H267 PosWiz lookup) [V]
- PayType 7 = credit note / gift voucher (confirmed via sale S26C249 PosWiz lookup) [V]
- PayType 8 = all online (confirmed via paypal_sales_v2.csv cross-reference) [V]
- RefType='X' → tblRefund.RefNo [V]; RefType='L' → tblTran.RefNo [V]
- tblSaleItem.RefNo = item provenance: 'INV'=supplier stock, 'B######'=bought-in s/h [V]
- Data migration boundary = August 2020 [V]
- tblDDRPayMethods = CashNet loan repayment bitmask codes only — NOT POS PayTypes [V]
- No PayType lookup table in DB — codes hardcoded in PosWiz application [V]

## Open Questions
None. All structural exploration complete as of Session 4.

## Planned Changes

### PayType code repurposing — proposed go-live 01/05/2026
Store manager has proposed repurposing dormant PayType codes for BNPL/ecommerce gateway granularity, splitting the current single PayType 8 (all online) into per-gateway codes. Specific code-to-gateway assignments TBD.

**Dormant codes available for repurposing:**
- PayType 1 — Cheque (2 historical rows)
- PayType 4 — VISA (3 historical rows, Dec 2020)
- PayType 5 — MasterCard (98 historical rows, pre-Jul 2021)
- PayType 9 — Other credit card (3 historical rows)

**Critical: dual-semantics date cutoff for reconciliation scripts**
Once repurposed, codes 1/4/5/9 carry different meanings before and after 01/05/2026. Any tblPayments query on these codes must apply a date filter:
- `Time_Stamp < 2026-05-01` → old card brand (historical, minimal rows)
- `Time_Stamp >= 2026-05-01` → new BNPL/ecomm gateway assignment

Update with confirmed gateway-to-code assignments when known.

## Next Step (new session)
All PayType codes resolved. Schema fully documented. Begin analytical/extraction scripts:
- Sales extract by date range (tblSale + tblSaleItem + tblPayments)
- EFTPOS reconciliation feed (PayType 2+3 → First Data settlement)
- Online orders extract (PayType 8 → cross-reference with gateway CSVs)

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication (PowerShell only — Bash shell fails with Named Pipes error)
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
