# Session 2026-05-01 — Q2 Extract Expansion

## Summary
Expanded q2_extract.py from 5 sheets to 10 sheets covering account code classification,
online gateway breakdown, and EFTPOS reconciliation. Created tools/ directory.

## Changes Made

### STATE.md
- Added StockID 24554 note: repeatable placeholder for gift voucher (PayType 7 / acct 808) line items in tblSaleItem; causes double-up handled in reconciliation scripts
- Added full tblSaleItem account code classification rules (verified via DB probe)
- Marked all three next steps as complete

### q2_extract.py — 5 sheets → 10 sheets
New sheets added:

**PosWiz_SaleItems** (2,719 rows)
- tblSaleItem joined to tblSale for date filtering
- Account code classification per row:
  - Origin=GFS or StockID=24554 → 808 (gift voucher)
  - RefNo LIKE 'L%' → 201 (seized pawn item, GST-exempt, rare)
  - All else → 200 (GST sale)
- Q2 result: 2,712 rows @ acct 200 ($245,075), 7 rows @ acct 808 ($915), 0 @ acct 201

**PosWiz_AccountDaily**
- Daily totals pivoted by account code (acct_200 / acct_201 / acct_808 / day_total)

**Online_Orders** (238 rows)
- PayType 8 rows from PosWiz_Payments with resolved gateway
- Gateway sourced from paypal_sales_v2.csv (join on sale_no / sale_ref)
- Q2 breakdown: Shopify Payments 142/$44k, PayPal 60/$13k, Afterpay 33/$10k, Zip 3/$1.8k

**Online_Daily**
- Daily totals pivoted by gateway + txn_count

**EFTPOS_Recon**
- 64 First Data ANZ deposits ($111,904) matched against PosWiz daily eftpos_pool_total
- Matching logic: next business day rule (Fri/Sat/Sun → Monday); FD_HOLIDAY_BUFFER=1 for public holidays
- Q2 result: 52 matched, 7 splits (card-type batches), 36 unmatched (boundary/holiday edge cases)
- Columns: fd_date, fd_amount, pw_trading_date, pw_expected_fd, pw_eftpos_total, variance, match_status

### tools/explore_sale_items.py (new)
Reusable tblSaleItem exploration tool replacing one-off _probe.py scripts.
- Args: --start, --end (date range), --sample N, --stockid N
- Sections: origin distribution, RefNo pattern distribution, account code preview, sample rows, loan items, optional StockID lookup
- sys.path.insert pattern allows running from project root

### Deleted
- _probe.py (superseded by tools/explore_sale_items.py)

## Key Facts Confirmed This Session
- RefNo prefixes: B=Buys (s/h, GST), L=Loans (seized, acct 201 exempt), C=Consignment (GST), INV=supplier stock (GST), OS-*=Other Stock ad-hoc (GST)
- Origin values: GST=standard stock, NULL=s/h bought-in (GST applies), OS=other stock, GFS=gift voucher
- Account 201 (exempt) applies only to L-prefix RefNo rows (seized pawn items) — none present in Q2
- StockID 24554 is the gift voucher placeholder — exclude from item-level analysis to avoid double-count
- Second-hand items carry GST (Origin=NULL rows → acct 200, not 201)
- FD settles next business day only; Fri/Sat/Sun batch to Monday

## Data Paths Used
- ANZ CSV: ssg-reconciliation/FY26_Q2/ANZ_2025.09.28_2026.01.05.csv
- Gateway map: ssg-reconciliation/FY26_Q2/paypal_sales_v2.csv
