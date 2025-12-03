import requests
import re
import json
from urllib.parse import quote

session = requests.Session()

# Get CSRF token
response = session.get('https://micro.domains/')
csrf_match = re.search(r"var csrftoken = '([^']+)'", response.text)
csrf = csrf_match.group(1)

print(f"CSRF Token: {csrf[:20]}...")

# Test individual TLDs with different filters
test_tlds = [
    'com', 'io', 'co', 'net', 'org',
    'ca', 'uk', 'de', 'fr', 'au',
    'sh', 'cc', 'ai', 'bz',
    'tv', 'be', 'me', 'ws',
    'tech', 'dev', 'app', 'rocks'
]

headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://micro.domains',
    'x-csrftoken': csrf,
    'x-requested-with': 'XMLHttpRequest',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}

results = {}

for tld in test_tlds:
    # URL encode the TLD array
    tlds_json = f'["{tld}"]'
    tlds_encoded = quote(tlds_json)
    
    data = {
        'draw': '10',
        'columns[0][data]': '0',
        'columns[1][data]': 'length',
        'columns[2][data]': 'price',
        'columns[3][data]': 'price_renewal',
        'order[0][column]': '2',
        'order[0][dir]': 'asc',
        'start': '0',
        'length': '100',
        'search[value]': '',
        'search[regex]': 'false',
        'price': '99999',
        'available': '1',
        'has_number': '0',
        'has_hyphen': '0',
        'price_renewal': '99999',
        'domain_length': '5',
        'sort': 'price',
        'tlds': tlds_json,
    }
    
    try:
        response = session.post('https://micro.domains/urls/', headers=headers, data=data, timeout=10)
        if response.status_code == 200:
            j = response.json()
            urls = j.get('urls', [])
            
            if urls:
                min_price = min(float(u.get('price', 999)) for u in urls)
                max_price = max(float(u.get('price', 999)) for u in urls)
                samples = [f"{u['domain']}.{u['tld']} (${float(u['price']):.2f})" for u in urls[:3]]
                
                results[tld] = {
                    'count': len(urls),
                    'min_price': min_price,
                    'max_price': max_price,
                    'samples': samples
                }
                print(f"✓ .{tld:8s}: {len(urls):3d} domains | ${min_price:7.2f} - ${max_price:7.2f}")
            else:
                print(f"✗ .{tld:8s}: no domains found")
        else:
            print(f"✗ .{tld:8s}: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ .{tld:8s}: {str(e)[:40]}")
    
    import time
    time.sleep(0.3)

# Save summary
with open('tld_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Saved detailed results to tld_comparison.json")

# Print sorted by min price
print("\n" + "="*85)
print("TLDs Sorted by Minimum Price:")
print("="*85)
print(f"{'TLD':8s} {'Count':8s} {'Min Price':12s} {'Max Price':12s} {'Cheapest Domains'}")
print("="*85)

for tld in sorted(results.keys(), key=lambda t: results[t]['min_price']):
    stats = results[tld]
    sample = stats['samples'][0] if stats['samples'] else 'N/A'
    print(f".{tld:7s} {stats['count']:8d} ${stats['min_price']:11.2f} ${stats['max_price']:11.2f} {sample}")

