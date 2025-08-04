import requests
from datetime import datetime as dt
from datetime import timezone as tz


def clean_entries(entry):
    created = dt.fromisoformat(entry.get('created')[:-1]).astimezone(tz.utc)
    created = dt.strftime(created, '%Y-%m-%d %H:%M:%S')
    return {
          'id': entry.get('id')
        , 'amount': entry.get('amount')
        , 'date': entry.get('date')
        , 'desc': entry.get('desc')
        , 'account': entry.get('account')
        , 'category': entry.get('category')
        , 'created': created
        , 'modified': entry.get('modified')
        , 'completed': entry.get('completed')
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