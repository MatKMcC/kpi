import psycopg2
from psycopg2 import sql, Error
from .queries import *
import re

class DataBase:
    """Database Connection Manager"""
    def __init__(self):
        self.connection = None
        try:
            # Establish the connection
            self.connection = psycopg2.connect(
                host='localhost',        # Replace with your host
                database='kpi',          # Replace with your database name
                user='rubicon',             # Replace with your MySQL username
                password='')             # Set your MySQL password
        except Error as e:
            print(f"Error while connecting to PostgreSQL: {e}")

    def __del__(self):
        self.drop_table("expenses_tmp")
        self.close()

    def close(self):
        if self.connection:
            self.connection.close()
            print("PostgreSQL connection is closed")

    def sql_string_conversion(self, string):
        vars = re.findall(r'\{([^}]*)\}', string)
        vars = {v: '%(' + v + ')s' for v in vars}
        return string.format(**vars)

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()

    # insert new expenses
    def update_expenses(self, expenses):
        if not self.connection:
            print("Cursor is not available")
            return
        try:
            n_expenses = 0
            for expense in expenses:
                self.execute_query(create_expenses_query)
                self.execute_query(self.sql_string_conversion(update_expenses_query), expense)
                n_expenses += 1
            print(f"Updated {n_expenses} expenses")
        except Error as e:
            print(f"Error updating expenses: {e}")

    def drop_table(self, table):
        self.execute_query(drop_table_query.format(table))

    def get_most_recent_date(self):
        return self.execute_query(get_recent_date_query)
