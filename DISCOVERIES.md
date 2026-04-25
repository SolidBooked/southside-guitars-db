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
- Column structure of `tblTran` and `tblTranItems`
- Row counts to identify data volume and most active tables
- Whether `tblBankFeeds` contains bank transaction data or is unused

---
