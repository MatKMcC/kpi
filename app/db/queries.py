drop_table_query = f"""
DROP TABLE {{}};
"""

create_expenses_query = """
CREATE TABLE IF NOT EXISTS expenses_tmp (
    id VARCHAR(256)
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

create_expenses_query = """
CREATE TABLE IF NOT EXISTS test.expenses_tmp (
    id VARCHAR(256)
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
INSERT INTO expenses_tmp (id, amount, date, created, modified, description, account, category, completed, deleted)
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
  , {{deleted}});
"""

get_recent_date_query = f"""
SELECT CAST(MAX(modified) AS DATE) recent_date
FROM test.expenses;
"""