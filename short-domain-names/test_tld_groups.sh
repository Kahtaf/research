#!/bin/bash

CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")

# Test specific TLD combinations using curl
test_tlds() {
    local tld_list="$1"
    local label="$2"
    
    echo "Testing: $label"
    
    # Build JSON array and URL encode it
    local json_array=$(python3 << EOFPYTHON
import json
import urllib.parse
tlds = $tld_list
json_str = json.dumps(tlds)
encoded = urllib.parse.quote(json_str)
print(encoded)
EOFPYTHON
)
    
    curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'origin: https://micro.domains' \
      -H "x-csrftoken: $CSRF" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF" \
      --data-raw "draw=10&start=0&length=150&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$json_array&domain_length=5&sort=price" | python3 << 'EOFANALYZE'
import sys, json
try:
    j = json.loads(sys.stdin.read())
    urls = j.get('urls', [])
    if urls:
        by_tld = {}
        for u in urls:
            tld = u['tld']
            if tld not in by_tld:
                by_tld[tld] = []
            by_tld[tld].append(u)
        
        for tld in sorted(by_tld.keys()):
            items = by_tld[tld]
            prices = [float(u['price']) for u in items]
            min_p, max_p = min(prices), max(prices)
            sample = f"{items[0]['domain']}.{tld}"
            print(f"  .{tld}: {len(items):3d} | ${min_p:7.2f}-${max_p:7.2f} | {sample}")
    else:
        print("  No domains found")
except Exception as e:
    print(f"  Error: {e}")
EOFANALYZE
    
    sleep 0.3
}

# Test in smaller groups
test_tlds '["com", "net", "org"]' "Major TLDs"
test_tlds '["io", "co", "ai"]' "Trendy TLDs"
test_tlds '["ca", "uk", "de", "fr"]' "Country TLDs"
test_tlds '["app", "dev", "tech"]' "Modern TLDs"
test_tlds '["tv", "ws", "to", "la"]' "Novelty TLDs"
test_tlds '["me", "bz", "sh", "cc"]' "Known inventory"

