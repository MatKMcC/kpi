from datetime import datetime as dt

from api.toshl_api_call import fetch_entries
from db.run_queries import DataBase
from config import *

if __name__ == '__main__':

    # get most recent entries
    # -- catch updated transactions somehow

    # retrieve entries from toshl API
    entries = fetch_entries(
        api_url = TOSHL_API_URL
      , access_token = API_TOKEN
      , start_date = START_DATE
      , end_date = dt.strftime(dt.today(), format='%Y-%m-%d'))

    # update database entries
    # -- for every transaction add to the db
    db = DataBase()
    db.update_expenses(entries)

    # launch UI to get transaction decision