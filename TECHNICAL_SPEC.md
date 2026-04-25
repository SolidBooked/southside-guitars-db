# Technical Specification — CWServer Database
_Living document. Updated as schema exploration progresses._

---

## 1. System Overview

**System name:** cwserver  
**Purpose:** Unified operational backend for Southside Guitars' point-of-sale, online sales,
and financial management. Powers three front-end modules:

| Module | Role |
|--------|------|
| PosWiz | In-store POS — sales, repairs, layby, inventory |
| CashNet | Web/online sales and payment processing |
| PayWiz | Payment management and reporting |

**Database engine:** Microsoft SQL Server 2016 Express (v13.x)  
**Instance:** `.\SQLEXPRESS` (MSSQL13.SQLEXPRESS)  
**Database:** `CWServer`  
**Auth:** Windows Authentication  
**Database file:** `C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS\MSSQL\DATA\CWServer.mdf`

---

## 2. Table Inventory

Total: 82 base tables (as of 25/04/2026). All in `dbo` schema.

### Active tables (non-zero rows)

| Table | Rows | Purpose |
|-------|------|---------|
| tblSaleItem | 59,996 | POS sale line items |
| tblLog | 58,793 | Audit/activity log |
| tblReceiptInfo | 57,197 | Receipt records (likely per payment method) |
| tblTranItems | 33,680 | Transaction line items (for tblTran — not POS sales) |
| tblPayments | 32,978 | Payment records |
| tblSale | 30,768 | POS sales header |
| tblPostCode | 16,875 | Postcode lookup |
| tblArticleCustom | 14,314 | Custom product fields |
| tblCustSupp | 10,728 | Customer and supplier master |
| tblArticle | 7,060 | Product catalog (primary — NOT tblProducts) |
| tblID | 5,600 | Identity/sequence table |
| tblAddrHist | 4,674 | Address history |
| tblTran | 4,533 | Transactions — type TBD (not POS sales) |
| tblNotes | 3,460 | Notes/comments |
| tblCashMove | 2,723 | Cash movements |
| tblHistory | 1,992 | Record history |
| tblRefundItem | 1,468 | Refund line items |
| tblBarcode | 1,399 | Barcode records |
| tblRevisions | 1,359 | Data revisions |
| tblRefund | 1,136 | Refund headers |
| tblRepairs | 975 | Repair jobs |
| tblBalance | 640 | Balance records |
| tblWording | 170 | UI/print wording config |
| tblVoucher | 99 | Gift vouchers |
| tblJewellery | 56 | Jewellery-specific data |
| tblStaffAccess | 54 | Staff permissions |
| tblStaff | 33 | Staff records |
| tblMoveType | 23 | Movement type codes |
| tblDodgy | 19 | Flagged transactions |
| tblDDRPayMethods | 17 | DDR payment method codes |
| tblColour | 15 | Colour codes |
| tblPayTimes | 14 | Pay period times |
| tblOrigin | 13 | Origin codes |
| tblTranItemsIdentify | 9 | Transaction item identifiers |
| tblProducts | 6 | Product groups/kits (NOT the main catalog) |
| tblUnitofMeasure | 6 | Units of measure |
| tblReason | 5 | Reason codes |
| tblRepairStatusList | 5 | Repair status options |
| tblRepairParts | 4 | Parts used in repairs |
| tblTills | 3 | Till/register config |
| tblRecordInfo | 2 | Record metadata |
| tblStoreRouting | 2 | Store routing config |
| tblAdminCashNET | 1 | CashNet config |
| tblAdminPayWiz | 1 | PayWiz config |
| tblAdminPOSWiz | 1 | PosWiz config |
| tblCategory | 1 | Product categories |
| tblHoldInfo | 1 | Hold config |
| tblPayEmpDetails | 1 | Employee pay details |
| tblStoreInfo | 1 | Store information |

### Empty tables (0 rows — features not in active use)
`tblAccChart`, `tblAccReceipts`, `tblAdminTracker`, `tblAuction`, `tblAuctionBidders`,
`tblAuctionItems`, `tblBankFeeds`, `tblBarcodesExcluded`, `tblCart`, `tblCartItems`,
`tblCategoryCustom`, `tblCCWebCategory`, `tblChaseItems`, `tblCheqCash`,
`tblComponentTemplates`, `tblCWRA`, `tblDDR`, `tblDiscounts`, `tblInvProcesses`,
`tblJournal`, `tblMarkets`, `tblOtherCharges`, `tblPaySheets`, `tblPayYTD`,
`tblPettyCash`, `tblPostage`, `tblQuickQuotePrices`, `tblQuoteItems`, `tblQuotes`,
`tblTestAddress`, `tblTestCustSupp`, `tblTestCustSuppAddress`, `tblWeightsItem`

---

## 3. Architecture — Two Transaction Subsystems

cwserver manages two distinct transaction workflows with separate table sets:

### Subsystem A: Retail Sales (PosWiz POS)
```
tblSale          ← sale header (immediate sales + layby)
tblSaleItem      ← sale line items (RefNo='INV' = new stock; RefNo='B######' = s/h bought-in)
tblPayments      ← payment records (RefType='S' → tblSale, 'X' → tblRefund, 'L' → tblTran[loan])
tblReceiptInfo   ← receipt lines with GST breakdown (same RefType/RefNo as tblPayments)
```

### Subsystem B: Second-Hand Goods / Pawnbroker (CashNet)
```
tblTran          ← transaction header; RefType: B=Buy(4,211), L=Loan(301), C=Consignment(21)
tblTranItems     ← individual second-hand stock items (one row per physical item)
tblRefund        ← refund records; RefNo uses X-prefix (e.g. X26A9); links via tblRefundItem.SaleNo
```

**tblPayments RefType confirmed [V]:**
- `S` → tblSale.SaleNo (retail sales)
- `X` → tblRefund.RefNo (refund payouts — cash/card back to customer)
- `L` → tblTran.RefNo where tblTran.RefType='L' (loan/pawn redemption payments)

**tblTran.RefType='B' (Buy) cash payouts** are NOT in tblPayments — tracked via tblCashMove ('Retail → Buys/Loans').

### Shared Infrastructure
```
tblCustSupp      ← customer and supplier master
tblArticle       ← new product catalog (7,060 products)
tblCashMove      ← daily cash movements (till ↔ bank ↔ safe ↔ buys/loans)
tblRepairs       ← guitar repair jobs
tblVoucher       ← gift vouchers
tblWording       ← key-value system config + per-item notes
```

## 4. Key Table Columns

### tblSale — POS Sales Header
| Column | Type | Notes |
|--------|------|-------|
| SaleNo | nvarchar(10) | Primary sale identifier |
| NameID | bigint | Customer FK → tblCustSupp |
| Amount | float | Total sale value |
| Paid | float | Amount paid to date |
| Settled | bit | 1=complete, 0=layby outstanding |
| SettleDate | datetime | When fully paid |
| Term/TermUnit | int/nvarchar | Layby terms |
| NextPayDate | datetime | Next layby instalment |
| PlacedBy | nvarchar(6) | Staff PIN |
| Time_Stamp | datetime | Created datetime |
| StoreNo | int | Always 224 (Southside Guitars) |

### tblPayments — Payment Records
| Column | Type | Notes |
|--------|------|-------|
| ReceiptNo | nvarchar(9) | FK → tblReceiptInfo |
| RefType + RefNo | nvarchar | S+SaleNo links to tblSale |
| PayType | int | Payment method (see lookup below) |
| Amount | float | Payment amount |
| Tendered | float | Cash tendered |
| PayRef | nvarchar | NULL — no card auth captured |
| VoucherNo | nvarchar | FK → tblVoucher if voucher payment |

### PayType Code Map
No lookup table in DB. tblReceiptInfo.PayCode = stock ORIGIN code (NEW/OS/GST), NOT payment method.
All online gateways (PayPal, Shopify, Afterpay online, Zip online) share PayType 8 — PosWiz labels
all online orders "(PayPal)". Gateway disambiguation requires paypal_sales_extract.py output.
Q2 FY26 gateway breakdown: Shopify Payments 142, PayPal 60, Afterpay 33, ZipPay 3.

**ANZ bank settlement by PayType:**
PayType 2+3 → First Data (FDSMA) daily batch. PayType 5+7 → no ANZ movement (Xero account 808).
PayType 6 → direct EFT. PayType 8 → four separate ANZ streams (PayPal/Shopify/Afterpay/Zip).

| Code | Count | Method | Confidence |
|------|-------|--------|-----------|
| 0 | 7,464 | Cash | [V] Tendered always populated |
| 1 | 2 | Cheque | [R] Only 2 rows; matches banking_summary regex |
| 2 | 22,990 | EFTPos / Card (all brands — integrated) | [V] All card types settle via First Data (FDSMA) |
| 3 | 142 | AMEX button (PosWiz staff error) | [V] Untrained staff; settles in same First Data batch as PayType 2; treat as PayType 2 for recon |
| 4 | 3 | Unknown (rare — Dec 2020 only) | [?] |
| 5 | 99 | Credit note / gift voucher (pre-Jul 2021) | [V] No bank movement; Xero account 808 |
| 6 | 463 | Direct Bank Transfer / EFT | [R] Max $11K; on loans and refunds; maps to banking_summary "Other/Bank" |
| 7 | 102 | Credit note / gift voucher (Mar 2022–present) | [V] Same function as PayType 5; staff turnover artefact; no bank movement; Xero account 808 |
| 8 | 1,710 | Online / "(PayPal)" — ALL gateways | [V] Confirmed by cross-ref with paypal_sales_v2.csv |
| 9 | 3 | Unknown (rare) | [?] Nov 2020–Mar 2023 |

### tblReceiptInfo — Receipt Lines (GST pre-calculated)
| Column | Type | Notes |
|--------|------|-------|
| ReceiptNo | nvarchar(9) | Receipt identifier |
| RefType + RefNo | nvarchar | Links to tblSale or tblTran |
| GSTAmount | float | Pre-calculated GST per line ← tax reconciliation |
| RecTotalAmount | float | Receipt total |
| Principle / Interest / FeesCharges | float | Layby/loan payment breakdown |

### tblTranItems — Second-Hand Stock Items
Each row = one physical second-hand item. Key fields:
`RefNo` (→tblTran), `StockID`, `Article`, `MakeArtist`, `ModelTitle`, `SerialNo`,
`Barcode`, `InStock`, `OnShelf`, `Qty`, `QtySold`, `PriceSold`, `SellerID`,
`Origin` (GST), `RRPrice1-5` (price tiers), `ShowOnWeb`, `PoliceDataSent`, `ItemCost`

## 5. Known Module Mappings

### tblSaleItem — full column map [V]
| Column | Type | Notes |
|--------|------|-------|
| SaleItemID | — | Row identifier |
| StoreNo | int | Always 224 |
| SaleNo | nvarchar | FK → tblSale.SaleNo |
| RefNo | nvarchar | Item provenance: 'INV'=supplier stock, 'B######'=bought-in s/h (→tblTran) |
| StockID | nvarchar | Numeric item ID → tblTranItems.StockID; NULL on 8,869 pre-migration rows |
| Origin | nvarchar(3) | GST treatment → tblOrigin (NEW/OS/GST/OL/NSF etc.) |
| Qty | float | Quantity sold |
| Amount | float | Line total (Sell price × Qty) |
| Comment | nvarchar | Optional note |
| Deleted | bit | Soft-delete flag |

### PosWiz Sale Item Summary PDF → DB field mapping
| PDF field | DB column | Table | Confidence |
|-----------|-----------|-------|-----------|
| Sale # (e.g. S25K1) | SaleNo | tblSale | [V] |
| Date (01-Nov-25) | Time_Stamp (date part) | tblSale | [V] |
| StockID | StockID | tblSaleItem | [V] |
| Sell price | Amount ÷ Qty | tblSaleItem | [R] |
| Qty | Qty | tblSaleItem | [V] |
| Description | Article | tblTranItems | [R] |
| Cost | ItemCost | tblTranItems | [R] |

### Data migration boundary
- **Prior system:** PawnIt (2013–Jul/Aug 2020). Data migrated into CWServer at cutover.
- **Pre-August 2020 records:** imported from PawnIt; dates preserved. PayType codes may reflect PawnIt conventions. StockID often NULL on tblSaleItem rows from this period (migration artefact).
- **Post-August 2020:** live CWServer/PosWiz/CashNet (ProCreate vendor) operations. PayType 3, 6, 7 first appear here.
- PayType 3 active Sep 2020 – Aug 2025 (staff gradually stopped using wrong button). PayType 7 active from Mar 2022 onwards.

---

## 5. Connection & Tooling

### sqlcmd
```
C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
  -S .\SQLEXPRESS -d CWServer -E -Q "<query>"
```

### Python
```python
# db.py get_connection() uses:
DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE=CWServer;Trusted_Connection=yes
```

### ODBC Driver location
Installed at: `C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\`

---

## 6. Data Quality Notes

_To be populated as issues are discovered during exploration._

---

## 7. System Details

| Detail | Value |
|--------|-------|
| Store number | 224 |
| Server | SALISBURYSERVER (`192.168.1.99`) |
| Client machines | `192.168.68.x` subnet |
| Police reporting | Second Hand Dealers Act (QLD) — files to `c:\policefiles` |
| Last police send | 14/03/2026 |
| Backup destination | OneDrive: `C:\Users\Southside Guitars\OneDrive\CWSever` |
| System vendor | ComWiz / ProCreate HQ |
| Data history | 2013-10-23 to present |

## 8. Changelog

| Date | Change |
|------|--------|
| 25/04/2026 | Initial spec created. 82 tables confirmed. Connection details verified. |
| 25/04/2026 | Column exploration complete. Two-subsystem architecture documented. PayType map drafted. |
| 25/04/2026 | PayType codes confirmed via Tendered column and paypal_sales_v2.csv cross-reference. RefType=X→tblRefund, RefType=L→tblTran(loan) confirmed. tblSaleItem.RefNo purpose identified. Migration boundary documented. |
| 26/04/2026 | PayType 3=AMEX (V), PayType 5+7=credit note/gift voucher (V) confirmed via PosWiz lookup. Prior system PawnIt (2013–2020) documented. ANZ bank settlement mapping per PayType added. SSG reconciliation cross-reference completed. |
