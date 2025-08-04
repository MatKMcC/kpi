import mysql.connector
from mysql.connector import Error
from .queries import *
import re

class DataBase:
    """Database Connection Manager"""
    def __init__(self):
        self.connection = None
        try:
            # Establish the connection
            self.connection = mysql.connector.connect(
                host='localhost',        # Replace with your host
                database='kpi',          # Replace with your database name
                user='root',             # Replace with your MySQL username
                password='')             # Set your MySQL password
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"Connected to MySQL Server version {db_info}")
                cursor = self.connection.cursor()
                cursor.execute("select database();")
                record = cursor.fetchone()
                print(f"You're connected to database: {record[0]}")
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")

    def __del__(self):
        self.close()

    def close(self):
        if self.connection:
            self.connection.close()
            print("MySQL connection is closed")

    def mysql_string_conversion(self, string):
        vars = re.findall(r'\{([^}]*)\}', string)
        vars = {v: '%(' + v + ')s' for v in vars}
        return string.format(**vars)

    # insert new expenses
    def update_expenses(self, expenses):
        if not self.connection:
            print("Cursor is not available")
            return
        try:
            for expense in expenses:
                self.connection.cursor().execute(create_expenses_query)
                self.connection.commit()
                self.connection.cursor().execute(self.mysql_string_conversion(update_expenses_query), expense)
                self.connection.commit()  # Commit the changes
        except Error as e:
            print(f"Error updating expenses: {e}")
