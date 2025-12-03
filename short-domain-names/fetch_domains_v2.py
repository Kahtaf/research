#!/usr/bin/env python3
"""
Domain scraper using a proper session with cookies and CSRF handling
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import re

def get_session():
    """Create a session with proper retry logic and cookies."""
    session = requests.Session()

    # Add retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Visit homepage to establish session and get CSRF token
    print("Establishing session and getting CSRF token...")
    response = session.get('https://micro.domains/')

    # Extract CSRF token from the page
    match = re.search(r"var csrftoken = '([^']+)'", response.text)
    if match:
        csrf_token = match.group(1)
        print(f"Got CSRF token: {csrf_token[:20]}...")

        # Add CSRF token to session headers
        session.headers.update({
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
        })

        return session, csrf_token
    else:
        raise ValueError("Could not find CSRF token in response")


def fetch_domains(session, start, length):
    """Fetch a batch of domains."""
    url = 'https://micro.domains/urls/'

    data = {
        'draw': '10',
        'start': str(start),
        'length': str(length),
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

    # Add column info
    for i in range(4):
        data[f'columns[{i}][data]'] = ''
        data[f'columns[{i}][name]'] = ''
        data[f'columns[{i}][searchable]'] = 'true'
        data[f'columns[{i}][orderable]'] = 'false'
        data[f'columns[{i}][search][value]'] = ''
        data[f'columns[{i}][search][regex]'] = 'false'

    data['columns[1][data]'] = 'length'
    data['columns[2][data]'] = 'price'
    data['columns[2][orderable]'] = 'true'
    data['columns[3][data]'] = 'price_renewal'
    data['columns[3][orderable]'] = 'true'

    data['order[0][column]'] = '2'
    data['order[0][dir]'] = 'asc'

    try:
        response = session.post(url, data=data, timeout=10)
        response.raise_for_status()

        # Check if we got JSON back
        if 'application/json' in response.headers.get('content-type', ''):
            return response.json()
        else:
            print(f"Warning: Got non-JSON response. Status: {response.status_code}")
            if len(response.text) < 500:
                print(f"Response: {response.text[:500]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def main():
    print("=== Domain Scraper v2 ===\n")

    try:
        session, csrf = get_session()
    except Exception as e:
        print(f"Failed to establish session: {e}")
        return

    all_domains = []
    max_requests = 30
    length = 100
    start = 0
    request_count = 0

    for request_count in range(max_requests):
        print(f"\nRequest {request_count + 1}/{max_requests}: start={start}, length={length}")

        result = fetch_domains(session, start, length)

        if not result:
            print("Failed to get results, stopping")
            break

        data = result.get('data', [])
        records_total = result.get('recordsTotal', 0)

        if not data:
            print(f"No more domains found. Total available: {records_total}")
            break

        print(f"Got {len(data)} results")

        for domain_info in data:
            # The structure appears to be an array: [domain_name, length, price, renewal_price]
            if isinstance(domain_info, list) and len(domain_info) >= 4:
                domain = domain_info[0]
                price = float(domain_info[2])
                renewal = float(domain_info[3])
            else:
                # Or it might be a dict
                domain = domain_info.get('0', '')
                price = float(domain_info.get('price', 999))
                renewal = float(domain_info.get('price_renewal', 999))

            if domain:
                all_domains.append({
                    'domain': domain,
                    'price': price,
                    'renewal': renewal,
                    'raw': domain_info,
                })

        start += length
        time.sleep(0.5)

        # Check if we've gotten all results
        if len(data) < length:
            print("Got fewer results than requested, stopping")
            break

    print(f"\n\nTotal domains found: {len(all_domains)}")

    # Save raw data
    with open('domains_raw.json', 'w') as f:
        json.dump(all_domains, f, indent=2)

    print("Results saved to domains_raw.json")


if __name__ == '__main__':
    main()
