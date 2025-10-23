drop_table_query = f"""
DROP TABLE IF EXISTS {{}};
"""

create_expenses_query = f"""
CREATE TABLE IF NOT EXISTS expenses (
    id VARCHAR(256) PRIMARY KEY
  , amount FLOAT
  , date DATE
  , created TIMESTAMP
  , modified TIMESTAMP
  , description VARCHAR(256)
  , account VARCHAR(256)
  , category VARCHAR(256)
  , deleted BOOLEAN
);
"""

create_metadata_query = f"""
CREATE TABLE IF NOT EXISTS metadata (
    id VARCHAR(256) PRIMARY KEY
  , status VARCHAR(256)
  , payback_period INT
);
"""

update_expenses_query = f"""
INSERT INTO expenses (id, amount, date, created, modified, description, account, category, deleted)
VALUES (
    {{id}}
  , {{amount}}
  , {{date}}
  , {{created}}
  , {{modified}}
  , {{desc}}
  , {{account}}
  , {{category}}
  , {{deleted}})
ON CONFLICT (id) DO UPDATE SET
    amount = EXCLUDED.amount
  , date = EXCLUDED.date
  , created = EXCLUDED.created
  , modified = EXCLUDED.modified
  , description = EXCLUDED.description
  , account = EXCLUDED.account
  , category = EXCLUDED.category
  , deleted = EXCLUDED.deleted
;
"""

join_medata_query = """
CREATE TABLE IF NOT EXISTS expenses_metadata AS 
SELECT
    e.id
  , e.amount
  , e.date
  , e.created 
  , e.description
  , e.account
  , e.category
  , m.status
  , m.payback_period
  , e.date + (INTERVAL '1 day' * m.payback_period) - (INTERVAL '1 day') final_payment_date
  , e.amount / m.payback_period payback_amount
FROM expenses e
INNER JOIN metadata m
  ON e.id = m.id
WHERE NOT e.deleted
;
"""

get_recent_date_query = f"""
SELECT CAST(MAX(modified) AS DATE) recent_date
FROM expenses;
"""

create_report_dates_query = """
CREATE TABLE report_dates AS
SELECT *
FROM report_dates_tmp
WHERE report_date BETWEEN '{start_date}' and '{end_date}';
"""

create_report_dates_tmp_query = """
CREATE TABLE report_dates_tmp (
    report_date DATE
  , period_name VARCHAR
  , join_date DATE);
"""

update_report_dates_01_day_query = """
INSERT INTO report_dates_tmp (report_date, period_name, join_date)
SELECT 
    datum::date AS report_date
  , '01 Day' AS period_name
  , datum::date AS join_date
FROM GENERATE_SERIES(
    '{start_date}'::date
  , '{end_date}'::date
  , '1 day'::interval) AS datum;
"""

update_report_dates_07_day_query = """
INSERT INTO report_dates_tmp (report_date, period_name, join_date)
SELECT 
    l.report_date AS report_date
  , '07 Days Trailing' AS period_name
  , r.report_date AS join_date
FROM report_dates_tmp l
LEFT JOIN report_dates_tmp r
  ON l.report_date BETWEEN r.report_date AND r.report_date + INTERVAL '6 day';
"""

update_report_dates_28_day_query = """
INSERT INTO report_dates_tmp (report_date, period_name, join_date)
SELECT 
    l.report_date AS report_date
  , '27 Days Trailing' AS period_name
  , r.report_date AS join_date
FROM report_dates_tmp l
LEFT JOIN report_dates_tmp r
  ON l.report_date BETWEEN r.report_date AND r.report_date + INTERVAL '27 day';
"""