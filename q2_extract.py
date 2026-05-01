"""
q2_extract.py -- CWServer Q2 FY26 data extraction for SSG reconciliation.

Covers PosWiz sales payments and CashNet second-hand buys for Oct-Dec 2025.
Output: Q2_FY26_Extract.xlsx (5 sheets)

Sheets:
  PosWiz_Payments  -- one row per payment transaction (raw, transaction-level)
  PosWiz_GST       -- GST per sale from tblReceiptInfo
  PosWiz_Daily     -- daily summary by PayType + GST (ready for Xero invoice building)
  CashNet_Buys     -- one row per B-number with classified payment method
  CashNet_Daily    -- daily buy summary: cash / bank transfer / total
"""
import re
import sys
import pandas as pd
from db import get_connection, query_df

Q2_START = "2025-10-01"
Q2_END   = "2026-01-01"  # exclusive

PAYTYPE_LABELS = {
    0: "Cash",
    1: "Cheque",
    2: "EFTPOS/Card",
    3: "EFTPOS/Card (AMEX btn)",
    4: "VISA (pre-integration)",
    5: "MasterCard (pre-integration)",
    6: "Bank Transfer",
    7: "Credit Note/Voucher",
    8: "Online (undifferentiated)",
    9: "Other Credit Card",
}

# PayTypes 2+3 settle together via First Data/FDSMA.
# 4+5 are pre-integration legacy (minimal Q2 rows expected).
EFTPOS_POOL = {2, 3, 4, 5}


def pull_poswiz_payments(conn):
    sql = """
        SELECT
            CAST(p.Time_Stamp AS DATE)  AS trading_date,
            p.RefNo                     AS sale_no,
            p.PayType                   AS pay_type,
            p.Amount                    AS payment_amount,
            p.Tendered                  AS tendered,
            p.PayRef                    AS pay_ref,
            s.Amount                    AS sale_total,
            s.Settled                   AS is_settled,
            s.Time_Stamp                AS sale_timestamp
        FROM tblPayments p
        LEFT JOIN tblSale s
               ON p.RefNo  = s.SaleNo
              AND p.RefType = 'S'
        WHERE p.Deleted  = 0
          AND p.RefType  = 'S'
          AND p.Time_Stamp >= ? AND p.Time_Stamp < ?
        ORDER BY trading_date, p.RefNo, p.PayType
    """
    df = query_df(conn, sql, [Q2_START, Q2_END])
    df["pay_type_label"] = df["pay_type"].map(PAYTYPE_LABELS).fillna("Unknown")
    df["eftpos_pool"]    = df["pay_type"].isin(EFTPOS_POOL)
    return df


def pull_poswiz_gst(conn):
    sql = """
        SELECT
            CAST(r.Time_Stamp AS DATE) AS trading_date,
            r.RefNo                    AS sale_no,
            SUM(r.GSTAmount)           AS gst_amount,
            SUM(r.SeqTotal)            AS line_total
        FROM tblReceiptInfo r
        WHERE r.Deleted  = 0
          AND r.RefType  = 'S'
          AND r.Time_Stamp >= ? AND r.Time_Stamp < ?
        GROUP BY CAST(r.Time_Stamp AS DATE), r.RefNo
        ORDER BY trading_date, r.RefNo
    """
    return query_df(conn, sql, [Q2_START, Q2_END])


def pull_cashnet_buys(conn):
    # Amount > 0 excludes voided buys (e.g. B25000306, B25000314 in Q2)
    sql = """
        SELECT
            t.RefNo                  AS b_number,
            CAST(t.TranDate AS DATE) AS tran_date,
            t.Amount                 AS buy_amount
        FROM tblTran t
        WHERE t.RefType = 'B'
          AND t.Deleted = 0
          AND t.Amount  > 0
          AND t.TranDate >= ? AND t.TranDate < ?
        ORDER BY t.TranDate, t.RefNo
    """
    return query_df(conn, sql, [Q2_START, Q2_END])


def pull_cashnet_movements(conn):
    sql = """
        SELECT
            CAST(cm.Time_Stamp AS DATE) AS move_date,
            cm.FromType,
            cm.Amount                   AS move_amount,
            cm.Reason
        FROM tblCashMove cm
        WHERE cm.Deleted = 0
          AND cm.ToType  = 'Buys/Loans'
          AND cm.Time_Stamp >= ? AND cm.Time_Stamp < ?
        ORDER BY cm.Time_Stamp
    """
    return query_df(conn, sql, [Q2_START, Q2_END])


def classify_buy_payment(buys: pd.DataFrame, movements: pd.DataFrame) -> pd.DataFrame:
    """
    3-pass matching (mirrors cashnet_parser.py logic):
      Pass 1 -- B-number (case-insensitive) found in CM Reason, same date.
      Pass 2 -- same date + amount match (handles CM B-number typos).
      Pass 3 -- default to Cash (no CM record found).
    FromType='Retail' -> Cash; FromType='Bank' -> Bank Transfer.
    """
    buys = buys.copy()
    buys["payment_method"] = "Cash"
    buys["cm_match_pass"]  = 3  # audit column: which pass resolved the match

    matched_cm = set()

    def from_type_to_method(from_type: str) -> str:
        return "Bank Transfer" if from_type == "Bank" else "Cash"

    # Pass 1
    for idx, buy in buys.iterrows():
        b = re.escape(buy["b_number"].upper())
        d = buy["tran_date"]
        mask = (
            (movements["move_date"] == d) &
            movements["Reason"].str.upper().str.contains(b, na=False) &
            ~movements.index.isin(matched_cm)
        )
        hits = movements[mask]
        if not hits.empty:
            cm_idx = hits.index[0]
            matched_cm.add(cm_idx)
            buys.at[idx, "payment_method"] = from_type_to_method(hits.at[cm_idx, "FromType"])
            buys.at[idx, "cm_match_pass"]  = 1

    # Pass 2 -- fuzzy on remaining unmatched buys
    unmatched = buys[buys["cm_match_pass"] == 3]
    for idx, buy in unmatched.iterrows():
        d = buy["tran_date"]
        a = buy["buy_amount"]
        mask = (
            (movements["move_date"] == d) &
            (abs(movements["move_amount"] - a) < 0.01) &
            ~movements.index.isin(matched_cm)
        )
        hits = movements[mask]
        if not hits.empty:
            cm_idx = hits.index[0]
            matched_cm.add(cm_idx)
            buys.at[idx, "payment_method"] = from_type_to_method(hits.at[cm_idx, "FromType"])
            buys.at[idx, "cm_match_pass"]  = 2

    return buys


def build_poswiz_daily(payments: pd.DataFrame, gst: pd.DataFrame) -> pd.DataFrame:
    day_gst = gst.groupby("trading_date")["gst_amount"].sum().reset_index()

    pivot = payments.pivot_table(
        index="trading_date",
        columns="pay_type",
        values="payment_amount",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    pivot.columns = [
        PAYTYPE_LABELS.get(c, f"paytype_{c}") if isinstance(c, int) else c
        for c in pivot.columns
    ]

    # Consolidated EFTPOS total (PayType 2+3; 4+5 if any appear)
    eftpos_cols = [PAYTYPE_LABELS[t] for t in EFTPOS_POOL if PAYTYPE_LABELS[t] in pivot.columns]
    pivot["eftpos_pool_total"] = pivot.reindex(columns=eftpos_cols, fill_value=0.0).sum(axis=1)

    txn_count  = payments.groupby("trading_date").size().reset_index(name="txn_count")
    sale_count = payments.groupby("trading_date")["sale_no"].nunique().reset_index(name="sale_count")

    summary = pivot.merge(day_gst,    on="trading_date", how="left")
    summary = summary.merge(txn_count,  on="trading_date", how="left")
    summary = summary.merge(sale_count, on="trading_date", how="left")
    return summary.sort_values("trading_date").reset_index(drop=True)


def build_cashnet_daily(buys: pd.DataFrame) -> pd.DataFrame:
    pivot = buys.pivot_table(
        index="tran_date",
        columns="payment_method",
        values="buy_amount",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    amount_cols  = [c for c in pivot.columns if c != "tran_date"]
    pivot["day_total"] = pivot[amount_cols].sum(axis=1)

    buy_count = buys.groupby("tran_date")["b_number"].count().reset_index(name="buy_count")
    pivot = pivot.merge(buy_count, on="tran_date", how="left")
    return pivot.sort_values("tran_date").reset_index(drop=True)


def main():
    print("Connecting to CWServer...")
    conn = get_connection()

    print("Pulling PosWiz payments (tblPayments + tblSale)...")
    payments = pull_poswiz_payments(conn)
    print(f"  {len(payments)} payment rows")

    print("Pulling PosWiz GST (tblReceiptInfo)...")
    gst = pull_poswiz_gst(conn)
    print(f"  {len(gst)} sale GST rows")

    print("Pulling CashNet buys (tblTran RefType=B)...")
    buys = pull_cashnet_buys(conn)
    print(f"  {len(buys)} buy transactions")

    print("Pulling CashNet cash movements (tblCashMove ToType=Buys/Loans)...")
    movements = pull_cashnet_movements(conn)
    print(f"  {len(movements)} movement rows")

    print("Classifying buy payment methods (3-pass match)...")
    buys = classify_buy_payment(buys, movements)
    p1 = (buys["cm_match_pass"] == 1).sum()
    p2 = (buys["cm_match_pass"] == 2).sum()
    p3 = (buys["cm_match_pass"] == 3).sum()
    print(f"  Pass 1 (B-number): {p1}  Pass 2 (fuzzy): {p2}  Pass 3 (default Cash): {p3}")

    print("Building daily summaries...")
    poswiz_daily  = build_poswiz_daily(payments, gst)
    cashnet_daily = build_cashnet_daily(buys)

    out_path = "Q2_FY26_Extract.xlsx"
    print(f"Writing {out_path}...")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        payments.to_excel(writer,      sheet_name="PosWiz_Payments", index=False)
        gst.to_excel(writer,           sheet_name="PosWiz_GST",      index=False)
        poswiz_daily.to_excel(writer,  sheet_name="PosWiz_Daily",    index=False)
        buys.to_excel(writer,          sheet_name="CashNet_Buys",    index=False)
        cashnet_daily.to_excel(writer, sheet_name="CashNet_Daily",   index=False)

    total_payments = payments["payment_amount"].sum()
    total_gst      = gst["gst_amount"].sum()
    total_buys     = buys["buy_amount"].sum()
    print(f"\nQ2 FY26 Totals:")
    print(f"  PosWiz payments : ${total_payments:,.2f}")
    print(f"  GST collected   : ${total_gst:,.2f}")
    print(f"  CashNet buys    : ${total_buys:,.2f}")
    print(f"\nOutput: {out_path}")
    conn.close()


if __name__ == "__main__":
    main()
