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
tblSaleItem      ← sale line items (links to tblTranItems for s/h stock, tblArticle for new)
tblPayments      ← payment records (RefType=S links to tblSale.SaleNo)
tblReceiptInfo   ← receipt lines with GST breakdown (RefType=S)
```

### Subsystem B: Second-Hand Goods / Pawnbroker (CashNet)
```
tblTran          ← pawn/consignment transaction header (police reporting)
tblTranItems     ← individual second-hand stock items (one row per physical item)
```
Note: tblTran payments may flow through tblPayments via an unknown RefType (X or L).

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

### PayType Code Map (inferred — confirm via CSV cross-reference)
| Code | Count | Inferred Method |
|------|-------|-----------------|
| 0 | 7,464 | Cash [?] |
| 1 | 2 | Cheque/EFT [?] |
| 2 | 22,990 | EFTPOS/Card [?] |
| 3 | 142 | Unknown [?] |
| 4 | 3 | Unknown [?] |
| 5 | 99 | Gift Voucher [R] |
| 6 | 463 | Unknown [?] |
| 7 | 102 | PayPal/Online [?] |
| 8 | 1,710 | Afterpay/BNPL [?] |
| 9 | 3 | Unknown [?] |

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

_To be populated via CSV cross-reference in future sessions._

**Target:** map `tblSale.SaleNo` + `tblSaleItem` + `tblPayments.PayType` → PosWiz CSV columns

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
