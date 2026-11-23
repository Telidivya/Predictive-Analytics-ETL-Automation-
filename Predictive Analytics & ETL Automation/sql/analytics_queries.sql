-- Payment Failure Intelligence System: SQL KPI queries
-- Assumes a table named transactions with the columns in data/transactions.csv.

-- 1. Overall payment health
SELECT
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN status IN ('Failed', 'Declined', 'Timeout') THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(100.0 * SUM(CASE WHEN status IN ('Failed', 'Declined', 'Timeout') THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    SUM(CASE WHEN status IN ('Failed', 'Declined', 'Timeout') THEN amount ELSE 0 END) AS failed_amount
FROM transactions;

-- 2. Failure rate by payment method
SELECT payment_method, COUNT(*) AS total_transactions,
       SUM(CASE WHEN status <> 'Successful' THEN 1 ELSE 0 END) AS failed_transactions,
       ROUND(100.0 * SUM(CASE WHEN status <> 'Successful' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM transactions
GROUP BY payment_method
ORDER BY failure_rate_pct DESC;

-- 3. Daily failure trend
SELECT transaction_date, COUNT(*) AS total_transactions,
       SUM(CASE WHEN status <> 'Successful' THEN 1 ELSE 0 END) AS failed_transactions
FROM transactions
GROUP BY transaction_date
ORDER BY transaction_date;

-- 4. Failure reasons and estimated failed value
SELECT failure_reason, COUNT(*) AS failures, SUM(amount) AS failed_value
FROM transactions
WHERE status <> 'Successful'
GROUP BY failure_reason
ORDER BY failures DESC;

-- 5. Operational risk: bank and region
SELECT bank, region, COUNT(*) AS total_transactions,
       SUM(CASE WHEN status <> 'Successful' THEN 1 ELSE 0 END) AS failures,
       ROUND(100.0 * SUM(CASE WHEN status <> 'Successful' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM transactions
GROUP BY bank, region
HAVING COUNT(*) >= 20
ORDER BY failure_rate_pct DESC;
