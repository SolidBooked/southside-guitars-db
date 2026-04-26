# Discoveries — CWServer Schema Exploration

Append-only log. Each entry tagged with confidence: [V] Verified | [R] Reasoned | [?] Unverified.

---

## 25/04/2026 — Discovery: Initial Schema Inventory

**What we found:**
CWServer contains 82 base tables, all in the `dbo` schema. No views found in initial scan.
SQL Server 2016 Express (MSSQL13.SQLEXPRESS). Database file at
`C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS\MSSQL\DATA\CWServer.mdf`. [V]

**Key table groupings identified:** [R]

| Group | Tables |
|-------|--------|
| Core transactions | `tblTran`, `tblTranItems`, `tblTranItemsIdentify` |
| Sales | `tblSale`, `tblSaleItem` |
| Payments | `tblPayments`, `tblCheqCash`, `tblCashMove`, `tblPettyCash` |
| Refunds | `tblRefund`, `tblRefundItem` |
| Accounting | `tblAccChart`, `tblAccReceipts`, `tblJournal`, `tblBalance`, `tblBankFeeds` |
| Module config | `tblAdminCashNET`, `tblAdminPayWiz`, `tblAdminPOSWiz` |
| Customers/Suppliers | `tblCustSupp`, `tblAddrHist` |
| Products/Inventory | `tblProducts`, `tblBarcode`, `tblCategory`, `tblBarcodesExcluded` |
| Repairs | `tblRepairs`, `tblRepairParts`, `tblRepairStatusList` |
| Layby/Pre-sale | `tblCart`, `tblCartItems`, `tblQuotes`, `tblQuoteItems`, `tblDDR`, `tblHoldInfo` |
| Payroll | `tblStaff`, `tblPayEmpDetails`, `tblPaySheets`, `tblPayTimes`, `tblPayYTD` |
| Misc | `tblVoucher`, `tblDiscounts`, `tblTills`, `tblLog`, `tblHistory`, `tblRevisions` |

**Why it matters:**
The presence of `tblAdminCashNET`, `tblAdminPayWiz`, `tblAdminPOSWiz` confirms cwserver is the
unified backend for all three modules. `tblTran`/`tblTranItems` is the likely source of truth
that all CSV exports are derived from. [R]

**Next to verify:**
- Column structure of `tblTran` and `tblTranItems` vs `tblSale` and `tblSaleItem`
- What `tblTran`/`tblTranItems` actually represent given the low row count vs `tblSale`

---

## 25/04/2026 — Discovery: Row Counts — Active Table Map

**What we found:** [V]

| Table | Rows | Notes |
|-------|------|-------|
| tblSaleItem | 59,996 | Largest table — POS sale line items |
| tblLog | 58,793 | Audit/activity log |
| tblReceiptInfo | 57,197 | Near 1:1 with SaleItem — receipt per line? |
| tblTranItems | 33,680 | ~7 items per tblTran row — different ratio than tblSale |
| tblPayments | 32,978 | ~1:1 with TranItems — likely payment per transaction item |
| tblSale | 30,768 | POS sales header — avg ~2 items per sale |
| tblCustSupp | 10,728 | Customer/supplier master |
| tblArticle | 7,060 | Product catalog (NOT tblProducts — see below) |
| tblTran | 4,533 | NOT the main POS table — low count vs tblSale |
| tblRepairs | 975 | Active repairs module |
| tblRefundItem | 1,468 / tblRefund 1,136 | Refunds in use |
| tblVoucher | 99 | Gift vouchers in use |
| tblDodgy | 19 | Inter-store flagged customer list (ProCreate network feature). Links to tblCustSupp.NameID via WarnText notes. Interstore columns (bit + InterstoreAmmend + InterstoreID) confirm cross-store sync design. SSG uses loosely — some genuine warnings (stolen goods), most are general customer notes. NOT transaction data; no reconciliation query impact. |

**Completely empty (0 rows) — features not in use:** [V]
`tblBankFeeds`, `tblDDR`, `tblJournal`, `tblCart`, `tblCartItems`, `tblQuotes`,
`tblQuoteItems`, `tblCheqCash`, `tblPettyCash`, `tblDiscounts`, `tblAccChart`,
`tblAccReceipts`, `tblAuction*`, `tblCWRA`, `tblInvProcesses`, `tblMarkets`

**Key surprises:** [R]
1. `tblSale` (30,768) is the main POS table, not `tblTran` (4,533). The naming is misleading.
   `tblTran` likely handles CashNet/web orders or layby payment schedules — needs column inspection.
2. `tblProducts` has only 6 rows — the product catalog lives in `tblArticle` (7,060 rows).
   In cwserver, "Article" = product. `tblProducts` may be a grouping/kit table.
3. `tblReceiptInfo` (57,197 rows) vs `tblSale` (30,768) — roughly 2 receipts per sale on average.
   Could represent one receipt per payment method used.

**Why it matters:**
- CSV bypass must target `tblSale`/`tblSaleItem` not `tblTran`/`tblTranItems`.
- `tblBankFeeds` being empty means bank feed data still comes from ANZ CSV only.
- Payroll tables (`tblPaySheets`, `tblPayYTD`) are empty — payroll not run through cwserver.

**Next to verify:**
- Map tblSale/tblSaleItem columns to PosWiz CSV export field names
- Confirm PayType integer → payment method name via CSV cross-reference

---

## 25/04/2026 — Discovery: Column Structure — Six Priority Tables

### tblSale (30,768 rows) — POS Sales Header [V]
All POS sales — both immediate and layby. Key columns:
- `SaleNo` (nvarchar 10) — primary sale identifier
- `NameID` (bigint) — customer FK → tblCustSupp
- `Amount` (float) — total sale value
- `Paid` (float) — amount paid to date
- `Settled` (bit) — 1 = fully paid, 0 = layby outstanding
- `SettleDate` (datetime) — when fully settled
- `Term`, `TermUnit` — layby terms (when Settled=0)
- `NextPayDate` (datetime) — next layby instalment due
- `HoldExpiry`, `SaleExpiry` — hold/expiry dates
- `PlacedBy` (nvarchar 6) — staff PIN
- `Time_Stamp` — created datetime
- `StoreNo` = 224 (Southside Guitars store number)
- `Freight` (float) — postage/freight charge
- Data range: 2013-11-06 to 2026-04-02

### tblSaleItem (59,996 rows) — POS Sale Line Items [V]
- `SaleNo` → FK to tblSale
- `RefNo` — unknown secondary reference (TBD)
- `StockID` → FK to tblTranItems (second-hand stock) or tblArticle (new stock)
- `Origin` (nvarchar 3) → FK to tblOrigin (GST treatment)
- `Qty` (float), `Amount` (float) — quantity and line total

### tblTran (4,533 rows) — Second-Hand/Pawnbroker Transactions [V]
NOT a POS table. Tracks second-hand goods under Queensland Second Hand Dealers Act:
- `RefNo` — transaction reference
- `RefType` (1 char) — transaction type code
- `TranDate` — date of transaction
- `Amount`, `Charges`, `MinFee`, `Interest` — loan/consignment financials
- `Term`, `TermUnit` — loan term
- `RedemptionIndicator`, `RedemptionSentToPolice`, `PoliceSent` — police reporting fields
- `OnShelf`, `ShelfDate` — when item goes on display shelf
- `Disposed`, `DisposedInfo`, `DisposedDate` — disposal tracking
- `SupplierRef`, `SellerPIN`, `PlacedBy` — who brought item in
- Data range: 2013-10-23 to 2026-03-31

### tblTranItems (33,680 rows) — Second-Hand Stock Items [V]
**NOT sale line items.** Each row = one physical second-hand item in the system:
- `RefNo` → FK to tblTran (which transaction brought it in)
- `StockID` — unique item identifier
- `Article`, `Category`, `MakeArtist`, `ModelTitle` — item description
- `SerialNo`, `Barcode` — identification
- `InStock`, `OnShelf`, `ShelfDate` — current location status
- `Qty`, `QtySold`, `QtyReturned`, `PriceSold` — sales tracking
- `SellerID`, `SellerPIN` — who consigned the item
- `Origin` → FK to tblOrigin (GST treatment)
- `RRPrice` through `RRPrice5` — five price tiers
- `ShowOnWeb`, `WebCode`, `eBay` — online listing fields
- `PoliceDataSent`, `PoliceSendChange` — police compliance
- `Disposed`, `WrittenOff`, `Checked` — status flags
- `ItemCost` — cost to acquire item
- `S0`-`S5` — six custom string fields for extra data
- Dimensions + PostageCode + ItemWeight — shipping fields for CashNet listings

### tblPayments (32,978 rows) — Payment Records [V]
- `ReceiptNo` → FK to tblReceiptInfo
- `RefType` + `RefNo` → links to tblSale (S=31,672), unknown-X (1,068), unknown-L (238)
- `PayType` (int) — payment method code (hardcoded in app, no lookup table found)
- `Amount` — payment amount
- `Tendered` — cash tendered (for cash payments)
- `PayRef` — NULL on all sampled rows (no card auth codes stored)
- `VoucherNo` — populated for gift voucher payments
- `Discount` — discount applied
- `Status`, `LastStatusChange` — payment status

**PayType frequency (inferred labels — [?] unconfirmed):**

| PayType | Count | Inferred |
|---------|-------|---------|
| 2 | 22,990 (68%) | EFTPOS/Card [?] |
| 0 | 7,464 (22%) | Cash [?] |
| 8 | 1,710 (5%) | Afterpay/BNPL [?] |
| 6 | 463 | Account credit / unknown [?] |
| 3 | 142 | Unknown [?] |
| 7 | 102 | PayPal / online [?] |
| 5 | 99 | Gift Voucher (matches tblVoucher row count) [R] |
| 4 | 3 | Unknown [?] |
| 9 | 3 | Unknown [?] |
| 1 | 2 | Cheque / EFT [?] |

PayType codes must be confirmed by cross-referencing PosWiz CSV exports.

### tblReceiptInfo (57,197 rows) — Receipt Line Items with GST [V]
One row per receipt line item — includes pre-calculated GST:
- `ReceiptNo` — receipt identifier
- `RefType` + `RefNo` → links to tblSale (S=55,662), unknown-X (1,299), L (236)
- `PayType`, `PayCode` (nvarchar 3) — payment method
- `SeqNo` — for split payment receipts
- `SeqTotal` — total for this receipt line
- `RecTotalAmount` — total receipt value
- `GSTAmount` — GST pre-calculated per receipt line ← key for tax reconciliation
- `SeqCost`, `SeqCostP1`, `SeqCostP2` — cost at price tiers
- `Principle`, `Interest`, `FeesCharges` — loan payment breakdown
- `StockID`, `StockRefNo` — links to stock item

---

## 25/04/2026 — Discovery: Lookup Tables and System Config

### RefType values across payment/receipt tables [V]
| RefType | tblPayments | tblReceiptInfo | Meaning | Links to |
|---------|-------------|----------------|---------|----------|
| S | 31,672 | 55,662 | Sale | tblSale.SaleNo |
| X | 1,068 | 1,299 | Refund payout | tblRefund.RefNo |
| L | 238 | 236 | Pawnbroker loan payment | tblTran where RefType='L' |

**RefType='X' confirmed [V]:** X-prefixed RefNos (e.g. X26A9) exist in tblRefund.RefNo. tblPayments with RefType='X' records the payment method used to pay out a refund to the customer. tblRefund.Amount matches tblPayments.Amount. tblRefundItem.SaleNo links back to the original sale being refunded.

**RefType='L' confirmed [V]:** L-prefixed RefNos (e.g. L21000013, L114) exist in tblTran where RefType='L'. tblTran.RefType has three codes: B (4,211 = Buy from public), L (301 = Loan/Pawn), C (21 = Consignment). RefType='L' payments are loan/pawn redemption payments.

Note: tblTran.RefType='B' (Buy transactions) do NOT have corresponding tblPayments records — cash payouts to sellers are tracked via tblCashMove ('Retail → Buys/Loans'), not tblPayments.

### tblCashMove — Daily Cash Movement Types [V]
Till cash flow vocabulary (FromType → ToType, count):
- `Retail → Bank` (1,806) — daily banking of till float
- `Retail → Buys/Loans` (376) — cash out for stock purchases or loan payouts
- `Retail → Voucher` (99) — gift voucher issuance
- `Bank → Retail` (98) — returning cash to till
- `Bank → Buys/Loans` (97) — bank float for purchases
- `Voucher → Retail` (84) — voucher redemption
- `Safe → Retail` (28), `Retail → Safe` (23) — safe movements
- `Retail → PayPal` (1) — confirms PayPal handled through system [V]

### tblWording — System Configuration Store [V]
Key-value config per StoreNo/ProductID. Notable entries:
- `StoreNo` = **224** — Southside Guitars' system store number
- `BackupPath` = `C:\Users\Southside Guitars\OneDrive\CWSever` — backups go to OneDrive
- `PolicePath` = `c:\policefiles` — second-hand goods police reporting output
- `LastPoliceSend` = 14/03/2026 — last police data submission
- `LastBackup` = 06/04/2026 — last successful backup
- Server = **SALISBURYSERVER** (`192.168.1.99`), clients on `192.168.68.x`
- Per-item notes stored here with WordingName = StockID (second-hand item notes)

### tblDDRPayMethods — NOT POS PayType lookup [V]
Power-of-2 bitmask codes for **Cashnet recurring/DDR payments only**:
Cash (32), EFTPos (4096), Credit Card (65536), Direct Debit (1), BPay (8), etc.
Not related to tblPayments.PayType integer codes.

### tblOrigin — Stock Origin and GST Rates [V]
| Code | Rate | Origin | Module |
|------|------|--------|--------|
| GST | 10% | Secondhand Goods | CashNet |
| NEW/NS/OS | 10% | New Stock Bought In | PosWiz/CashNet |
| NSF | 0% | New GST Free | PosWiz/CashNet |
| OL | 0% | Old Loan Pledge Stock | CashNet |
| SHF | 0% | Secondhand GST Free | CashNet |
| EX | 10% | Exempt Download Item | CashNet |
| AUC | 10% | Auction Stock | CashNet |
| IMP | 10% | Imported from Overseas | CashNet |

### tblMoveType — Second-Hand Item Disposal Codes [V]
Pawnbroker compliance codes including: Redeemed, Seized By Police, 21/56 Day Stop Dealing Notice,
SOLD Second Hand Goods, SOLD Forfeited Goods, Defaulted, Bankrupt, Repaid, Auction, EBay Auction.
System vendor: **ComWiz / ProCreate HQ**.

---

## 25/04/2026 — Discovery: PayType Code Map, tblSaleItem.RefNo, Data Migration Boundary

### Data migration boundary [V]
cwserver (ProCreate/PosWiz/CashNet) went live **August 2020**, migrating from **PawnIt** (in use 2013–Jul/Aug 2020).
All data with `tblSale.Time_Stamp < 2020-08-01` is imported from PawnIt (dates preserved).
PayType codes in pre-2020 records may reflect PawnIt's conventions. PayTypes 3, 6, 7 first appear
post-August 2020 — they are cwserver-native codes. PayType 8 exists in both eras.

**Stock migration artefact (pre-Aug 2020 only):** Second-hand items from the old system were
imported with a duplicated record — one with a new cwserver StockID and one with an 'INV'-prefixed
stock number carrying fragmented data. Post-August 2020: 'INV' prefix in tblSaleItem.StockID is
NOT a migration artefact — it denotes new stock received from a supplier invoice (legitimate usage).
Note: No INV-prefixed StockIDs remain in tblSaleItem or tblTranItems as of 25/04/2026.

### PayType code map — confirmed [V] [26/04/2026]
PosWiz stores payment method as an integer in tblPayments.PayType. No lookup table exists in the DB.
`tblReceiptInfo.PayCode` is the stock ORIGIN code (NEW/OS/GST etc.), NOT a payment method label.

**Important:** PosWiz labels ALL online orders as "(PayPal)" regardless of actual gateway
(PayPal, Shopify Payments, Afterpay online, Zip online). All online orders share PayType 8 in
the DB. Gateway disambiguation requires paypal_sales_extract.py cross-reference against gateway CSVs.
Q2 FY26 breakdown: Shopify Payments 142, PayPal 60, Afterpay 33, ZipPay 3 (from paypal_sales_v2.csv).

**ANZ bank settlement by PayType:**
- PayType 0 (Cash) → Cash on Hand account (no ANZ line per transaction)
- PayType 2+3 (EFTPos + AMEX) → First Data / FDSMA single daily settlement batch on ANZ
- PayType 5+7 (Credit note/Voucher) → Xero account 808 (CURRLIAB); NO bank movement; manual journal
- PayType 6 (Bank Transfer) → direct ANZ transfer; appears as "Other" in banking summary
- PayType 8 (Online/"PayPal") → four separate ANZ lines: TRANSFER FROM PAYPAL / SHOPIFY / AFTERPAY / ZIPMONEY

| Code | Count | Status | Method | Evidence |
|------|-------|--------|--------|----------|
| 0 | 7,464 | [V] | Cash | Tendered column always populated; Tendered=NULL for all other types |
| 1 | 2 | [R] | Cheque | Only 2 rows; matches "Cheque" in banking_summary_parser regex |
| 2 | 22,990 | [V] | EFTPos/Card (all brands — integrated) | Tendered=NULL; all card brands (Visa/MC/Amex) settle via First Data (FDSMA) in one batch |
| 3 | 142 | [V] | AMEX button in PosWiz (staff error) | Sep 2020–Aug 2025; untrained staff using separate AMEX button; settles in same First Data batch as PayType 2; treat as PayType 2 for reconciliation |
| 4 | 3 | [?] | Unknown (rare) | Dec 2020 only — 3 rows total |
| 5 | 99 | [V] | Credit note / gift voucher (pre-Jul 2021) | 98 payments; superseded by PayType 7; no bank movement; Xero account 808 |
| 6 | 463 | [R] | Direct Bank Transfer / EFT | Max $11,000; appears on loans (3) and refunds (49); banking_summary "Other/Bank" |
| 7 | 102 | [V] | Credit note / gift voucher (Mar 2022–present) | Same function as PayType 5; both PosWiz buttons always existed; usage shift = staff turnover artefact; no bank movement; Xero account 808 |
| 8 | 1,710 | [V] | Online / "(PayPal)" — ALL gateways | All Afterpay/ZipPay/PayPal/Shopify online go through one "PayPal" PosWiz button; gateway disambiguation requires paypal_sales_extract.py |
| 9 | 3 | [?] | Unknown (rare) | Nov 2020–Mar 2023 only — 3 rows total |

### tblSaleItem.RefNo — item provenance field [V]
NOT a payment reference. Encodes where the sold item came from:
- `'INV'` — new stock from supplier invoice (post-Aug 2020 usage)
- `'B######'` (e.g. B26000027) — second-hand item bought from public; links to tblTran.RefNo where RefType='B'
- `NULL` / empty — pre-migration imported records (StockID also often NULL for these)

59,881 of 59,996 tblSaleItem rows have RefNo populated. Only 115 are NULL/empty.

### PosWiz CSV field mapping → tblSale/tblSaleItem [V/R]
From poswiz_parser.py regex (Sale Item Summary PDF format):
| PDF field | Maps to | Table | Notes |
|-----------|---------|-------|-------|
| Sale # (e.g. S25K1) | SaleNo | tblSale | Primary grouping key |
| Date (01-Nov-25) | Time_Stamp (date) | tblSale | |
| StockID | StockID | tblSaleItem | Numeric; links to tblTranItems (s/h) or tblTranItems (new) |
| Sell price × Qty | Amount | tblSaleItem | [R] |
| Qty | Qty | tblSaleItem | |
| Description | Article | tblTranItems | |
| Cost | ItemCost | tblTranItems | [R] |

Year+month encoding in RefNos: prefix letter (S/X/B/L/C) + 2-digit year + letter month (A=Jan…) + sequence.
Older records use prefix + sequential number without month encoding (e.g. L114, L115).

---

## 26/04/2026 — Discovery: PayType Map Fully Resolved + tblDodgy + Pre-2020 Stock Artefact (Session 4)

### Correction: PayType 5 was NOT credit note/gift voucher

PayType 5 was recorded as [V] credit note/gift voucher in Session 3. That was an **inference** from the PayType 7 verification (sale S26C249 PosWiz lookup) — not a direct verification of any PayType 5 record. Incorrect confidence tag was applied.

**Corrected via PosWiz UI (store owner confirmed):** PosWiz payment buttons are sequential, 0-indexed from the top (position 1 = Cash = PayType 0). PayType 5 = MasterCard button. PayType 4 = VISA button. Both were separate card-brand buttons prior to EFTPOS integration. First Data (FDSMA) integrated provider consolidated all card brands under PayType 2 from mid-2021 — PayType 4 and 5 stopped being used at that point. [V]

### Fully resolved PayType code map — all codes [V]

| Code | Count | Method | Notes |
|------|-------|--------|-------|
| 0 | 7,464 | Cash | Tendered always populated |
| 1 | 2 | Cheque | Legacy button; almost never used |
| 2 | 22,990 | EFTPOS / Card (all brands — integrated) | All card types settle via First Data (FDSMA) since mid-2021 |
| 3 | 142 | AMEX button (PosWiz UI artefact) | Settles in same First Data batch as PayType 2; treat as PayType 2 for reconciliation |
| 4 | 3 | VISA (pre-integration only) | Dec 2020 only; consolidated under PayType 2 from mid-2021 |
| 5 | 99 | MasterCard (pre-integration only) | Pre-Jul 2021; consolidated under PayType 2 from mid-2021; settles via First Data same as PayType 2+3 |
| 6 | 463 | Direct bank transfer / EFT | Max $11K; on loans and refunds |
| 7 | 102 | Credit note / gift voucher | Mar 2022–present; no bank movement; Xero account 808 |
| 8 | 1,710 | Online / "(PayPal)" — ALL gateways | PayPal + Shopify Payments + Afterpay + ZipPay via single "PayPal" PosWiz button |
| 9 | 3 | Other credit card | 3 rows total |

**EFTPOS integration timeline:** Pre-mid-2021, VISA (PayType 4), MasterCard (PayType 5), and AMEX (PayType 3) each had a dedicated PosWiz button. After First Data (FDSMA) integration, all card brands consolidated under PayType 2. PayType 4 and 5 went dormant; PayType 3 (AMEX) persisted due to staff habit but routes through the same settlement batch.

**Corrected ANZ bank settlement mapping:**
- PayType 0 (Cash) → Cash on Hand; no ANZ line
- PayType 2+3 → First Data (FDSMA) daily EFTPOS batch (PayType 4+5 also routed here pre-mid-2021 — historical only)
- PayType 6 (Bank Transfer) → direct ANZ EFT
- PayType 7 (Credit note/Voucher) → NO bank movement; Xero account 808 (CURRLIAB); manual journal only
- PayType 8 (Online) → four ANZ streams: TRANSFER FROM PAYPAL / SHOPIFY / AFTERPAY / ZIPMONEY

### tblDodgy — inter-store customer watchlist [V]

19 rows. ProCreate network feature originally designed for flagging customers across stores in the same network. SSG uses it loosely — some genuine alerts (e.g. stolen goods), most are general customer notes. Links to `tblCustSupp.NameID` via WarnText field. Has interstore columns (bit + InterstoreAmmend + InterstoreID) confirming cross-store sync design. **NOT transaction anomaly data. No reconciliation query impact.**

### Pre-2020 StockID=NULL — PawnIt migration artefact confirmed [V]

PawnIt→CWServer migration (Aug 2020) duplicated ~11,000 second-hand stock items into ~22,000 records. Each original item produced two rows:
- **Numerical StockID** — correct CWServer second-hand record
- **INV-prefix StockID** — incorrectly typed as new supplier stock (no QLD Second Hand Dealers Act tracking obligation)

The INV-prefix duplication explains StockID=NULL and orphaned rows in tblSaleItem for pre-Aug 2020 data. Post-Aug 2020: INV prefix in tblSaleItem.StockID is legitimate (new stock from supplier invoice, not a migration artefact).

---
