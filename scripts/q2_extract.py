"""
q2_extract.py -- CWServer Q2 FY26 data extraction for SSG reconciliation.

Covers PosWiz sales payments and CashNet second-hand buys for Oct-Dec 2025.
Output: Q2_FY26_Extract.xlsx (10 sheets)

Sheets:
  PosWiz_Payments   -- one row per payment transaction (raw, transaction-level)
  PosWiz_GST        -- GST per sale from tblReceiptInfo
  PosWiz_Daily      -- daily summary by PayType + GST (ready for Xero invoice building)
  PosWiz_SaleItems  -- one row per sale line item with Xero account code (200/201/808)
  PosWiz_AccountDaily -- daily totals by account code (200/201/808)
  EFTPOS_Recon      -- PosWiz daily EFTPOS totals vs First Data ANZ deposits (T+1 to T+6)
  CashNet_Buys      -- one row per B-number with classified payment method
  CashNet_Daily     -- daily buy summary: cash / bank transfer / total
"""
import re
import sys
from datetime import date, timedelta
import pandas as pd
from db import get_connection, query_df

Q2_START = "2025-10-01"
Q2_END   = "2026-01-01"  # exclusive

ANZ_CSV          = r"C:\Users\User\Projects\ssg-reconciliation\FY26_Q2\ANZ_2025.09.28_2026.01.05.csv"
PAYPAL_SALES_CSV = r"C:\Users\User\Projects\ssg-reconciliation\FY26_Q2\paypal_sales_v2.csv"
FD_SETTLEMENT_MATCH = "FIRST DATA MERCH"
FD_SETTLEMENT_TYPE  = "SETTLEMENT"
# FD settles on next business day. Fri/Sat/Sun all arrive Monday.
# +1 calendar day tolerance covers public holidays pushing settlement one extra day.
FD_HOLIDAY_BUFFER   = 1

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


def pull_poswiz_sale_items(conn):
    sql = """
        SELECT
            CAST(s.Time_Stamp AS DATE) AS trading_date,
            si.SaleNo                  AS sale_no,
            si.RefNo,
            si.StockID,
            si.Origin,
            si.Qty,
            si.Amount                  AS item_amount
        FROM tblSaleItem si
        JOIN tblSale s ON si.SaleNo = s.SaleNo
        WHERE si.Deleted = 0
          AND s.Time_Stamp >= ? AND s.Time_Stamp < ?
        ORDER BY trading_date, si.SaleNo
    """
    df = query_df(conn, sql, [Q2_START, Q2_END])
    df["account_code"] = df.apply(_classify_account_code, axis=1)
    return df


def _classify_account_code(row) -> int:
    if row["Origin"] == "GFS" or row["StockID"] == 24554:
        return 808
    if isinstance(row["RefNo"], str) and row["RefNo"].upper().startswith("L"):
        return 201
    return 200


def build_account_daily(items: pd.DataFrame) -> pd.DataFrame:
    pivot = items.pivot_table(
        index="trading_date",
        columns="account_code",
        values="item_amount",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    pivot.columns = [
        f"acct_{c}" if isinstance(c, int) else c
        for c in pivot.columns
    ]

    for col in ("acct_200", "acct_201", "acct_808"):
        if col not in pivot.columns:
            pivot[col] = 0.0

    pivot["day_total"] = pivot["acct_200"] + pivot["acct_201"] + pivot["acct_808"]
    return pivot.sort_values("trading_date").reset_index(drop=True)


def pull_anz_fd_settlements(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        header=None,
        names=["txn_date", "amount", "description", "c3", "c4", "c5", "c6", "c7"],
        dtype=str,
    )
    df["txn_date"] = pd.to_datetime(df["txn_date"], dayfirst=True).dt.date
    df["amount"]   = pd.to_numeric(df["amount"].str.replace(",", ""), errors="coerce")

    mask = (
        df["description"].str.contains(FD_SETTLEMENT_MATCH, na=False) &
        df["description"].str.contains(FD_SETTLEMENT_TYPE,  na=False) &
        (df["amount"] > 0)
    )
    fd = df.loc[mask, ["txn_date", "amount", "description"]].copy()
    fd = fd.sort_values("txn_date").reset_index(drop=True)
    return fd


def _next_business_day(d: date) -> date:
    """Return the next Mon-Fri after d. Fri/Sat/Sun all advance to following Monday."""
    days_ahead = {4: 3, 5: 2, 6: 1}.get(d.weekday(), 1)
    return d + timedelta(days=days_ahead)


def match_eftpos_settlements(poswiz_daily: pd.DataFrame, fd: pd.DataFrame) -> pd.DataFrame:
    """
    Match FD deposits to PosWiz trading days using next-business-day rule.
    Fri/Sat/Sun trading days all expect a Monday FD deposit.
    FD_HOLIDAY_BUFFER adds tolerance for public holidays pushing settlement one extra day.

    match_status values:
      MATCHED      -- exact amount match on expected settlement date
      SPLIT        -- amount differs but within 50% (partial batch / card-type split)
      UNMATCHED_FD -- FD deposit found no matching PosWiz day
      UNMATCHED_PW -- PosWiz day with EFTPOS total has no FD deposit matched
    """
    pw = poswiz_daily[["trading_date", "eftpos_pool_total"]].copy()
    pw["trading_date"]     = pd.to_datetime(pw["trading_date"]).dt.date
    pw["expected_fd_date"] = pw["trading_date"].apply(_next_business_day)
    pw = pw[pw["eftpos_pool_total"] > 0].copy()
    pw["matched"] = False

    rows = []
    for _, dep in fd.iterrows():
        dep_date   = dep["txn_date"]
        dep_amount = dep["amount"]

        candidates = pw[
            (pw["expected_fd_date"] >= dep_date - timedelta(days=FD_HOLIDAY_BUFFER)) &
            (pw["expected_fd_date"] <= dep_date + timedelta(days=FD_HOLIDAY_BUFFER)) &
            (~pw["matched"])
        ]

        if candidates.empty:
            rows.append({
                "fd_date":         dep_date,
                "fd_amount":       dep_amount,
                "pw_trading_date": None,
                "pw_expected_fd":  None,
                "pw_eftpos_total": None,
                "variance":        None,
                "match_status":    "UNMATCHED_FD",
            })
            continue

        diff     = (candidates["eftpos_pool_total"] - dep_amount).abs()
        best_idx = diff.idxmin()
        best     = candidates.loc[best_idx]
        variance = round(dep_amount - best["eftpos_pool_total"], 2)

        if variance == 0.0:
            status = "MATCHED"
        elif abs(variance) < dep_amount * 0.5:
            status = "SPLIT"
        else:
            status = "UNMATCHED_FD"

        if status != "UNMATCHED_FD":
            pw.at[best_idx, "matched"] = True

        rows.append({
            "fd_date":         dep_date,
            "fd_amount":       dep_amount,
            "pw_trading_date": best["trading_date"],
            "pw_expected_fd":  best["expected_fd_date"],
            "pw_eftpos_total": best["eftpos_pool_total"],
            "variance":        variance,
            "match_status":    status,
        })

    for _, pw_row in pw[~pw["matched"]].iterrows():
        rows.append({
            "fd_date":         None,
            "fd_amount":       None,
            "pw_trading_date": pw_row["trading_date"],
            "pw_expected_fd":  pw_row["expected_fd_date"],
            "pw_eftpos_total": pw_row["eftpos_pool_total"],
            "variance":        None,
            "match_status":    "UNMATCHED_PW",
        })

    result = pd.DataFrame(rows)
    result = result.sort_values(
        ["pw_trading_date", "fd_date"],
        na_position="last",
    ).reset_index(drop=True)
    return result


def load_online_gateway_map(csv_path: str) -> dict:
    """Load paypal_sales_v2.csv and return sale_ref -> (gateway, match_type) dict."""
    df = pd.read_csv(csv_path)
    return {
        row["sale_ref"]: (row["actual_gateway"], row["match_type"])
        for _, row in df.iterrows()
    }


def build_online_orders(payments: pd.DataFrame, gateway_map: dict) -> pd.DataFrame:
    """Extract PayType 8 rows from payments and attach resolved gateway."""
    online = payments[payments["pay_type"] == 8].copy()
    online["gateway"] = online["sale_no"].map(
        lambda s: gateway_map.get(s, ("Unknown", "none"))[0]
    )
    online["gateway_match_type"] = online["sale_no"].map(
        lambda s: gateway_map.get(s, ("Unknown", "none"))[1]
    )
    return online.reset_index(drop=True)


def build_online_daily(online: pd.DataFrame) -> pd.DataFrame:
    """Daily totals by gateway (PayPal / Afterpay / Zip / Shopify Payments)."""
    pivot = online.pivot_table(
        index="trading_date",
        columns="gateway",
        values="payment_amount",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    amount_cols = [c for c in pivot.columns if c != "trading_date"]
    pivot["online_total"] = pivot[amount_cols].sum(axis=1)

    txn_count = online.groupby("trading_date").size().reset_index(name="txn_count")
    pivot = pivot.merge(txn_count, on="trading_date", how="left")
    return pivot.sort_values("trading_date").reset_index(drop=True)


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

    print("Pulling PosWiz sale items (tblSaleItem + account classification)...")
    sale_items = pull_poswiz_sale_items(conn)
    print(f"  {len(sale_items)} item rows")
    acct_counts = sale_items["account_code"].value_counts().sort_index()
    for code, cnt in acct_counts.items():
        total = sale_items.loc[sale_items["account_code"] == code, "item_amount"].sum()
        print(f"    Acct {code}: {cnt} rows  ${total:,.2f}")

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
    account_daily = build_account_daily(sale_items)
    cashnet_daily = build_cashnet_daily(buys)

    print("Loading online gateway map (paypal_sales_v2.csv)...")
    gateway_map  = load_online_gateway_map(PAYPAL_SALES_CSV)
    online_orders = build_online_orders(payments, gateway_map)
    online_daily  = build_online_daily(online_orders)
    gw_counts = online_orders["gateway"].value_counts()
    gw_totals = online_orders.groupby("gateway")["payment_amount"].sum()
    for gw in gw_counts.index:
        print(f"  {gw:<20}  {gw_counts[gw]:>4} txns  ${gw_totals[gw]:>10,.2f}")
    unknown = (online_orders["gateway"] == "Unknown").sum()
    if unknown:
        print(f"  WARNING: {unknown} PayType 8 rows not found in paypal_sales_v2.csv")

    print(f"Loading ANZ First Data settlements from CSV...")
    fd_settlements = pull_anz_fd_settlements(ANZ_CSV)
    print(f"  {len(fd_settlements)} FD settlement deposits  ${fd_settlements['amount'].sum():,.2f}")
    eftpos_recon = match_eftpos_settlements(poswiz_daily, fd_settlements)
    matched   = (eftpos_recon["match_status"] == "MATCHED").sum()
    splits    = (eftpos_recon["match_status"] == "SPLIT").sum()
    unmatched = eftpos_recon["match_status"].str.startswith("UNMATCHED").sum()
    print(f"  Matched: {matched}  Splits: {splits}  Unmatched: {unmatched}")

    out_path = "Q2_FY26_Extract.xlsx"
    print(f"Writing {out_path}...")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        payments.to_excel(writer,       sheet_name="PosWiz_Payments",     index=False)
        gst.to_excel(writer,            sheet_name="PosWiz_GST",          index=False)
        poswiz_daily.to_excel(writer,   sheet_name="PosWiz_Daily",        index=False)
        sale_items.to_excel(writer,     sheet_name="PosWiz_SaleItems",    index=False)
        account_daily.to_excel(writer,  sheet_name="PosWiz_AccountDaily", index=False)
        online_orders.to_excel(writer,  sheet_name="Online_Orders",       index=False)
        online_daily.to_excel(writer,   sheet_name="Online_Daily",        index=False)
        eftpos_recon.to_excel(writer,   sheet_name="EFTPOS_Recon",        index=False)
        buys.to_excel(writer,           sheet_name="CashNet_Buys",        index=False)
        cashnet_daily.to_excel(writer,  sheet_name="CashNet_Daily",       index=False)

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
