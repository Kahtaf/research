import requests
import re
import json

session = requests.Session()
r = session.get('https://micro.domains/')

csrf_match = re.search(r"var csrftoken = '([^']+)'", r.text)
csrf_token = csrf_match.group(1)

def make_request(modifications=None):
    data = {
        'draw': '10',
        'columns[0][data]': '0',
        'columns[0][name]': '',
        'columns[0][searchable]': 'true',
        'columns[0][orderable]': 'false',
        'columns[0][search][value]': '',
        'columns[0][search][regex]': 'false',
        'columns[1][data]': 'length',
        'columns[1][name]': '',
        'columns[1][searchable]': 'true',
        'columns[1][orderable]': 'false',
        'columns[1][search][value]': '',
        'columns[1][search][regex]': 'false',
        'columns[2][data]': 'price',
        'columns[2][name]': '',
        'columns[2][searchable]': 'true',
        'columns[2][orderable]': 'true',
        'columns[2][search][value]': '',
        'columns[2][search][regex]': 'false',
        'columns[3][data]': 'price_renewal',
        'columns[3][name]': '',
        'columns[3][searchable]': 'true',
        'columns[3][orderable]': 'true',
        'columns[3][search][value]': '',
        'columns[3][search][regex]': 'false',
        'order[0][column]': '2',
        'order[0][dir]': 'asc',
        'start': '0',
        'length': '50',
        'search[value]': '',
        'search[regex]': 'false',
        'price': '20',
        'available': '1',
        'has_number': '1',
        'has_hyphen': '0',
        'price_renewal': '20',
        'tlds': 'null',
        'domain_length': '5',
        'sort': 'price',
    }

    if modifications:
        data.update(modifications)

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'dnt': '1',
        'origin': 'https://micro.domains',
        'priority': 'u=1, i',
        'referer': 'https://micro.domains/?',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'x-csrftoken': csrf_token,
        'x-requested-with': 'XMLHttpRequest',
    }

    response = session.post('https://micro.domains/urls/', headers=headers, data=data)
    return response

# Test 1: Original (gets 0 results)
print("Test 1: Original parameters (no changes)")
r = make_request()
j = r.json()
print(f"  Data: {len(j.get('data', []))} | Total: {j.get('recordsTotal')}")

# Test 2: Remove filters one by one
print("\nTest 2: Without has_number")
r = make_request({'has_number': ''})
j = r.json()
print(f"  Data: {len(j.get('data', []))} | Total: {j.get('recordsTotal')}")

# Test 3: Without available filter
print("\nTest 3: Without available")
r = make_request({'available': ''})
j = r.json()
print(f"  Data: {len(j.get('data', []))} | Total: {j.get('recordsTotal')}")

# Test 4: Just basic parameters
print("\nTest 4: Minimal filters (just domain_length=5, price=20)")
r = make_request({
    'has_number': '',
    'available': '',
    'has_hyphen': '',
    'price_renewal': '',
    'tlds': '',
})
j = r.json()
print(f"  Data: {len(j.get('data', []))} | Total: {j.get('recordsTotal')}")
if j.get('data'):
    print(f"  First 3:")
    for item in j['data'][:3]:
        print(f"    {item}")
