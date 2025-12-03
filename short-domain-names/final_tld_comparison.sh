#!/bin/bash

CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")

echo "Testing TLD groups with the working format from earlier..."
echo "CSRF: ${CSRF:0:20}..."
echo ""

# Use exact format that worked earlier
test_group() {
    local label="$1"
    local tlds_json="$2"
    
    echo "Testing: $label"
    
    # URL encode using Python (same as before)
    local tlds_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$tlds_json'))")
    
    curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json, text/javascript, */*; q=0.01' \
      -H 'accept-language: en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'dnt: 1' \
      -H 'origin: https://micro.domains' \
      -H 'referer: https://micro.domains/?' \
      -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
      -H "x-csrftoken: $CSRF" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF" \
      --data-raw "draw=10&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=length&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=price&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=price_renewal&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=asc&start=0&length=200&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$tlds_encoded&domain_length=5&sort=price" | python3 << 'PYEND'
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
            sample = items[0]['domain']
            print(f"  .{tld}: {len(items):3d} | ${min_p:7.2f}-${max_p:7.2f} | {sample}.{tld}")
    else:
        print("  No domains")
except Exception as e:
    print(f"  Error: {str(e)[:50]}")
PYEND
    
    sleep 0.5
}

# Test various TLD combinations
test_group "Major 3-letter" '["com","net","org"]'
test_group "Tech 3-letter" '["app","dev","tech"]'
test_group "Trendy 2-letter" '["io","co","ai"]'
test_group "Creative 2-letter" '["tv","to","la"]'
test_group "Country 2-letter" '["ca","uk","de"]'
test_group "Novelty 2-letter" '["me","bz","ws"]'
test_group "Misc combos" '["sh","cc","is"]'
test_group "Mixed popular" '["com","io","me"]'
test_group "All cheap?" '["me","bz","cc","sh"]'

