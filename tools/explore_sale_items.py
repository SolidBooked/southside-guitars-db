"""
explore_sale_items.py
=====================
Inspect tblSaleItem structure and data for a given date range.

Usage:
    python tools/explore_sale_items.py
    python tools/explore_sale_items.py --start 2025-10-01 --end 2026-01-01
    python tools/explore_sale_items.py --start 2026-01-01 --end 2026-04-01 --sample 10
    python tools/explore_sale_items.py --stockid 24554

Outputs (all to stdout):
  1. Origin distribution + totals
  2. RefNo pattern distribution (B/L/C/INV/OS-* etc.)
  3. Account code preview (200/201/808 per classification rules)
  4. Sample rows
  5. StockID lookup (if --stockid supplied)
  6. Loan items (L-prefix RefNo) — rare seized pawn items
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection, query_df


def origin_distribution(conn, start: str, end: str) -> None:
    print(f"\n=== Origin distribution ({start} to {end}) ===")
    df = query_df(conn, """
        SELECT si.Origin,
               COUNT(*)       AS row_count,
               SUM(si.Amount) AS total_amount
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        GROUP BY si.Origin
        ORDER BY row_count DESC
    """, [start, end])
    print(df.to_string(index=False))


def refno_pattern_distribution(conn, start: str, end: str) -> None:
    print(f"\n=== RefNo pattern distribution ({start} to {end}) ===")
    df = query_df(conn, """
        SELECT
            CASE
                WHEN si.RefNo LIKE 'B%'   THEN 'B-prefix  (bought-in s/h)'
                WHEN si.RefNo LIKE 'L%'   THEN 'L-prefix  (pawn loan — acct 201)'
                WHEN si.RefNo LIKE 'C%'   THEN 'C-prefix  (consignment)'
                WHEN si.RefNo LIKE 'INV%' THEN 'INV       (supplier stock)'
                WHEN si.RefNo LIKE 'OS-%' THEN 'OS-*      (other stock, ad-hoc)'
                ELSE 'other: ' + ISNULL(si.RefNo, 'NULL')
            END AS refno_pattern,
            si.Origin,
            COUNT(*)       AS cnt,
            SUM(si.Amount) AS total
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        GROUP BY
            CASE
                WHEN si.RefNo LIKE 'B%'   THEN 'B-prefix  (bought-in s/h)'
                WHEN si.RefNo LIKE 'L%'   THEN 'L-prefix  (pawn loan — acct 201)'
                WHEN si.RefNo LIKE 'C%'   THEN 'C-prefix  (consignment)'
                WHEN si.RefNo LIKE 'INV%' THEN 'INV       (supplier stock)'
                WHEN si.RefNo LIKE 'OS-%' THEN 'OS-*      (other stock, ad-hoc)'
                ELSE 'other: ' + ISNULL(si.RefNo, 'NULL')
            END,
            si.Origin
        ORDER BY cnt DESC
    """, [start, end])
    print(df.to_string(index=False))


def account_code_preview(conn, start: str, end: str) -> None:
    print(f"\n=== Account code classification preview ({start} to {end}) ===")
    print("  Rule: GFS/StockID=24554 -> 808 | L-prefix RefNo -> 201 | else -> 200")
    df = query_df(conn, """
        SELECT
            CASE
                WHEN si.Origin = 'GFS' OR si.StockID = 24554 THEN '808 (voucher)'
                WHEN si.RefNo LIKE 'L%'                       THEN '201 (exempt — seized pawn)'
                ELSE                                               '200 (GST sale)'
            END AS account_code,
            COUNT(*)       AS row_count,
            SUM(si.Amount) AS total_amount
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        GROUP BY
            CASE
                WHEN si.Origin = 'GFS' OR si.StockID = 24554 THEN '808 (voucher)'
                WHEN si.RefNo LIKE 'L%'                       THEN '201 (exempt — seized pawn)'
                ELSE                                               '200 (GST sale)'
            END
        ORDER BY account_code
    """, [start, end])
    print(df.to_string(index=False))


def sample_rows(conn, start: str, end: str, n: int) -> None:
    print(f"\n=== Sample rows — {n} rows ({start} to {end}) ===")
    df = query_df(conn, f"""
        SELECT TOP {n}
            CAST(s.Time_Stamp AS DATE) AS sale_date,
            si.SaleNo, si.RefNo, si.StockID, si.Origin,
            si.Qty, si.Amount, si.Comment
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        ORDER BY s.Time_Stamp
    """, [start, end])
    print(df.to_string(index=False))


def loan_items(conn, start: str, end: str) -> None:
    print(f"\n=== Loan items (L-prefix RefNo, acct 201) — {start} to {end} ===")
    df = query_df(conn, """
        SELECT
            CAST(s.Time_Stamp AS DATE) AS sale_date,
            si.SaleNo, si.RefNo, si.StockID, si.Origin,
            si.Qty, si.Amount, si.Comment
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND si.RefNo LIKE 'L%'
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        ORDER BY s.Time_Stamp
    """, [start, end])
    if df.empty:
        print("  (none found — as expected, these are rare)")
    else:
        print(df.to_string(index=False))


def stockid_lookup(conn, stock_id: int, start: str, end: str) -> None:
    print(f"\n=== StockID {stock_id} rows ({start} to {end}) ===")
    df = query_df(conn, """
        SELECT
            CAST(s.Time_Stamp AS DATE) AS sale_date,
            si.SaleNo, si.RefNo, si.StockID, si.Origin,
            si.Qty, si.Amount, si.Comment
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND si.StockID = ?
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        ORDER BY s.Time_Stamp
    """, [stock_id, start, end])
    if df.empty:
        print(f"  (no rows for StockID {stock_id} in range)")
    else:
        print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="Explore tblSaleItem for a date range")
    parser.add_argument("--start",   default="2025-10-01", help="Start date (inclusive) YYYY-MM-DD")
    parser.add_argument("--end",     default="2026-01-01", help="End date (exclusive) YYYY-MM-DD")
    parser.add_argument("--sample",  type=int, default=5,  help="Number of sample rows to show")
    parser.add_argument("--stockid", type=int, default=None, help="Look up a specific StockID")
    args = parser.parse_args()

    conn = get_connection()

    origin_distribution(conn, args.start, args.end)
    refno_pattern_distribution(conn, args.start, args.end)
    account_code_preview(conn, args.start, args.end)
    sample_rows(conn, args.start, args.end, args.sample)
    loan_items(conn, args.start, args.end)

    if args.stockid is not None:
        stockid_lookup(conn, args.stockid, args.start, args.end)

    conn.close()


if __name__ == "__main__":
    main()
