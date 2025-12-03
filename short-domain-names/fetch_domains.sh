#!/bin/bash

# Get fresh CSRF token
echo "Fetching CSRF token..."
CSRF_TOKEN=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")

if [ -z "$CSRF_TOKEN" ]; then
    echo "Failed to get CSRF token"
    exit 1
fi

echo "Got CSRF token: ${CSRF_TOKEN:0:20}..."

# Make request to API with pagination
OUTPUT_FILE="domains_raw.json"
> "$OUTPUT_FILE"  # Clear file

for start in 0 100 200 300 400 500 600 700 800 900 1000; do
    echo "Fetching domains from offset $start..."

    curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json, text/javascript, */*; q=0.01' \
      -H 'accept-language: en-US,en;q=0.9' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'origin: https://micro.domains' \
      -H 'referer: https://micro.domains/?' \
      -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
      -H "x-csrftoken: $CSRF_TOKEN" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF_TOKEN" \
      --data-raw "draw=10&start=$start&length=100&search%5Bvalue%5D=&search%5Bregex%5D=false&price=20&available=1&has_number=1&has_hyphen=0&price_renewal=20&domain_length=5&sort=price" \
      >> "$OUTPUT_FILE"

    echo "" >> "$OUTPUT_FILE"
    sleep 0.5
done

echo "Results saved to $OUTPUT_FILE"
