#!/usr/bin/env python3
"""
Final domain scraper for micro.domains
"""

import requests
import re
import json
import time
from typing import List, Dict, Tuple

class DomainScraper:
    def __init__(self):
        self.session = None
        self.csrf_token = None
        self.all_domains = []

    def setup_session(self):
        """Initialize session and get CSRF token."""
        self.session = requests.Session()
        try:
            response = self.session.get('https://micro.domains/', timeout=10)
            match = re.search(r"var csrftoken = '([^']+)'", response.text)
            if match:
                self.csrf_token = match.group(1)
                print(f"✓ Session established with CSRF token: {self.csrf_token[:20]}...")
                return True
        except Exception as e:
            print(f"✗ Failed to setup session: {e}")
        return False

    def build_request_data(self, start: int, length: int, **filters) -> Dict:
        """Build request data with given filters."""
        data = {
            'draw': '10',
            'columns[0][data]': '0',
            'columns[0][name]': '',
            'columns[0][searchable]': 'true',
            'columns[0][orderable]': 'false',
            'columns[0][search][value]': '',
            'columns[0][search][regex]': 'false',
            'columns[1][data]': 'length',
            'columns[1][name]': '',
            'columns[1][searchable]': 'true',
            'columns[1][orderable]': 'false',
            'columns[1][search][value]': '',
            'columns[1][search][regex]': 'false',
            'columns[2][data]': 'price',
            'columns[2][name]': '',
            'columns[2][searchable]': 'true',
            'columns[2][orderable]': 'true',
            'columns[2][search][value]': '',
            'columns[2][search][regex]': 'false',
            'columns[3][data]': 'price_renewal',
            'columns[3][name]': '',
            'columns[3][searchable]': 'true',
            'columns[3][orderable]': 'true',
            'columns[3][search][value]': '',
            'columns[3][search][regex]': 'false',
            'order[0][column]': '2',
            'order[0][dir]': 'asc',
            'start': str(start),
            'length': str(length),
            'search[value]': '',
            'search[regex]': 'false',
            'domain_length': '5',
            'price': '20',
            'price_renewal': '20',
            'sort': 'price',
        }

        for key, val in filters.items():
            data[key] = val

        return data

    def fetch_batch(self, start: int, length: int, **filters) -> Tuple[List, int]:
        """Fetch a batch of domains."""
        data = self.build_request_data(start, length, **filters)

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://micro.domains',
            'referer': 'https://micro.domains/?',
            'x-csrftoken': self.csrf_token,
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }

        try:
            response = self.session.post(
                'https://micro.domains/urls/',
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('data', []), result.get('recordsTotal', 0)
            else:
                return [], 0

        except Exception as e:
            return [], 0

    def parse_domain_info(self, item) -> Dict:
        """Parse a domain info item from the API response."""
        if isinstance(item, (list, tuple)) and len(item) >= 4:
            return {
                'domain': item[0],
                'length': item[1] if len(item) > 1 else 0,
                'price': float(item[2]) if len(item) > 2 else 999,
                'renewal': float(item[3]) if len(item) > 3 else 999,
            }
        elif isinstance(item, dict):
            return {
                'domain': item.get('0', ''),
                'length': item.get('length', 0),
                'price': float(item.get('price', 999)),
                'renewal': float(item.get('price_renewal', 999)),
            }
        return None

    def is_interesting(self, domain: str) -> Tuple[bool, List[str]]:
        """Check if a domain is visually interesting."""
        reasons = []
        parts = domain.split('.')
        name = parts[0].lower()

        if len(name) != 5:
            return False, reasons

        # Check for palindromes
        if name == name[::-1]:
            reasons.append('palindrome')

        # Check for repeating patterns
        if name[0] == name[1]:
            reasons.append('double_start')
        if name[3] == name[4]:
            reasons.append('double_end')

        if name[1] == name[2]:
            reasons.append('double_middle')

        # Common 5-letter words
        words = {
            'about', 'above', 'abuse', 'acute', 'admit', 'adopt', 'adult', 'after',
            'again', 'agent', 'agree', 'ahead', 'alarm', 'album', 'alert', 'alike',
            'alive', 'allow', 'alone', 'along', 'alter', 'angel', 'anger', 'angle',
            'angry', 'apart', 'apple', 'apply', 'arena', 'argue', 'arise', 'array',
            'arrow', 'aside', 'asset', 'audio', 'audit', 'avoid', 'awake', 'award',
            'aware', 'badly', 'bagel', 'baker', 'banal', 'bands', 'banks', 'badge',
            'baked', 'beach', 'beast', 'bears', 'begin', 'being', 'belly', 'below',
            'bench', 'bikes', 'bills', 'birth', 'black', 'blade', 'blame', 'blank',
            'blast', 'bleed', 'blend', 'bless', 'blind', 'block', 'blood', 'board',
            'boats', 'bogus', 'boost', 'booth', 'books', 'botch', 'bound', 'brain',
            'brand', 'brass', 'brave', 'bread', 'break', 'breed', 'brief', 'brick',
            'bride', 'bring', 'brink', 'broad', 'broke', 'brown', 'brush', 'build',
            'built', 'burst', 'buyer', 'cable', 'cages', 'cakes', 'camel', 'calls',
            'camps', 'canal', 'candy', 'canoe', 'canon', 'cards', 'cargo', 'carol',
            'carry', 'cases', 'catch', 'cause', 'caves', 'cedar', 'chain', 'chair',
            'chaos', 'charm', 'chart', 'chase', 'cheap', 'cheat', 'check', 'chess',
            'chest', 'chief', 'child', 'china', 'chips', 'chose', 'civic', 'civil',
            'claim', 'class', 'clean', 'clear', 'click', 'cliff', 'climb', 'clock',
            'close', 'cloth', 'cloud', 'coach', 'coast', 'codes', 'coins', 'color',
            'comet', 'comic', 'coral', 'cores', 'corps', 'costs', 'could', 'count',
            'court', 'cover', 'coves', 'crack', 'craft', 'crash', 'crate', 'crazy',
            'cream', 'creek', 'crime', 'crisp', 'cross', 'crowd', 'crown', 'crude',
            'crush', 'crust', 'cubic', 'curve', 'cyber', 'cycle', 'daily', 'dairy',
            'dance', 'dealt', 'dears', 'death', 'debut', 'decor', 'decoy', 'delay',
            'delta', 'dense', 'depth', 'derby', 'devil', 'diary', 'diner', 'disco',
            'diver', 'divot', 'docks', 'dodge', 'doing', 'donor', 'doors', 'doubt',
            'dough', 'doves', 'downs', 'draft', 'drain', 'drake', 'drank', 'draws',
            'dread', 'dream', 'dress', 'dried', 'drier', 'dries', 'drift', 'drill',
            'drink', 'drive', 'droit', 'droll', 'drone', 'drool', 'drops', 'dross',
            'drove', 'drown', 'drums', 'drunk', 'dudes', 'dully', 'dummy', 'dumpy',
            'dunce', 'dunes', 'dusty', 'dutch', 'dwell', 'dying', 'eager', 'eagle',
            'early', 'earn', 'earth', 'easel', 'eased', 'eases', 'eater', 'ebony',
            'edict', 'edged', 'edger', 'edges', 'edits', 'egged', 'egret', 'eject',
            'elbow', 'elder', 'elect', 'elite', 'elope', 'elude', 'email', 'embed',
            'ember', 'emcee', 'emoji', 'enemy', 'enjoy', 'enrol', 'ensue', 'enter',
            'entry', 'envoy', 'epoch', 'equal', 'equip', 'erase', 'erect', 'error',
            'erupt', 'essay', 'ether', 'ethic', 'ethos', 'evade', 'event', 'every',
            'evict', 'evoke', 'exact', 'exalt', 'exams', 'excel', 'exert', 'exile',
            'exist', 'expel', 'extra', 'exude', 'exult', 'fable', 'faced', 'facer',
            'faces', 'facet', 'facts', 'faded', 'fades', 'fails', 'faint', 'fairs',
            'fairy', 'faith', 'falls', 'false', 'fames', 'fancy', 'fangs', 'farms',
            'fatal', 'fated', 'fates', 'fatty', 'fault', 'fauna', 'favor', 'faxed',
            'faxes', 'fazed', 'fears', 'feast', 'feats', 'feeds', 'feels', 'fence',
            'ferns', 'ferry', 'fetal', 'fetch', 'fetid', 'fever', 'fewer', 'fiber',
            'field', 'fiend', 'fiery', 'fifes', 'fifth', 'fifty', 'fight', 'files',
            'fills', 'films', 'filth', 'final', 'finch', 'finds', 'fined', 'finer',
            'fines', 'finny', 'fires', 'firms', 'first', 'fishy', 'fists', 'fixed',
            'fixer', 'fixes', 'fizzy', 'fjord', 'flack', 'flags', 'flail', 'flair',
            'flake', 'flaky', 'flame', 'flank', 'flaps', 'flare', 'flash', 'flask',
            'flats', 'flaws', 'fleas', 'fleck', 'flees', 'fleet', 'flesh', 'flick',
            'flier', 'flies', 'fling', 'flint', 'flips', 'flirt', 'float', 'flock',
            'flood', 'floor', 'flops', 'flora', 'flour', 'flout', 'flows', 'fluid',
            'fluke', 'flung', 'flush', 'flute', 'foamy', 'focal', 'focus', 'foggy',
            'foils', 'folds', 'folks', 'folly', 'fonts', 'foods', 'fools', 'foots',
            'foray', 'force', 'forge', 'forgo', 'forks', 'forms', 'forte', 'forth',
            'forty', 'forum', 'foyer', 'frail', 'frame', 'frank', 'fraud', 'freak',
            'freer', 'frees', 'fresh', 'friar', 'fried', 'fries', 'frill', 'frisk',
            'frizz', 'frock', 'front', 'frost', 'froth', 'frown', 'froze', 'fruit',
            'fryer', 'fuels', 'fugue', 'fully', 'fumes', 'funds', 'funky', 'funny',
            'furor', 'furry', 'fused', 'fuses', 'fussy', 'fuzzy',
        }

        if name in words:
            reasons.append('word')

        # Check for number patterns
        if any(c.isdigit() for c in name):
            reasons.append('has_numbers')

            # Special pattern: 0x0 style (hex-like)
            if '0' in name and 'x' in name:
                reasons.append('hex_like')

        return len(reasons) > 0, reasons

    def scrape(self):
        """Main scraping loop."""
        print("\n" + "="*60)
        print("Starting domain scrape")
        print("="*60)

        # Try different parameter combinations
        filter_sets = [
            {
                'name': 'minimal filters',
                'filters': {}
            },
            {
                'name': 'with has_number only',
                'filters': {'has_number': '1', 'available': ''}
            },
        ]

        for filter_config in filter_sets:
            if len(self.all_domains) > 150:
                break

            print(f"\n--- Trying: {filter_config['name']} ---")

            for start in range(0, 5000, 100):
                if len(self.all_domains) > 200:
                    break

                print(f"Offset {start:5d}...", end=' ', flush=True)

                batch, total = self.fetch_batch(start, 100, **filter_config['filters'])

                if not batch:
                    print("no data")
                    break

                print(f"{len(batch):3d} results", flush=True)

                for item in batch:
                    parsed = self.parse_domain_info(item)
                    if parsed:
                        # Avoid duplicates
                        if not any(d['domain'] == parsed['domain'] for d in self.all_domains):
                            self.all_domains.append(parsed)

                time.sleep(0.3)

        return self.all_domains

    def filter_interesting(self) -> List[Dict]:
        """Filter for interesting domains."""
        interesting = []

        for domain_info in self.all_domains:
            domain = domain_info['domain']
            is_interesting, reasons = self.is_interesting(domain)

            if is_interesting:
                interesting.append({
                    'domain': domain,
                    'price': domain_info['price'],
                    'renewal': domain_info['renewal'],
                    'reasons': reasons,
                    'tld': domain.split('.')[-1] if '.' in domain else 'unknown',
                })

        # Sort by price then by domain name
        interesting.sort(key=lambda x: (x['price'], x['domain']))

        return interesting

    def save_results(self):
        """Save all results to files."""
        interesting = self.filter_interesting()

        print("\n" + "="*60)
        print(f"Total domains found: {len(self.all_domains)}")
        print(f"Interesting domains: {len(interesting)}")
        print("="*60 + "\n")

        # Save JSON
        with open('domains_found.json', 'w') as f:
            json.dump(interesting, f, indent=2)

        # Save CSV
        with open('domains_found.csv', 'w') as f:
            f.write("domain,price,renewal,tld,reasons\n")
            for item in interesting:
                f.write(f"{item['domain']},{item['price']:.2f},{item['renewal']:.2f},{item['tld']},\"{';'.join(item['reasons'])}\"\n")

        # Print top 50
        print("Top interesting domains:\n")
        for i, item in enumerate(interesting[:50], 1):
            print(f"{i:2d}. {item['domain']:20s} ${item['price']:6.2f}  | {', '.join(item['reasons'])}")

        print(f"\nFull results saved to:")
        print(f"  - domains_found.json")
        print(f"  - domains_found.csv")

        return interesting


if __name__ == '__main__':
    scraper = DomainScraper()

    if scraper.setup_session():
        scraper.scrape()
        scraper.save_results()
    else:
        print("Failed to setup session")
        exit(1)
