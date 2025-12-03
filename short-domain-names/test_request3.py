import requests
import re
import json

session = requests.Session()
r = session.get('https://micro.domains/')

csrf_match = re.search(r"var csrftoken = '([^']+)'", r.text)
csrf_token = csrf_match.group(1)

# Test different parameter combinations
test_cases = [
    {
        'name': 'No filters (just price/renewal)',
        'params': {
            'price': '20',
            'price_renewal': '20',
            'domain_length': '5',
        }
    },
    {
        'name': 'With available=1',
        'params': {
            'price': '20',
            'price_renewal': '20',
            'domain_length': '5',
            'available': '1',
        }
    },
    {
        'name': 'With available=1, has_number=1',
        'params': {
            'price': '20',
            'price_renewal': '20',
            'domain_length': '5',
            'available': '1',
            'has_number': '1',
        }
    },
]

for test in test_cases:
    print(f"\nTesting: {test['name']}")

    data = {
        'draw': '10',
        'start': '0',
        'length': '50',
        'search[value]': '',
        'search[regex]': 'false',
        'order[0][column]': '2',
        'order[0][dir]': 'asc',
    }

    # Add test-specific params
    data.update(test['params'])

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-csrftoken': csrf_token,
        'x-requested-with': 'XMLHttpRequest',
        'origin': 'https://micro.domains',
        'referer': 'https://micro.domains/?',
    }

    response = session.post('https://micro.domains/urls/', headers=headers, data=data)

    if response.status_code == 200:
        json_data = response.json()
        data_count = len(json_data.get('data', []))
        records = json_data.get('recordsTotal', 0)
        print(f"  ✓ Status 200 | Data: {data_count} | Total: {records}")
        if data_count > 0:
            print(f"    First: {json_data['data'][0]}")
    else:
        print(f"  ✗ Status {response.status_code}")
