#!/bin/bash

# Get CSRF token
CSRF=$(curl -s 'https://micro.domains/' | grep -oP "var csrftoken = '\K[^']+")
echo "CSRF Token: ${CSRF:0:20}..."
echo ""

# All 2-letter TLDs
TLDs_2letter="ac ai bz ca cc ch cm co cx de es eu fm fr gg id in io is la li me mx nl pe ph pw sg sh so to tv uk us vc ws"

# All 3-letter TLDs (abbreviated for batch testing)
TLDs_3letter="app art bar bid bio biz boo cab cam car ceo com dad day dev diy dog eco esq fan fit foo fun fyi gay gdn how icu inc ing ink kim krd lat law llc lol ltd mba men moe mom mov net new ngo nyc one ong onl org phd pro pub red rip run sex ski soy tax tel top uno vet vin vip win wtf xxx xyz zip"

OUTPUT_DIR="comprehensive_tld_results"
mkdir -p "$OUTPUT_DIR"

# Function to batch test TLDs
batch_test_tlds() {
    local tld_list=$1
    local batch_name=$2
    local output_file="$OUTPUT_DIR/${batch_name}.json"
    
    # Build JSON array
    local tlds_array="["
    local first=true
    for tld in $tld_list; do
        if [ "$first" = false ]; then
            tlds_array="${tlds_array},"
        fi
        tlds_array="${tlds_array}\"${tld}\""
        first=false
    done
    tlds_array="${tlds_array}]"
    
    # URL encode
    local tlds_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$tlds_array'))")
    
    echo "Testing $batch_name..."
    echo "  TLDs: $tld_list"
    
    curl -s 'https://micro.domains/urls/' \
      -H 'accept: application/json' \
      -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
      -H 'origin: https://micro.domains' \
      -H "x-csrftoken: $CSRF" \
      -H 'x-requested-with: XMLHttpRequest' \
      -b "csrftoken=$CSRF" \
      --data-raw "draw=10&start=0&length=200&search%5Bvalue%5D=&search%5Bregex%5D=false&price=99999&available=1&has_number=0&has_hyphen=0&price_renewal=99999&tlds=$tlds_encoded&domain_length=5&sort=price" \
      > "$output_file"
    
    sleep 0.5
}

# Test 2-letter TLDs in groups of 10
echo "=== Testing 2-Letter TLDs ==="
i=0
batch=""
for tld in $TLDs_2letter; do
    batch="$batch $tld"
    ((i++))
    if [ $i -eq 10 ] || [ "$tld" = "$(echo $TLDs_2letter | awk '{print $NF}')" ]; then
        batch_test_tlds "$batch" "2letter_batch_$((i/10+1))"
        batch=""
        i=0
    fi
done

echo ""
echo "=== Testing 3-Letter TLDs ==="
# Test 3-letter TLDs in groups of 15
i=0
batch=""
for tld in $TLDs_3letter; do
    batch="$batch $tld"
    ((i++))
    if [ $i -eq 15 ] || [ "$tld" = "$(echo $TLDs_3letter | awk '{print $NF}')" ]; then
        batch_test_tlds "$batch" "3letter_batch_$((i/15+1))"
        batch=""
        i=0
    fi
done

echo ""
echo "✓ Comprehensive TLD search complete!"
echo "  Results saved to $OUTPUT_DIR/"
