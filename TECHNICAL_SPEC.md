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

## 3. Key Table Specifications

_To be populated as columns are explored._

### tblTran
_Primary POS transaction table — TBD_

### tblTranItems
_Transaction line items — TBD_

### tblSale
_TBD — relationship to tblTran unclear until columns examined_

### tblPayments
_Payment records — TBD_

### tblBankFeeds
_Bank feed data — TBD — unknown if populated_

---

## 4. Known Module Mappings

_To be populated as queries are developed. Goal: map cwserver fields → PosWiz CSV columns → Cashnet CSV columns._

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

## 7. Changelog

| Date | Change |
|------|--------|
| 25/04/2026 | Initial spec created. 82 tables confirmed. Connection details verified. |
