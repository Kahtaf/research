#!/usr/bin/env python3
"""
Domain search scraper for micro.domains
Paginates through domain search results to find visually appealing 5-letter domains.
"""

import requests
import json
import time
import sys
from urllib.parse import urlencode
from collections import defaultdict

# CSRF tokens from the curl request (may need updating)
CSRF_TOKEN = "HYPnq8hX47x7Wnh2be4pf3nLjoUptHwnW8MlGcG1Rr4FeQJi2tZRfKWLDBAYtOBk"
X_CSRF_TOKEN = "843NTslKgtXiNY66ugM6bqZubNcunR9Dne0L9wKO3NuQ5rymlvHyb7yuv0S3nYeA"

BASE_URL = "https://micro.domains/urls/"

HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'dnt': '1',
    'origin': 'https://micro.domains',
    'priority': 'u=1, i',
    'referer': 'https://micro.domains/?',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-csrftoken': X_CSRF_TOKEN,
    'x-requested-with': 'XMLHttpRequest',
}

COOKIES = {
    'csrftoken': CSRF_TOKEN,
}


def build_request_data(start, length):
    """Build the request data for domain search."""
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
        'price': '20',
        'available': '1',
        'has_number': '1',
        'has_hyphen': '0',
        'price_renewal': '20',
        'tlds': 'null',
        'domain_length': '5',
        'sort': 'price',
    }
    return data


def query_domains(start, length):
    """Query domains from the API."""
    data = build_request_data(start, length)
    try:
        response = requests.post(
            BASE_URL,
            headers=HEADERS,
            cookies=COOKIES,
            data=data,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}", file=sys.stderr)
        return None


def is_interesting_domain(domain):
    """Check if a domain looks visually appealing."""
    # Convert to lowercase for analysis
    domain_lower = domain.lower()

    # Remove the TLD (last part after the dot)
    if '.' in domain_lower:
        name_part = domain_lower.split('.')[0]
    else:
        name_part = domain_lower

    # Check for interesting patterns
    interesting_reasons = []

    # Check if it forms a word or word-like
    common_words = {
        'about', 'acres', 'admin', 'adopt', 'audio', 'awake',
        'badge', 'beach', 'bears', 'birth', 'black', 'blade', 'blank', 'blend', 'blind', 'block', 'board', 'boats', 'books', 'brain', 'brand', 'bread', 'break', 'breed', 'brick', 'bride', 'brief', 'bring', 'brink', 'broad', 'broke', 'brown', 'build',
        'cable', 'cache', 'cadet', 'cages', 'cakes', 'calls', 'camps', 'cards', 'cargo', 'carry', 'cases', 'catch', 'cause', 'caves', 'chaos', 'charm', 'chart', 'cheap', 'cheat', 'check', 'chess', 'chest', 'chief', 'child', 'china', 'chips', 'chose', 'civic', 'civil', 'claim', 'class', 'clean', 'clear', 'click', 'cliff', 'climb', 'cloth', 'cloud', 'coach', 'coast', 'codes', 'coins', 'color', 'comet', 'comic', 'common', 'coral', 'cores', 'corps', 'costs', 'could', 'count', 'court', 'cover', 'coves', 'crack', 'craft', 'crash', 'crate', 'crazy', 'cream', 'creek', 'crime', 'crisp', 'cross', 'crowd', 'crown', 'crude', 'crush', 'cyber',
        'daily', 'dairy', 'dance', 'dealt', 'dears', 'death', 'debug', 'debut', 'decor', 'decoy', 'delay', 'delta', 'dense', 'depth', 'devil', 'diary', 'dicer', 'dices', 'digit', 'diner', 'disco', 'diver', 'divot', 'docks', 'dodge', 'doing', 'dolls', 'donor', 'doors', 'dosed', 'doses', 'doubt', 'dough', 'doves', 'downs', 'draft', 'drain', 'drake', 'drank', 'drape', 'dread', 'dream', 'dress', 'dried', 'drier', 'dries', 'drift', 'drill', 'drink', 'drive', 'droit', 'droll', 'drone', 'drool', 'droop', 'drops', 'dross', 'drove', 'drown', 'drums', 'drunk', 'dudes', 'dulls', 'dummy', 'dumpy', 'dunce', 'dunes', 'dusky', 'dusty', 'dutch', 'duvet', 'dwell', 'dying',
        'eager', 'eagle', 'early', 'earth', 'eased', 'easel', 'easer', 'eases', 'eater', 'ebony', 'edict', 'edged', 'edger', 'edges', 'edits', 'egged', 'egret', 'eject', 'elbow', 'elder', 'elect', 'elite', 'elope', 'elude', 'email', 'embed', 'ember', 'emcee', 'emoji', 'enamel', 'enemy', 'enjoy', 'enrol', 'ensue', 'enter', 'entry', 'envoy', 'epoch', 'equal', 'equip', 'erase', 'erect', 'error', 'erupt', 'essay', 'ether', 'ethic', 'ethos', 'evade', 'event', 'every', 'evict', 'evoke', 'exact', 'exalt', 'exams', 'excel', 'exert', 'exile', 'exist', 'expel', 'exert', 'extra', 'exude', 'exult', 'eyelid', 'eyes',
        'fable', 'faced', 'facer', 'faces', 'facet', 'facts', 'faded', 'fades', 'fails', 'faint', 'fairs', 'fairy', 'faith', 'fake', 'falls', 'false', 'fames', 'fancy', 'fangs', 'farms', 'fatal', 'fated', 'fates', 'fatty', 'fault', 'fauna', 'favor', 'faxed', 'faxes', 'fazed', 'fears', 'feast', 'feats', 'feeds', 'feels', 'fence', 'ferns', 'ferry', 'fetal', 'fetch', 'fetid', 'feud', 'fever', 'fewer', 'fiber', 'field', 'fiend', 'fiery', 'fifes', 'fifth', 'fifty', 'fight', 'file', 'files', 'fills', 'films', 'filth', 'final', 'finch', 'finds', 'fined', 'finer', 'fines', 'finny', 'fiona', 'fires', 'firms', 'first', 'fishy', 'fists', 'fits', 'fixed', 'fixer', 'fixes', 'fixer', 'fizzy', 'fjord', 'flack', 'flags', 'flail', 'flair', 'flake', 'flaky', 'flame', 'flank', 'flaps', 'flare', 'flash', 'flask', 'flats', 'flaunt', 'flavor', 'flaws', 'fleas', 'fleck', 'flees', 'fleet', 'flesh', 'flick', 'flier', 'flies', 'flight', 'fling', 'flint', 'flips', 'flirt', 'float', 'flock', 'flood', 'floor', 'flops', 'flora', 'flour', 'flout', 'flows', 'fluid', 'fluke', 'flung', 'flush', 'flute', 'foamy', 'focal', 'focus', 'foggy', 'fogey', 'foils', 'folds', 'foley', 'folks', 'folly', 'fonts', 'foods', 'fools', 'foots', 'foray', 'force', 'forge', 'forgo', 'forks', 'forms', 'forte', 'forth', 'forty', 'forum', 'foyer', 'frail', 'frame', 'frank', 'fraud', 'freak', 'freer', 'frees', 'fresh', 'friar', 'fried', 'fries', 'frill', 'fringe', 'frisk', 'frizz', 'frock', 'froggy', 'front', 'frost', 'froth', 'frown', 'froze', 'fruit', 'fryer', 'fuels', 'fugue', 'fully', 'fumes', 'funds', 'funky', 'funny', 'furor', 'furry', 'fused', 'fuses', 'fussy', 'fuzzy',
        'gains', 'gales', 'gamer', 'games', 'gangs', 'gates', 'gauge', 'gaunt', 'gauze', 'gavel', 'gawks', 'gayer', 'gaily', 'games', 'gears', 'geeks', 'genus', 'germs', 'giddy', 'gifts', 'gigue', 'gills', 'girls', 'given', 'giver', 'gives', 'gizmo', 'glade', 'glads', 'gland', 'glare', 'glass', 'glaze', 'gleam', 'glean', 'glees', 'glens', 'glide', 'glint', 'gloom', 'glory', 'gloss', 'glove', 'glued', 'glues', 'gluey', 'gnarl', 'gnash', 'gnats', 'gnome', 'goads', 'goals', 'goats', 'godly', 'going', 'golds', 'golfs', 'goods', 'gooey', 'goofy', 'goons', 'goose', 'gored', 'gores', 'gorge', 'gorse', 'gotta', 'gouge', 'gourd', 'gowns', 'grabs', 'grace', 'grade', 'grads', 'graft', 'grail', 'grain', 'grand', 'grant', 'grape', 'graph', 'grasp', 'grass', 'grate', 'grave', 'gravy', 'grays', 'graze', 'great', 'greed', 'greek', 'green', 'greet', 'grey', 'grids', 'grief', 'grill', 'grime', 'grimy', 'grind', 'grins', 'grins', 'gripe', 'grist', 'grits', 'groan', 'grock', 'groin', 'groom', 'grope', 'gross', 'group', 'grout', 'grove', 'growl', 'grows', 'grown', 'grubs', 'gruff', 'grunt', 'guard', 'guava', 'guess', 'guest', 'guide', 'guild', 'guilt', 'guise', 'gulch', 'gulfs', 'gulls', 'gulps', 'gummy', 'gumbo', 'gummy', 'gummy', 'gunky', 'gusts', 'gusty', 'gutter', 'guys',
        'habit', 'hacks', 'haiku', 'hails', 'hairs', 'hairy', 'halal', 'haled', 'hales', 'halts', 'halve', 'hands', 'handy', 'hangs', 'hanks', 'happy', 'hardy', 'harem', 'harem', 'hares', 'harks', 'harms', 'harsh', 'haste', 'hasty', 'hated', 'hater', 'hates', 'hauls', 'haunt', 'haven', 'havoc', 'hawks', 'hawks', 'haystack', 'hazel', 'heads', 'heals', 'heaps', 'hears', 'heart', 'heath', 'heats', 'heave', 'heavy', 'hecks', 'hedge', 'heeds', 'heels', 'hefty', 'heidi', 'heils', 'heirs', 'heist', 'helix', 'hello', 'helps', 'hence', 'henna', 'henry', 'herbs', 'herds', 'here', 'heron', 'heros', 'hertz', 'hexed', 'hexes', 'hider', 'hides', 'hiked', 'hiker', 'hikes', 'hills', 'hilly', 'hilts', 'hinds', 'hinge', 'hints', 'hippo', 'hippy', 'hired', 'hires', 'hitch', 'hives', 'hoard', 'hoary', 'hobby', 'hocks', 'hodge', 'hoers', 'hogan', 'hoist', 'holds', 'holes', 'holly', 'holmes', 'holms', 'homed', 'homer', 'homes', 'hones', 'honey', 'honks', 'honor', 'hoods', 'hoofs', 'hooks', 'hoops', 'hoots', 'hoped', 'hopes', 'hoppy', 'horde', 'horns', 'horny', 'horse', 'hosed', 'hoses', 'hosts', 'hotel', 'hound', 'hours', 'house', 'hovel', 'hover', 'howdy', 'howls', 'hubs', 'huffed', 'huffs', 'huffy', 'huger', 'hulks', 'hulky', 'hulls', 'human', 'humid', 'humor', 'humps', 'humus', 'hunch', 'hunks', 'hunky', 'hunts', 'hurls', 'hurry', 'hurts', 'husky', 'hutch', 'hyena', 'hymns', 'hypes', 'hyper',
        'icily', 'icing', 'ickle', 'icons', 'ideal', 'ideas', 'ident', 'idyll', 'igloo', 'image', 'imbed', 'imbue', 'imply', 'inane', 'inbox', 'incur', 'index', 'india', 'indie', 'inept', 'inert', 'infer', 'infos', 'infra', 'ingle', 'ingot', 'injoy', 'inlet', 'inner', 'input', 'inset', 'inter', 'intone', 'intro', 'inure', 'irate', 'irked', 'irony', 'islet', 'issue', 'itchy', 'items', 'ivory', 'ivied',
        'jacks', 'jaded', 'jades', 'jaggy', 'jails', 'jaunt', 'jawed', 'jeans', 'jeeps', 'jeers', 'jello', 'jelly', 'jesse', 'jests', 'jetty', 'jewel', 'jiffy', 'jihad', 'jilts', 'jinks', 'jinns', 'jinxs', 'jives', 'joacs', 'joans', 'jobed', 'jobes', 'jocko', 'jocks', 'joeys', 'johns', 'joins', 'joint', 'joist', 'joked', 'joker', 'jokes', 'jolly', 'jolts', 'joule', 'joust', 'jowly', 'jowls', 'joynt', 'joystick', 'juana', 'judas', 'judge', 'juice', 'juicy', 'jules', 'julep', 'july', 'jumbo', 'jumps', 'jumpy', 'junco', 'junes', 'junks', 'junky', 'juror', 'jurus', 'jutes', 'jutty',
        'kayak', 'kayla', 'keeps', 'keeve', 'kefir', 'kelps', 'kelly', 'kemps', 'kenaf', 'kendo', 'kenos', 'kente', 'kenya', 'keyed', 'keyer', 'khaki', 'khan', 'khans', 'khyar', 'kicks', 'kiddo', 'kiddos', 'kiddy', 'kided', 'kides', 'kills', 'kilns', 'kilos', 'kilts', 'kimes', 'kinds', 'kines', 'kings', 'kinks', 'kinky', 'kinos', 'kinse', 'kiosk', 'kipped', 'kipper', 'kirby', 'kirks', 'kerns', 'kerry', 'kesas', 'ketch', 'keted', 'ketol', 'ketos', 'ketts', 'keyed', 'khaki', 'khans', 'kicks', 'kiddo', 'kiddy', 'kills', 'kilns', 'kilos', 'kilts', 'kinds', 'kines', 'kings', 'kinks', 'kinky', 'kinos', 'kiosk', 'kited', 'kiter', 'kites', 'kithe', 'kitty', 'kiwis', 'klans', 'knack', 'knags', 'knaps', 'knave', 'knead', 'kneed', 'kneel', 'knees', 'knelt', 'kneve', 'knife', 'knigs', 'knish', 'knits', 'knobs', 'knock', 'knoll', 'knops', 'knosp', 'knots', 'known', 'knows', 'knubs', 'knuff', 'knurl', 'kraut', 'krios', 'kudos', 'kyack', 'kyaks', 'kyars', 'kyats', 'kyloe', 'kynes',
        'label', 'labor', 'laced', 'lacer', 'laces', 'lacey', 'lacks', 'laded', 'laden', 'lades', 'ladic', 'ladle', 'laers', 'laevo', 'lager', 'lages', 'laics', 'laird', 'lairs', 'lairy', 'laith', 'laked', 'laker', 'lakes', 'lalls', 'lamed', 'lamen', 'lamer', 'lames', 'lamia', 'lammy', 'lamps', 'lanai', 'lance', 'lands', 'landy', 'lanes', 'lange', 'lanky', 'lanny', 'lansa', 'lansa', 'lansy', 'laoch', 'laorn', 'lapel', 'lapps', 'lapse', 'laras', 'larch', 'lards', 'lardy', 'lares', 'large', 'largo', 'larks', 'larky', 'larny', 'larry', 'larva', 'larum', 'larva', 'lases', 'lasha', 'lashe', 'lashi', 'lashs', 'lasso', 'lassy', 'laste', 'lasts', 'late', 'lated', 'laten', 'later', 'lates', 'lathe', 'lathi', 'laths', 'lathy', 'latic', 'latis', 'laton', 'laude', 'lauds', 'laugh', 'laund', 'laura', 'laure', 'laurs', 'laury', 'lause', 'lauta', 'laved', 'laven', 'laver', 'laves', 'lavin', 'lavor', 'lavis', 'lavos', 'lavra', 'lavre', 'lavre', 'lavro', 'lavvy', 'lawer', 'lawes', 'lawly', 'lawna', 'lawne', 'lawny', 'lawre', 'lawry', 'laws', 'lawsuit', 'lawsy', 'lawte', 'lawty', 'laxed', 'laxen', 'laxer', 'laxes', 'laxly', 'laxon', 'layed', 'layer', 'layia', 'layid', 'layin', 'lazar', 'laze', 'lazed', 'lazes', 'lazily', 'lazos', 'lazos', 'lazos', 'lazus', 'lazzy',
    }

    # Symmetry checks
    if len(name_part) == 5:
        # Check for palindromes or symmetrical patterns
        if name_part == name_part[::-1]:
            interesting_reasons.append("palindrome")

        # Check for repeated patterns (like aa, bb, etc)
        if name_part[0] == name_part[1] or name_part[3] == name_part[4]:
            interesting_reasons.append("repeated letters")

        # Check for digit patterns
        if any(c.isdigit() for c in name_part):
            if all(c.isdigit() or c == '0' or c == 'x' for c in name_part):
                interesting_reasons.append("hex-like pattern")

        # Check if it's a recognizable word
        if name_part in common_words:
            interesting_reasons.append("word")

    # Check for common misspellings or fun variations
    fun_patterns = [
        'bussy', 'catty', 'ditzy', 'dizzy', 'fatty', 'gassy',
        'giddy', 'goofy', 'gotta', 'handy', 'happy', 'hippy',
        'jazzy', 'jolly', 'kinda', 'kitty', 'limpy', 'loopy',
        'messy', 'missy', 'mopey', 'moody', 'nasty', 'netty',
        'pansy', 'perky', 'picky', 'pithy', 'potty', 'puppy',
        'pussy', 'putty', 'sassy', 'silly', 'sissy', 'soggy',
        'sorry', 'spicy', 'wimpy', 'zippy',
    ]

    if name_part in fun_patterns:
        interesting_reasons.append("fun pattern")

    return len(interesting_reasons) > 0, interesting_reasons


def scrape_domains(max_requests=20, length=100):
    """Scrape domains by paginating through results."""
    all_domains = []
    start = 0
    request_count = 0
    total_results = 0

    print(f"Starting domain scrape with length={length}")

    while request_count < max_requests:
        print(f"\nRequest {request_count + 1}/{max_requests}: start={start}, length={length}")

        result = query_domains(start, length)

        if not result:
            print("Failed to get results, stopping")
            break

        data = result.get('data', [])
        records_total = result.get('recordsTotal', 0)

        if not data:
            print(f"No more domains found. Total processed: {total_results}")
            break

        print(f"Got {len(data)} results (total available: {records_total})")

        for domain_info in data:
            domain = domain_info.get('0', '')  # The domain name
            price = float(domain_info.get('price', 999))
            price_renewal = float(domain_info.get('price_renewal', 999))

            if domain and price < 20 and price_renewal < 20:
                all_domains.append({
                    'domain': domain,
                    'price': price,
                    'renewal': price_renewal,
                })
                total_results += 1

        start += length
        request_count += 1

        # Be respectful with requests
        time.sleep(0.5)

        # Stop if we've processed all results
        if total_results >= records_total:
            break

    return all_domains


def main():
    print("=== Domain Scraper for micro.domains ===\n")

    # Test with large page size
    print("Scraping domains with length=100 for higher throughput...\n")
    domains = scrape_domains(max_requests=30, length=100)

    print(f"\n\nTotal domains found: {len(domains)}\n")

    # Filter for interesting domains
    interesting = []
    for domain_info in domains:
        domain = domain_info['domain']
        is_interesting, reasons = is_interesting_domain(domain)

        if is_interesting:
            interesting.append({
                'domain': domain,
                'price': domain_info['price'],
                'renewal': domain_info['renewal'],
                'reasons': reasons,
            })

    print(f"Interesting domains found: {len(interesting)}\n")
    print("=" * 60)

    # Sort by price
    interesting.sort(key=lambda x: x['price'])

    # Display results
    for i, item in enumerate(interesting[:30], 1):
        print(f"{i:2d}. {item['domain']:20s} | Price: ${item['price']:5.2f} | Renewal: ${item['renewal']:5.2f} | {', '.join(item['reasons'])}")

    # Save to file
    with open('domains_found.json', 'w') as f:
        json.dump(interesting, f, indent=2)

    print(f"\nResults saved to domains_found.json")


if __name__ == '__main__':
    main()
