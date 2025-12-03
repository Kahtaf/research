#!/bin/bash

CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")

# Test individual TLDs
declare -a tlds=("com" "io" "co" "net" "ca" "sh" "cc" "ai" "bz" "tv" "uk" "de")

OUTPUT_FILE="individual_tld_results.txt"
> "$OUTPUT_FILE"

for tld in "${tlds[@]}"; do
    echo "Testing .$tld..."
    
    # URL encode the tld as JSON array
    tlds_param="[%22$tld%22]"
    
    response=$(curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'origin: https://micro.domains' \
      -H "x-csrftoken: $CSRF" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF" \
      --data-raw "draw=10&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=length&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=price&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=price_renewal&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=asc&start=0&length=50&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$tlds_param&domain_length=5&sort=price")
    
    # Count results
    count=$(echo "$response" | python3 -c "import sys, json; j=json.load(sys.stdin); print(len(j.get('urls', [])))" 2>/dev/null || echo "0")
    
    if [ "$count" != "0" ] && [ "$count" != "" ]; then
        echo "  ✓ Found $count domains"
        echo "$response" | python3 -c "
import sys, json
j = json.load(sys.stdin)
urls = j.get('urls', [])
if urls:
    min_p = min(float(u['price']) for u in urls)
    max_p = max(float(u['price']) for u in urls)
    print(f'    Price range: \${min_p:.2f} - \${max_p:.2f}')
    for u in urls[:3]:
        print(f'      {u[\"domain\"]}.{u[\"tld\"]} \${u[\"price\"]:.2f}')
" 2>/dev/null || true
    else
        echo "  ✗ No domains found"
    fi
    
    sleep 0.3
done
