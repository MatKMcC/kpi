from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

from api.ynab_api_call import fetch_entries
from db.run_queries import DataBase
from config import *

if __name__ == '__main__':

    # get most recent entries
    db = DataBase(START_DATE)
    last_knowledge_of_server = db.get_last_knowledge_of_server()

    # retrieve entries from toshl API
    entries, server_knowledge = fetch_entries(
        api_url = API_URL
      , access_token = API_TOKEN
      , start_date = START_DATE
      , last_knowledge_of_server = last_knowledge_of_server)
    print(f"Entries received from API: {len(entries):,}")

    # update the last knowledge of the server
    db.update_server_knowledge(server_knowledge)

    # update database entries
    db.update_entries(entries)

    # add in existing metadata
    db.join_metadata()

    # launch UI to get transaction decision