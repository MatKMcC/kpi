import requests
from datetime import datetime as dt
from datetime import timezone as tz

def clean_entries(entry):
    return {
          'id': entry.get('id')
        , 'amount': entry.get('amount')
        , 'date': entry.get('date')
        , 'created': entry.get('created')
        , 'desc': entry.get('desc')
        , 'account': entry.get('account')
        , 'category': entry.get('category')
        , 'modified': entry.get('modified')
        , 'deleted': entry.get('deleted')}

def fetch_entries(api_url, access_token, start_date, end_date=None):

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'from': start_date
      , 'to': end_date
      , 'per_page': 25
      , 'page': 0
      , 'include_deleted': 'true'
    }

    response = requests.get(f'{api_url}/entries', headers=headers, params=params)
    if response.status_code == 200:
        entries = response.json()
        page_entries = entries
        while len(page_entries) != 0:
            params['page'] += 1
            page_entries = requests.get(f'{api_url}/entries', headers=headers, params=params).json()
            entries += page_entries
        entries = [clean_entries(el) for el in entries]
        return entries
    else:
        return None