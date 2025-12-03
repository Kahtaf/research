#!/bin/bash

OUTPUT_FILE="all_domains.txt"
> "$OUTPUT_FILE"

CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")
echo "Using CSRF: ${CSRF:0:20}..."

# Scrape with multiple offsets
for length in 100 150 200; do
    for start in 0 100 200 300 400 500 600 700 800; do
        echo "Fetching: offset=$start, length=$length..."

        curl -s 'https://micro.domains/urls/' \
          -H 'accept: application/json, text/javascript, */*; q=0.01' \
          -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
          -H 'origin: https://micro.domains' \
          -H 'referer: https://micro.domains/?' \
          -H 'x-csrftoken: '$CSRF \
          -H 'x-requested-with: XMLHttpRequest' \
          -b "csrftoken=$CSRF" \
          --data-raw "draw=10&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=length&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=price&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=price_renewal&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=2&order%5B0%5D%5Bdir%5D=asc&start=$start&length=$length&search%5Bvalue%5D=&search%5Bregex%5D=false&price=20&available=1&has_number=1&has_hyphen=0&price_renewal=20&tlds=null&domain_length=5&sort=price" >> "$OUTPUT_FILE"

        echo "" >> "$OUTPUT_FILE"
        sleep 0.5
    done
done

echo "✓ Done! Results in $OUTPUT_FILE"

# Count how many valid JSON objects we got
python3 << 'PYEOF'
import json
import sys

count = 0
with open('all_domains.txt') as f:
    content = f.read()
    
# Split by empty lines and find JSON objects
for line in content.split('\n\n'):
    if line.strip().startswith('{'):
        try:
            j = json.loads(line)
            urls = j.get('urls', [])
            count += len(urls)
        except:
            pass

print(f"Total domains collected: {count}")
PYEOF
