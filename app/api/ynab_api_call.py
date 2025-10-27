import requests

def clean_entries(entry):
    return {
          'id': entry.get('id')
        , 'amount': entry.get('amount') / 1000
        , 'date': entry.get('date')
        , 'memo': entry.get('memo')
        , 'cleared': entry.get('cleared')
        , 'approved': entry.get('approved')
        , 'account_id': entry.get('account_id')
        , 'account_name': entry.get('account_name')
        , 'payee_id': entry.get('payee_id')
        , 'payee_name': entry.get('payee_name')
        , 'category_id': entry.get('category_id')
        , 'category_name': entry.get('category_name')
        , 'deleted': entry.get('deleted')}

def fetch_entries(api_url, access_token, start_date, last_knowledge_of_server=None):

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'since_date': start_date
      , 'last_knowledge_of_server': last_knowledge_of_server
    }

    response = requests.get(f'{api_url}/budgets/last-used/transactions', headers=headers, params=params)
    print(response.status_code)
    if response.status_code == 200:
        entries = response.json()
        return entries['data']['transactions'], entries['data']['server_knowledge']
    else:
        return None