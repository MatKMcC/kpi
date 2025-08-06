drop_table_query = f"""
DROP TABLE {{}};
"""

create_expenses_query = f"""
CREATE TABLE IF NOT EXISTS {{}} (
    id VARCHAR(256) PRIMARY KEY
  , amount FLOAT
  , date DATE
  , created TIMESTAMP
  , modified TIMESTAMP
  , description VARCHAR(256)
  , account VARCHAR(256)
  , category VARCHAR(256)
  , completed BOOLEAN
  , deleted BOOLEAN
);
"""

update_expenses_query = f"""
INSERT INTO expenses (id, amount, date, created, modified, description, account, category, completed, deleted)
VALUES (
    {{id}}
  , {{amount}}
  , {{date}}
  , {{created}}
  , {{modified}}
  , {{desc}}
  , {{account}}
  , {{category}}
  , {{completed}}
  , {{deleted}})
ON CONFLICT (id) DO UPDATE SET
    amount = EXCLUDED.amount
  , date = EXCLUDED.date
  , created = EXCLUDED.created
  , modified = EXCLUDED.modified
  , description = EXCLUDED.description
  , account = EXCLUDED.account
  , category = EXCLUDED.category
  , completed = EXCLUDED.completed
  , deleted = EXCLUDED.deleted
;
"""

get_recent_date_query = f"""
SELECT CAST(MAX(modified) AS DATE) recent_date
FROM expenses;
"""