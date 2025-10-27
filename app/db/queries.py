drop_table_query = f"""
DROP TABLE IF EXISTS {{}};
"""

create_entries_query = f"""
CREATE TABLE IF NOT EXISTS entries (
    id VARCHAR(256) PRIMARY KEY
  , amount FLOAT
  , date DATE
  , memo VARCHAR(256)
  , cleared VARCHAR(256)
  , approved BOOLEAN
  , account_id VARCHAR(256)
  , account_name VARCHAR(256)
  , payee_id VARCHAR(256)
  , payee_name VARCHAR(256)
  , category_id VARCHAR(256)
  , category_name VARCHAR(256)
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

update_entries_query = f"""
INSERT INTO entries (
    id
  , amount
  , date
  , memo
  , cleared
  , approved
  , account_id
  , account_name
  , payee_id
  , payee_name
  , category_id
  , category_name
  , deleted)
VALUES (
    {{id}}
  , {{amount}}
  , {{date}}
  , {{memo}}
  , {{cleared}}
  , {{approved}}
  , {{account_id}}
  , {{account_name}}
  , {{payee_id}}
  , {{payee_name}}
  , {{category_id}}
  , {{category_name}}
  , {{deleted}})
ON CONFLICT (id) DO UPDATE SET
    amount = EXCLUDED.amount
  , date = EXCLUDED.date
  , memo = EXCLUDED.memo
  , cleared = EXCLUDED.cleared
  , approved = EXCLUDED.approved
  , account_id = EXCLUDED.account_id
  , account_name = EXCLUDED.account_name
  , payee_id = EXCLUDED.payee_id
  , payee_name = EXCLUDED.payee_name
  , category_id = EXCLUDED.category_id
  , category_name = EXCLUDED.category_name
  , deleted = EXCLUDED.deleted
;
"""

join_medata_query = """
CREATE TABLE IF NOT EXISTS entries_metadata AS 
SELECT
    e.id
  , e.amount
  , e.date
  , e.memo
  , e.cleared
  , e.approved
  , e.account_id
  , e.account_name
  , e.payee_id
  , e.payee_name
  , e.category_id
  , e.category_name
  , m.status
  , m.payback_period
  , e.date + (INTERVAL '1 day' * m.payback_period) - (INTERVAL '1 day') final_payment_date
  , e.amount / m.payback_period payback_amount
FROM entries e
INNER JOIN metadata m
  ON e.id = m.id
WHERE NOT e.deleted
;
"""

create_report_dates_query = """
CREATE TABLE report_dates AS (
SELECT *
FROM report_dates_tmp
WHERE report_date BETWEEN '{start_date}' and '{end_date}');
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

create_server_knowledge_query = f"""
CREATE TABLE IF NOT EXISTS server_knowledge (
    timestamp TIMESTAMP PRIMARY KEY
  , server_knowledge INT
);
"""

get_last_knowledge_of_server_query = """
SELECT server_knowledge
FROM server_knowledge
ORDER BY timestamp DESC
LIMIT 1;
"""

update_server_knowledge_query = f"""
INSERT INTO server_knowledge (
    timestamp
  , server_knowledge)
VALUES (
    '{{timestamp}}'
  , {{server_knowledge}})
;
"""