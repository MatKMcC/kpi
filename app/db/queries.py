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