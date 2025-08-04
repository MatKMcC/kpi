create_schema_query = """
CREATE schema IF NOT EXISTS test
"""

create_expenses_query = """
CREATE TABLE IF NOT EXISTS test.expenses (
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
)
"""

update_expenses_query = f"""
INSERT INTO test.expenses (id, amount, date, created, modified, description, account, category, completed, deleted)
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
"""