import requests
import re
import json

session = requests.Session()
r = session.get('https://micro.domains/')
csrf_match = re.search(r"var csrftoken = '([^']+)'", r.text)
csrf = csrf_match.group(1)

headers = {
    'accept': 'application/json',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://micro.domains',
    'x-csrftoken': csrf,
    'x-requested-with': 'XMLHttpRequest',
}

# Test without filters
params = [
    ('No filters', {}),
    ('has_number=1', {'has_number': '1'}),
    ('has_number=0', {'has_number': '0'}),
    ('has_number=0, no available', {'has_number': '0', 'available': ''}),
]

for name, extra_data in params:
    data = {
        'draw': '10',
        'columns[0][data]': '0',
        'columns[1][data]': 'length',
        'columns[2][data]': 'price',
        'columns[3][data]': 'price_renewal',
        'order[0][column]': '2',
        'order[0][dir]': 'asc',
        'start': '0',
        'length': '25',
        'search[value]': '',
        'search[regex]': 'false',
        'price': '20',
        'available': '1',
        'has_number': '',
        'has_hyphen': '0',
        'price_renewal': '20',
        'tlds': 'null',
        'domain_length': '5',
        'sort': 'price',
    }
    
    data.update(extra_data)
    
    response = session.post('https://micro.domains/urls/', headers=headers, data=data)
    
    print(f"\n{name}:")
    if response.status_code == 200:
        j = response.json()
        urls = j.get('urls', [])
        print(f"  ✓ Status 200 | Got {len(urls)} results")
        if urls:
            for item in urls[:3]:
                print(f"    - {item['domain']}.{item['tld']} ${item['price']:.2f}")
    else:
        print(f"  ✗ Status {response.status_code}")
