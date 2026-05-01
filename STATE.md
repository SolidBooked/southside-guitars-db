# State — southside-guitars-db
Last updated: 01/05/2026 AEST

## Status
Session 5 complete. PayType repurposing live (01/05/2026). q2_extract.py built and validated. Account code classification in progress.

## PayType Code Map (tblPayments)
- PayType 0 = Cash [V] — Tendered column always populated
- PayType 1 = Cheque [V] — legacy button; 2 rows total; almost never used
- PayType 2 = EFTPOS/Card (all brands) [V] — Tendered=NULL; single integrated disbursement via First Data (FDSMA)
- PayType 3 = AMEX button in PosWiz [V] — October 2023: merchant services provider changed; AMEX settlement integrated into EFTPOS batch (same as PayType 2). All PayType 3 rows after Oct 2023 are staff training failures (miskeys), not genuine AMEX-routed transactions. Last legitimate AMEX use: Oct 2023 cluster. Post-Oct 2023 rows: Aug 2025 (1 row, $76) — confirmed miskey. **From 01/05/2026: repurposed to Afterpay.**
- PayType 4 = VISA [V] — pre-EFTPOS-integration only; 3 rows Dec 2020; card brands consolidated under PayType 2 from mid-2021; **from 01/05/2026: repurposed to ZipPay**
- PayType 5 = MasterCard [V] — pre-EFTPOS-integration only; 98 rows pre-Jul 2021; consolidated under PayType 2 from mid-2021
- PayType 6 = Direct bank transfer / EFT [V] — max $11K; appears on loans and refunds
- PayType 7 = Credit note / gift voucher [V] — Mar 2022–present; 102 rows; no bank movement; Xero account 808
- PayType 8 = Online orders [V] — pre-01/05/2026: ALL online (PayPal + Shopify Payments + Afterpay + ZipPay) via single "PayPal" button, no gateway granularity; **from 01/05/2026: PayPal only**
- PayType 9 = Other credit card [V] — 3 rows total; **from 01/05/2026: repurposed to Shopify Payments**

**EFTPOS integration timeline:** Pre-mid-2021, VISA (PayType 4), MasterCard (PayType 5), and AMEX (PayType 3) had separate PosWiz buttons. After First Data (FDSMA) integrated provider was enabled, all card brands settled through one batch. PayType 4 and 5 stopped being used; PayType 3 (AMEX) persisted due to staff habit but routes through same settlement.

**Correction note (Session 4):** PayType 5 was recorded as "credit note/gift voucher [V]" in Sessions 2–3. That was an inference from the PayType 7 lookup — never directly verified. Corrected to MasterCard [V] based on PosWiz UI button order confirmed by store owner.

## What Was Confirmed This Session (Session 5)
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
- StockID 24554 = repeatable placeholder used exclusively to record gift voucher (PayType 7 / Xero account 808) line items in tblSaleItem [V] — the only viable mechanism found to capture payment type at transaction time; causes a double-up in item counts which is acknowledged and handled in SSG reconciliation scripts (exclude StockID 24554 from sales item analysis)
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

**Confirmed gateway-to-code assignments (live from 01/05/2026) [V]:**
- PayType 3: AMEX button → **Afterpay** (previously AMEX card via EFTPOS/First Data batch)
- PayType 4: VISA → **ZipPay**
- PayType 8: PayPal button → **PayPal only** (previously all-online bucket; now gateway-specific)
- PayType 9: Other credit card → **Shopify Payments**
- PayType 1, 5: remain dormant/unassigned

**Critical: dual-semantics date cutoff for reconciliation scripts**
Codes 3/4/8/9 carry different meanings before and after 01/05/2026. Any tblPayments query on these codes must apply a date filter:
- `Time_Stamp < 2026-05-01` → old meaning (card brand or all-online bucket)
- `Time_Stamp >= 2026-05-01` → new gateway assignment (see above)

Note: PayType 8 pre-cutoff contained ALL online gateways (PayPal + Shopify + Afterpay + ZipPay). Post-cutoff each has its own code. Aggregate online queries across the cutoff must union all four codes for post-cutoff rows.

**Reconciliation source-of-truth:** Gateway CSV files (PayPal, Afterpay, ZipPay, Shopify Payments) are the primary source for all online gateway reconciliation. PosWiz PayType codes are a secondary signal only — gateway CSVs are used to confirm/correct DB transactions in case of human error (e.g. staff hitting wrong button). The AMEX button label remains unchanged in PosWiz UI; miskeys are expected and corrected via CSV cross-reference, not prevented at point of sale.

## Scripts Built

### q2_extract.py [V — 01/05/2026]
Q2 FY26 (Oct–Dec 2025) extraction covering both PosWiz and CashNet subsystems.
Output: `Q2_FY26_Extract.xlsx` (10 sheets)
- **PosWiz_Payments** — 1,463 rows; tblPayments + tblSale join; PayType label + EFTPOS pool flag
- **PosWiz_GST** — 1,404 rows; tblReceiptInfo GST per sale
- **PosWiz_Daily** — daily summary by PayType + EFTPOS pool total + GST
- **PosWiz_SaleItems** — 2,719 rows; tblSaleItem + account code (200/201/808); 2,712 @ 200 ($245k), 7 @ 808 ($915)
- **PosWiz_AccountDaily** — daily totals by Xero account code (200/201/808)
- **Online_Orders** — 238 PayType 8 rows with resolved gateway (Shopify 142/$44k, PayPal 60/$13k, Afterpay 33/$10k, Zip 3/$1.8k); joined from paypal_sales_v2.csv
- **Online_Daily** — daily gateway breakdown
- **EFTPOS_Recon** — PosWiz daily EFTPOS totals vs 64 First Data ANZ deposits ($111,904); 52 matched, 7 splits, 36 unmatched (boundary/holiday edge cases)
- **CashNet_Buys** — 82 rows; tblTran (RefType=B, Amount>0); payment method classified via 3-pass tblCashMove match
- **CashNet_Daily** — daily Cash / Bank Transfer / total / buy count

Validated totals: CashNet $39,712.00 [V] (exact match to cashnet_parser Q2 figure).
Pass 3 Cash defaults: 4 buys (no CM record found — expected, cashnet memory noted ~3).

## tblSaleItem Account Code Classification [V — 01/05/2026]

RefNo prefix meaning (confirmed by store owner):
- `B######` = Buys (second-hand bought-in) — GST applies
- `L######` = Loans (pawn loans) — seized/forfeited items are GST-exempt (financial transaction)
- `C######` = Consignment — GST applies
- `INV`     = Supplier stock — GST applies
- `OS-*`    = Other Stock (ad-hoc, no stock record) — GST applies
- `S######` = Sale reference (not a stock origin)

Origin field values (tblSaleItem):
- `GST` = supplier/bought-in stock with GST set
- `NULL` = second-hand bought-in (B-prefix), GST still applies
- `OS`  = Other Stock (ad-hoc unlisted items)
- `GFS` = Gift voucher placeholder (always StockID 24554)

**Account code classification rule (applied per tblSaleItem row):**
1. `Origin = 'GFS'` OR `StockID = 24554` → **808** (gift voucher)
2. `RefNo LIKE 'L%'` → **201** (seized pawn item, GST-exempt) — rare
3. All other rows → **200** (GST sales)

Note: StockID 24554 rows (account 808) are the gift voucher double-up placeholder — exclude from 200/201 totals in any item-level analysis.

## Next Steps
All three planned extraction tasks complete as of 01/05/2026:
- ~~Add tblSaleItem join → Xero account codes (200/201/808)~~ [V]
- ~~EFTPOS reconciliation feed~~ [V]
- ~~Online orders extract (PayType 8 → gateway CSV)~~ [V]

## Connection
```
Instance : .\SQLEXPRESS
Database : CWServer
Auth     : Windows Authentication (PowerShell only — Bash shell fails with Named Pipes error)
sqlcmd   : C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
Python   : pyodbc + ODBC Driver 17 for SQL Server
```
