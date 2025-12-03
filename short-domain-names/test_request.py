import requests
import re
import json

# Get the page and extract CSRF token and any cookies
session = requests.Session()
r = session.get('https://micro.domains/')

# Extract CSRF token
csrf_match = re.search(r"var csrftoken = '([^']+)'", r.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"CSRF Token: {csrf_token}")

    # Check cookies
    print(f"Cookies in session: {session.cookies.get_dict()}")

    # Try request with various header configurations
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-csrftoken': csrf_token,
        'x-requested-with': 'XMLHttpRequest',
        'origin': 'https://micro.domains',
        'referer': 'https://micro.domains/',
    }

    data = {
        'draw': '10',
        'start': '0',
        'length': '50',
        'search[value]': '',
        'search[regex]': 'false',
        'price': '20',
        'available': '1',
        'has_number': '1',
        'has_hyphen': '0',
        'price_renewal': '20',
        'domain_length': '5',
    }

    print("\nAttempting POST request...")
    response = session.post('https://micro.domains/urls/', headers=headers, data=data)

    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")

    if response.status_code != 200:
        print(f"Error: {response.text[:500]}")
    else:
        try:
            json_data = response.json()
            print(f"Got JSON! Data count: {len(json_data.get('data', []))}")
            if json_data.get('data'):
                print(f"First domain: {json_data['data'][0]}")
        except:
            print("Response is not valid JSON")
            print(response.text[:500])
