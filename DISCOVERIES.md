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
- Column structure of `tblSale` and `tblSaleItem` vs PosWiz CSV export fields
- Column structure of `tblTran` to determine what it actually stores
- What `tblReceiptInfo` contains — is it the payment method split per sale?

---
