#!/bin/bash

# Get fresh CSRF token
CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")
echo "CSRF Token: ${CSRF:0:20}..."

# Test multiple TLD combinations
# Using URL-encoded JSON arrays for tlds parameter

declare -A tld_sets=(
    ["popular"]='["com","io","co","net"]'
    ["country"]='["ca","uk","de","fr"]'
    ["short"]='["sh","cc","ai","bz"]'
    ["tech"]='["tech","dev","app","rocks"]'
    ["misc"]='["tv","be","me","ws"]'
)

OUTPUT_DIR="multi_tld_data"
mkdir -p "$OUTPUT_DIR"

for label in "${!tld_sets[@]}"; do
    tlds_json="${tld_sets[$label]}"
    # URL encode the JSON array
    tlds_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$tlds_json'))")
    
    echo ""
    echo "=== Testing TLDs: $label ($tlds_json) ==="
    
    output_file="$OUTPUT_DIR/domains_${label}.json"
    > "$output_file"
    
    # Fetch multiple pages
    for start in 0 100 200 300; do
        echo "  Fetching offset $start..."
        
        curl -s 'https://micro.domains/urls/' \
          -H 'accept: application/json, text/javascript, */*; q=0.01' \
          -H 'accept-language: en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7' \
          -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
          -H 'dnt: 1' \
          -H 'origin: https://micro.domains' \
          -H 'referer: https://micro.domains/' \
          -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
          -H "x-csrftoken: $CSRF" \
          -H 'x-requested-with: XMLHttpRequest' \
          -b "csrftoken=$CSRF" \
          --data-raw "draw=10&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=length&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=price&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=price_renewal&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=asc&start=$start&length=100&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$tlds_encoded&domain_length=5&sort=price" \
          >> "$output_file"
        
        echo "" >> "$output_file"
        sleep 0.5
    done
done

echo ""
echo "✓ Multi-TLD search complete. Results saved to $OUTPUT_DIR/"
echo ""

# Analyze results
python3 << 'PYEOF'
import json
import os
from collections import defaultdict

tld_stats = defaultdict(lambda: {'count': 0, 'min_price': 999, 'max_price': 0, 'domains': []})

for filename in os.listdir('multi_tld_data'):
    if filename.endswith('.json'):
        filepath = os.path.join('multi_tld_data', filename)
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith('{'):
                    try:
                        j = json.loads(line)
                        for item in j.get('urls', []):
                            domain_name = item.get('domain', '')
                            tld = item.get('tld', '')
                            price = float(item.get('price', 999))
                            renewal = float(item.get('price_renewal', 999))
                            
                            if domain_name and tld:
                                full_domain = f"{domain_name}.{tld}"
                                tld_stats[tld]['count'] += 1
                                tld_stats[tld]['min_price'] = min(tld_stats[tld]['min_price'], price)
                                tld_stats[tld]['max_price'] = max(tld_stats[tld]['max_price'], price)
                                
                                if len(tld_stats[tld]['domains']) < 5:
                                    tld_stats[tld]['domains'].append(f"{full_domain} (${price:.2f})")
                    except:
                        pass

print("TLD Comparison Summary:")
print("="*80)
print(f"{'TLD':8s} {'Count':8s} {'Min Price':12s} {'Max Price':12s} {'Sample Domains'}")
print("="*80)

for tld in sorted(tld_stats.keys()):
    stats = tld_stats[tld]
    min_price = stats['min_price'] if stats['min_price'] < 999 else 'N/A'
    max_price = stats['max_price'] if stats['max_price'] > 0 else 'N/A'
    samples = ', '.join(stats['domains'][:3])
    
    print(f"{tld:8s} {stats['count']:8d} ${str(min_price):11s} ${str(max_price):11s} {samples}")

PYEOF
