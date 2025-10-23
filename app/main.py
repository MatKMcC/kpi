from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

from api.toshl_api_call import fetch_entries
from db.run_queries import DataBase
from config import *

if __name__ == '__main__':

    # get most recent entries
    db = DataBase(START_DATE)
    most_recent_entry = db.get_most_recent_date()
    if most_recent_entry[0][0] is not None:
        START_DATE = dt.strftime(most_recent_entry[0][0] + relativedelta(days=-14), '%Y-%m-%d')

    # retrieve entries from toshl API
    entries = fetch_entries(
        api_url = TOSHL_API_URL
      , access_token = API_TOKEN
      , start_date = START_DATE
      , end_date = dt.strftime(dt.today(), format='%Y-%m-%d'))
    print(f"Entries received from API: {len(entries):,}")

    # update database entries
    # -- for every transaction add to the db
    db.update_expenses(entries)

    # add in existing metadata
    db.join_metadata()

    # launch UI to get transaction decision