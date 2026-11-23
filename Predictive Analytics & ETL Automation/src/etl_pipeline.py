"""ETL pipeline for the Payment Failure Intelligence System."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

REQUIRED_COLUMNS = {
    "transaction_id", "transaction_date", "transaction_hour", "payment_method",
    "bank", "region", "device_type", "amount", "risk_score", "status", "failure_reason"
}

def load_data(path: Path = DATA / "transactions.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["transaction_date"] = pd.to_datetime(out["transaction_date"], errors="coerce")
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    out["transaction_hour"] = pd.to_numeric(out["transaction_hour"], errors="coerce")
    out["risk_score"] = pd.to_numeric(out["risk_score"], errors="coerce")
    out = out.dropna(subset=["transaction_id", "transaction_date", "amount", "transaction_hour"])
    out = out.drop_duplicates(subset=["transaction_id"])
    for col in ["payment_method", "bank", "region", "device_type", "status", "failure_reason"]:
        out[col] = out[col].fillna("Unknown").astype(str).str.strip()
    out["is_failed"] = out["status"].isin(["Failed", "Declined", "Timeout"]).astype(int)
    out["is_successful"] = (out["status"] == "Successful").astype(int)
    out["day_of_week"] = out["transaction_date"].dt.day_name()
    out["is_weekend"] = (out["transaction_date"].dt.dayofweek >= 5).astype(int)
    out["amount_band"] = pd.cut(
        out["amount"], bins=[-float("inf"), 500, 2000, 10000, 30000, float("inf")],
        labels=["0-500", "501-2000", "2001-10000", "10001-30000", "30000+"]
    ).astype(str)
    out["time_band"] = pd.cut(
        out["transaction_hour"], bins=[-1, 5, 11, 17, 23],
        labels=["Night", "Morning", "Afternoon", "Evening"]
    ).astype(str)
    return out.sort_values("transaction_date").reset_index(drop=True)

def build_kpis(df: pd.DataFrame):
    work = df.copy()
    work["transaction_day"] = work["transaction_date"].dt.date
    daily = work.groupby("transaction_day", as_index=False).agg(
        total_transactions=("transaction_id", "count"),
        failed_transactions=("is_failed", "sum"),
        total_amount=("amount", "sum"),
        failed_amount=("amount", lambda s: s[work.loc[s.index, "is_failed"].eq(1)].sum())
    )
    daily["failure_rate"] = daily["failed_transactions"] / daily["total_transactions"]
    method = work.groupby("payment_method", as_index=False).agg(
        total_transactions=("transaction_id", "count"),
        failed_transactions=("is_failed", "sum"),
        failed_amount=("amount", lambda s: s[work.loc[s.index, "is_failed"].eq(1)].sum())
    )
    method["failure_rate"] = method["failed_transactions"] / method["total_transactions"]
    reason = (work[work["is_failed"] == 1].groupby("failure_reason", as_index=False)
              .agg(failed_transactions=("transaction_id", "count"),
                   failed_amount=("amount", "sum"))
              .sort_values("failed_transactions", ascending=False))
    return daily, method, reason

def main():
    raw = load_data()
    clean = transform_data(raw)
    clean.to_csv(DATA / "cleaned_transactions.csv", index=False)
    daily, method, reason = build_kpis(clean)
    daily.to_csv(DATA / "daily_kpis.csv", index=False)
    method.to_csv(DATA / "payment_method_kpis.csv", index=False)
    reason.to_csv(DATA / "failure_reason_kpis.csv", index=False)
    print(f"ETL complete: {len(raw):,} input rows → {len(clean):,} clean rows")
    print(f"Overall failure rate: {clean['is_failed'].mean():.2%}")

if __name__ == "__main__":
    main()
