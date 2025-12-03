import json

all_domains = []

# Parse JSON from file
with open('all_domains.txt') as f:
    for line in f:
        line = line.strip()
        if line.startswith('{'):
            try:
                j = json.loads(line)
                urls = j.get('urls', [])
                for url_item in urls:
                    domain_name = url_item.get('domain', '')
                    tld = url_item.get('tld', '')
                    price = float(url_item.get('price', 999))
                    renewal = float(url_item.get('price_renewal', 999))
                    
                    if domain_name and tld and price < 20 and renewal < 20:
                        full_domain = f"{domain_name}.{tld}"
                        all_domains.append({
                            'domain': full_domain,
                            'name': domain_name,
                            'tld': tld,
                            'price': price,
                            'renewal': renewal,
                        })
            except:
                pass

print(f"Total domains collected: {len(all_domains)}")

# Find the most interesting ones
interesting = []

for item in all_domains:
    domain_name = item['name'].lower()
    reasons = []
    
    if len(domain_name) == 5:
        # Palindromes
        if domain_name == domain_name[::-1]:
            reasons.append('palindrome')
            interesting.append({**item, 'reasons': reasons})
            continue
        
        # Hex-like patterns (has 0 and x)
        if '0' in domain_name and 'x' in domain_name:
            reasons.append('hex_like')
            interesting.append({**item, 'reasons': reasons})
            continue
        
        # Double letter patterns at start/end
        if domain_name[0] == domain_name[1] and domain_name[3] == domain_name[4]:
            reasons.append('symmetrical_doubles')
            interesting.append({**item, 'reasons': reasons})
            continue
        
        # Cool number patterns like "1337" style
        if domain_name in ['1337s', '1337h', '1337l', 'd34d5', 'n00b5', 'l33t5', 'd4rk5']:
            reasons.append('l33t')
            interesting.append({**item, 'reasons': reasons})
            continue
        
        # Pronounceable looking domains with numbers
        # Look for number+vowel+consonant patterns
        vowels = set('aeiouy')
        consonants = set('bcdfghjklmnprstvwxz')
        numbers = set('0123456789')
        
        # Check if it has a good mix and looks cool
        num_count = sum(1 for c in domain_name if c.isdigit())
        letter_count = sum(1 for c in domain_name if c.isalpha())
        
        if num_count >= 1 and num_count <= 3 and letter_count >= 2:
            # Check for patterns like "0r0" or "1o1" or "b1g" 
            has_interesting_pattern = False
            
            # Check for zero/oh look-alikes
            if domain_name.replace('0', 'o').lower() != domain_name.lower():
                has_interesting_pattern = True
            # Check for l/1 look-alikes
            if domain_name.replace('1', 'l').lower() != domain_name.lower():
                has_interesting_pattern = True
            # Check for 5/s look-alikes
            if domain_name.replace('5', 's').lower() != domain_name.lower():
                has_interesting_pattern = True
            # Check for 3/e look-alikes
            if domain_name.replace('3', 'e').lower() != domain_name.lower():
                has_interesting_pattern = True
            # Check for 4/a look-alikes
            if domain_name.replace('4', 'a').lower() != domain_name.lower():
                has_interesting_pattern = True
            
            if has_interesting_pattern:
                reasons = ['leet_like']
                interesting.append({**item, 'reasons': reasons})

# Remove duplicates
seen_domains = set()
unique_interesting = []
for item in interesting:
    if item['domain'] not in seen_domains:
        seen_domains.add(item['domain'])
        unique_interesting.append(item)

# Sort by price
unique_interesting.sort(key=lambda x: (x['price'], x['domain']))

print(f"Interesting domains found: {len(unique_interesting)}\n")

# Show top
print("="*80)
print(f"{'#':3s} {'Domain':20s} {'Price':8s} {'Renewal':8s} {'Traits'}")
print("="*80)

for i, item in enumerate(unique_interesting[:50], 1):
    traits = ', '.join(item['reasons'])
    print(f"{i:3d} {item['domain']:20s} ${item['price']:7.2f} ${item['renewal']:7.2f} {traits}")

if len(unique_interesting) < 20:
    print(f"\nOnly found {len(unique_interesting)} interesting domains, getting more...")
    # If we don't have enough, include some of the coolest looking ones
    coolest = []
    for item in all_domains:
        domain_name = item['name'].lower()
        if len(domain_name) == 5:
            # Include domains that look cool even if not matching above patterns
            if any(c in domain_name for c in '04e1lo8z35'):  # Cool looking combos
                if domain_name.count(domain_name[0]) >= 2:  # Has repeating letters
                    coolest.append({**item, 'reasons': ['cool_looking']})
    
    coolest.sort(key=lambda x: (x['price'], x['domain']))
    unique_interesting.extend(coolest[:20])
    unique_interesting = list({d['domain']: d for d in unique_interesting}.values())
    unique_interesting.sort(key=lambda x: (x['price'], x['domain']))

# Save results
with open('domains_interesting.json', 'w') as f:
    json.dump(unique_interesting[:30], f, indent=2)

print(f"\n✓ Interesting domains saved to domains_interesting.json")
