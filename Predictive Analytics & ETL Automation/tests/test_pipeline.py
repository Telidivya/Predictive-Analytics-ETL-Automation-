import pandas as pd
from src.etl_pipeline import transform_data, build_kpis

def sample():
    return pd.DataFrame([
        {"transaction_id":"A1","transaction_date":"2025-01-01","transaction_hour":10,
         "payment_method":"UPI","bank":"Bank A","region":"South","device_type":"Mobile",
         "amount":1000,"risk_score":20,"status":"Successful","failure_reason":"N/A"},
        {"transaction_id":"A2","transaction_date":"2025-01-02","transaction_hour":23,
         "payment_method":"Card","bank":"Bank B","region":"West","device_type":"Desktop",
         "amount":5000,"risk_score":70,"status":"Failed","failure_reason":"Network Timeout"},
    ])

def test_transform_creates_failure_flag_and_features():
    result = transform_data(sample())
    assert result["is_failed"].tolist() == [0, 1]
    assert "amount_band" in result.columns
    assert "is_weekend" in result.columns

def test_kpis_count_failures():
    result = transform_data(sample())
    daily, method, reason = build_kpis(result)
    assert daily["total_transactions"].sum() == 2
    assert daily["failed_transactions"].sum() == 1
    assert method.loc[method["payment_method"] == "Card", "failure_rate"].iloc[0] == 1.0
    assert reason["failed_transactions"].sum() == 1
