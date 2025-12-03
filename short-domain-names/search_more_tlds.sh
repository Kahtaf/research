#!/bin/bash

CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")

# Test more TLD combinations
declare -A searches=(
    ["geo_codes"]='["ca","uk","au","nz"]'
    ["short_codes"]='["sh","cc","to","vi"]'
    ["city_codes"]='["la","ly","sc","st"]'
    ["misc2"]='["gp","gy","hn","ht"]'
)

for label in "${!searches[@]}"; do
    tlds_json="${searches[$label]}"
    tlds_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$tlds_json'))")
    
    echo "Testing: $label"
    
    curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'origin: https://micro.domains' \
      -H "x-csrftoken: $CSRF" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF" \
      --data-raw "draw=10&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=length&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=price&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=price_renewal&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=asc&start=0&length=100&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$tlds_encoded&domain_length=5&sort=price" | python3 << 'EOFPYTHON'
import sys, json
try:
    j = json.loads(sys.stdin.read())
    urls = j.get('urls', [])
    if urls:
        by_tld = {}
        for u in urls:
            tld = u.get('tld', '')
            if tld not in by_tld:
                by_tld[tld] = []
            by_tld[tld].append(u)
        
        for tld in sorted(by_tld.keys()):
            items = by_tld[tld]
            min_p = min(float(u['price']) for u in items)
            max_p = max(float(u['price']) for u in items)
            sample = f"{items[0]['domain']}.{tld}"
            print(f"  .{tld}: {len(items)} domains | ${min_p:.2f}-${max_p:.2f} | e.g., {sample}")
    else:
        print("  No domains found")
except Exception as e:
    print(f"  Error: {e}")
EOFPYTHON
    
    sleep 0.3
done
