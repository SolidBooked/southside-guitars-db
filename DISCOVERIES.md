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
| tblDodgy | 19 | Flagged/suspicious transactions |

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
| RefType | tblPayments | tblReceiptInfo | Likely meaning |
|---------|-------------|----------------|----------------|
| S | 31,672 | 55,662 | Sale (tblSale) |
| X | 1,068 | 1,299 | Unknown — TBD |
| L | 238 | 236 | Layby? or Loan? — TBD |

Note: No `T` (Tran) type in payments/receipts — tblTran payments may flow through a different mechanism.

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
