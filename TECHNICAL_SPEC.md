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

_Full table list with row counts to be populated after first `--counts` run._

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
