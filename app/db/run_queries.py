import psycopg2
from dateutil.relativedelta import relativedelta
from psycopg2 import sql, Error
from sqlalchemy import create_engine
from psycopg2.extras import RealDictCursor

from .queries import *
from .util import *
import re

class DataBase:
    """Database Connection Manager"""
    def __init__(self, start_date):
        self.connection = None
        try:
            # Establish the connection
            self.connection = psycopg2.connect(
                host='localhost',        # Replace with your host
                database='kpi',          # Replace with your database name
                user='rubicon',             # Replace with your MySQL username
                password='')             # Set your MySQL password
            self.connection_string = 'postgresql+psycopg2://rubicon@localhost:5432/kpi'
            self.engine = create_engine(self.connection_string)
            # setup data tables
            self.execute_query(create_entries_query)
            self.execute_query(create_metadata_query)
            self.execute_query(create_server_knowledge_query)
            self.create_dates_table(start_date)
            self.start_date = start_date

        except Error as e:
            print(f"Error while connecting to PostgreSQL: {e}")

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
        try:
            return cursor.fetchall()
        except:
            return []

    # insert new expenses
    def update_entries(self, entries):
        try:
            counts = 0
            for entry in entries:
                self.execute_query(self.sql_string_conversion(update_entries_query), entry)
                counts += 1
            print(f"Updated {counts} entries")
        except Error as e:
            print(f"Error updating entries: {e}")

    def get_last_knowledge_of_server(self):
        return self.execute_query(get_last_knowledge_of_server_query)

    def update_server_knowledge(self, server_knowledge):
        return self.execute_query(update_server_knowledge_query.format(
            timestamp=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
          , server_knowledge=server_knowledge))

    def create_dates_table(self, start_date):
        # Just in case script doesn't complete next time
        self.drop_table('report_dates')
        self.drop_table('report_dates_tmp')
        end_date = from_date(to_date(start_date) + relativedelta(years=1))
        self.execute_query(create_report_dates_tmp_query.format(start_date=start_date, end_date=end_date))
        self.execute_query(update_report_dates_01_day_query.format(start_date=start_date, end_date=end_date))
        self.execute_query(update_report_dates_07_day_query)
        self.execute_query(update_report_dates_28_day_query)
        self.execute_query(create_report_dates_query.format(start_date=start_date, end_date=end_date))

    def join_metadata(self):
        self.drop_table("expenses_metadata")
        return self.execute_query(join_medata_query)

    def drop_table(self, table):
        self.execute_query(drop_table_query.format(table))

    def __del__(self):
        self.drop_table('report_dates_tmp')
        self.close()
