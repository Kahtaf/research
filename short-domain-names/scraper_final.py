#!/usr/bin/env python3
"""
Final domain scraper for micro.domains
"""

import requests
import re
import json
import time
from typing import List, Dict, Tuple
import os

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

        # Add custom filters
        for key, val in filters.items():
            data[key] = val

        return data

    def fetch_batch(self, start: int, length: int, **filters) -> Tuple[List, int]:
        """Fetch a batch of domains."""
        data = self.build_request_data(start, length, **filters)

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://micro.domains',
            'referer': 'https://micro.domains/?',
            'x-csrftoken': self.csrf_token,
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
                print(f"  ✗ HTTP {response.status_code}")
                return [], 0

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request error: {e}")
            return [], 0
        except json.JSONDecodeError:
            print(f"  ✗ Invalid JSON response")
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

        # Extract name without TLD
        parts = domain.split('.')
        name = parts[0].lower()

        if len(name) != 5:
            return False, reasons

        # Check for palindromes
        if name == name[::-1]:
            reasons.append('palindrome')

        # Check for repeating patterns
        if name[0] == name[1] or name[3] == name[4]:
            reasons.append('double_letters')

        if name[1] == name[2] or name[2] == name[3]:
            reasons.append('consecutive_repeats')

        # Common words
        words = {
            'about', 'acres', 'admin', 'adopt', 'audio', 'awake',
            'badge', 'beach', 'bears', 'birth', 'black', 'blade',
            'blank', 'blend', 'blind', 'block', 'board', 'boats',
            'books', 'brain', 'brand', 'bread', 'break', 'breed',
            'brick', 'bride', 'brief', 'bring', 'brink', 'broad',
            'broke', 'brown', 'build', 'cable', 'cache', 'cadet',
            'cakes', 'calls', 'camps', 'cards', 'cargo', 'carry',
            'cases', 'catch', 'cause', 'caves', 'chaos', 'charm',
            'chart', 'cheap', 'cheat', 'check', 'chess', 'chest',
            'chief', 'child', 'china', 'chips', 'chose', 'civic',
            'civil', 'claim', 'class', 'clean', 'clear', 'click',
            'cliff', 'climb', 'cloth', 'cloud', 'coach', 'coast',
            'codes', 'coins', 'color', 'comet', 'comic', 'coral',
            'cores', 'corps', 'costs', 'could', 'count', 'court',
            'cover', 'coves', 'crack', 'craft', 'crash', 'crate',
            'crazy', 'cream', 'creek', 'crime', 'crisp', 'cross',
            'crowd', 'crown', 'crude', 'crush', 'cyber', 'daily',
            'dairy', 'dance', 'dealt', 'dears', 'death', 'debug',
            'debut', 'decor', 'decoy', 'delay', 'delta', 'dense',
            'depth', 'devil', 'diary', 'dicer', 'dices', 'digit',
            'diner', 'disco', 'diver', 'divot', 'docks', 'dodge',
            'doing', 'dolls', 'donor', 'doors', 'doubt', 'dough',
            'doves', 'downs', 'draft', 'drain', 'drake', 'drank',
            'drape', 'dread', 'dream', 'dress', 'dried', 'drier',
            'dries', 'drift', 'drill', 'drink', 'drive', 'droit',
            'droll', 'drone', 'drool', 'droop', 'drops', 'dross',
            'drove', 'drown', 'drums', 'drunk', 'dudes', 'dulls',
            'dummy', 'dumpy', 'dunce', 'dunes', 'dusky', 'dusty',
            'dutch', 'duvet', 'dwell', 'dying', 'eager', 'eagle',
            'early', 'earth', 'eased', 'easel', 'easer', 'eases',
            'eater', 'ebony', 'edict', 'edged', 'edger', 'edges',
            'edits', 'egged', 'egret', 'eject', 'elbow', 'elder',
            'elect', 'elite', 'elope', 'elude', 'email', 'embed',
            'ember', 'emcee', 'emoji', 'enemy', 'enjoy', 'enrol',
            'ensue', 'enter', 'entry', 'envoy', 'epoch', 'equal',
            'equip', 'erase', 'erect', 'error', 'erupt', 'essay',
            'ether', 'ethic', 'ethos', 'evade', 'event', 'every',
            'evict', 'evoke', 'exact', 'exalt', 'exams', 'excel',
            'exert', 'exile', 'exist', 'expel', 'extra', 'exude',
            'exult', 'fable', 'faced', 'facer', 'faces', 'facet',
            'facts', 'faded', 'fades', 'fails', 'faint', 'fairs',
            'fairy', 'faith', 'falls', 'false', 'fames', 'fancy',
            'fangs', 'farms', 'fatal', 'fated', 'fates', 'fatty',
            'fault', 'fauna', 'favor', 'faxed', 'faxes', 'fazed',
            'fears', 'feast', 'feats', 'feeds', 'feels', 'fence',
            'ferns', 'ferry', 'fetal', 'fetch', 'fetid', 'fever',
            'fewer', 'fiber', 'field', 'fiend', 'fiery', 'fifes',
            'fifth', 'fifty', 'fight', 'files', 'fills', 'films',
            'filth', 'final', 'finch', 'finds', 'fined', 'finer',
            'fines', 'finny', 'fires', 'firms', 'first', 'fishy',
            'fists', 'fixed', 'fixer', 'fixes', 'fizzy', 'fjord',
            'flack', 'flags', 'flail', 'flair', 'flake', 'flaky',
            'flame', 'flank', 'flaps', 'flare', 'flash', 'flask',
            'flats', 'flaws', 'fleas', 'fleck', 'flees', 'fleet',
            'flesh', 'flick', 'flier', 'flies', 'fling', 'flint',
            'flips', 'flirt', 'float', 'flock', 'flood', 'floor',
            'flops', 'flora', 'flour', 'flout', 'flows', 'fluid',
            'fluke', 'flung', 'flush', 'flute', 'foamy', 'focal',
            'focus', 'foggy', 'foils', 'folds', 'folks', 'folly',
            'fonts', 'foods', 'fools', 'foots', 'foray', 'force',
            'forge', 'forgo', 'forks', 'forms', 'forte', 'forth',
            'forty', 'forum', 'foyer', 'frail', 'frame', 'frank',
            'fraud', 'freak', 'freer', 'frees', 'fresh', 'friar',
            'fried', 'fries', 'frill', 'frisk', 'frizz', 'frock',
            'front', 'frost', 'froth', 'frown', 'froze', 'fruit',
            'fryer', 'fuels', 'fugue', 'fully', 'fumes', 'funds',
            'funky', 'funny', 'furor', 'furry', 'fused', 'fuses',
            'fussy', 'fuzzy', 'gains', 'gales', 'gamer', 'games',
            'gangs', 'gates', 'gauge', 'gaunt', 'gauze', 'gavel',
            'gawks', 'gears', 'geeks', 'genus', 'germs', 'giddy',
            'gifts', 'gigue', 'gills', 'girls', 'given', 'giver',
            'gives', 'gizmo', 'glade', 'glads', 'gland', 'glare',
            'glass', 'glaze', 'gleam', 'glean', 'glees', 'glens',
            'glide', 'glint', 'gloom', 'glory', 'gloss', 'glove',
            'glued', 'glues', 'gnarl', 'gnash', 'gnats', 'gnome',
            'goads', 'goals', 'goats', 'godly', 'going', 'golds',
            'golfs', 'goods', 'gooey', 'goofy', 'goons', 'goose',
            'gored', 'gores', 'gorge', 'gorse', 'gotta', 'gouge',
            'gourd', 'gowns', 'grabs', 'grace', 'grade', 'grads',
            'graft', 'grail', 'grain', 'grand', 'grant', 'grape',
            'graph', 'grasp', 'grass', 'grate', 'grave', 'gravy',
            'grays', 'graze', 'great', 'greed', 'greek', 'green',
            'greet', 'grids', 'grief', 'grill', 'grime', 'grimy',
            'grind', 'grins', 'gripe', 'grist', 'grits', 'groan',
            'groin', 'groom', 'grope', 'gross', 'group', 'grout',
            'grove', 'growl', 'grows', 'grown', 'grubs', 'gruff',
            'grunt', 'guard', 'guava', 'guess', 'guest', 'guide',
            'guild', 'guilt', 'guise', 'gulch', 'gulfs', 'gulls',
            'gulps', 'gummy', 'gumbo', 'gunky', 'gusts', 'gusty',
            'gypsy', 'habit', 'hacks', 'haiku', 'hails', 'hairs',
            'hairy', 'halts', 'halve', 'hands', 'handy', 'hangs',
            'happy', 'hardy', 'harem', 'hares', 'harks', 'harms',
            'harsh', 'haste', 'hasty', 'hated', 'hater', 'hates',
            'hauls', 'haunt', 'haven', 'havoc', 'hawks', 'hazel',
            'heads', 'heals', 'heaps', 'hears', 'heart', 'heath',
            'heats', 'heave', 'heavy', 'hedge', 'heeds', 'heels',
            'hefty', 'heirs', 'heist', 'helix', 'hello', 'helps',
            'hence', 'henna', 'herbs', 'herds', 'heron', 'heros',
            'hertz', 'hexed', 'hexes', 'hider', 'hides', 'hiked',
            'hiker', 'hikes', 'hills', 'hilly', 'hilts', 'hinds',
            'hinge', 'hints', 'hippo', 'hippy', 'hired', 'hires',
            'hitch', 'hives', 'hoard', 'hoary', 'hobby', 'hocks',
            'hoist', 'holds', 'holes', 'holly', 'holms', 'homed',
            'homer', 'homes', 'hones', 'honey', 'honks', 'honor',
            'hoods', 'hoofs', 'hooks', 'hoops', 'hoots', 'hoped',
            'hopes', 'hoppy', 'horde', 'horns', 'horny', 'horse',
            'hosed', 'hoses', 'hosts', 'hotel', 'hound', 'hours',
            'house', 'hovel', 'hover', 'howdy', 'howls', 'huffed',
            'huffs', 'huffy', 'huger', 'hulks', 'hulky', 'hulls',
            'human', 'humid', 'humor', 'humps', 'humus', 'hunch',
            'hunks', 'hunky', 'hunts', 'hurls', 'hurry', 'hurts',
            'husky', 'hutch', 'hyena', 'hymns', 'hypes', 'hyper',
            'icily', 'icing', 'icons', 'ideal', 'ideas', 'ident',
            'idyll', 'igloo', 'image', 'imbed', 'imbue', 'imply',
            'inane', 'inbox', 'incur', 'index', 'india', 'indie',
            'inept', 'inert', 'infer', 'infos', 'infra', 'ingle',
            'ingot', 'inlet', 'inner', 'input', 'inset', 'inter',
            'intro', 'inure', 'irate', 'irked', 'irony', 'islet',
            'issue', 'itchy', 'items', 'ivory', 'jacks', 'jaded',
            'jades', 'jails', 'jaunt', 'jawed', 'jeans', 'jeeps',
            'jeers', 'jello', 'jelly', 'jests', 'jetty', 'jewel',
            'jiffy', 'jihad', 'jilts', 'jinks', 'jives', 'jocks',
            'joeys', 'joins', 'joint', 'joist', 'joked', 'joker',
            'jokes', 'jolly', 'jolts', 'joule', 'joust', 'jowls',
            'joynt', 'judge', 'juice', 'juicy', 'jumbo', 'jumps',
            'jumpy', 'junco', 'junks', 'junky', 'juror', 'jutes',
            'kayak', 'keeps', 'kelps', 'kendo', 'kenos', 'kenya',
            'keyed', 'khaki', 'khans', 'kicks', 'kiddo', 'kiddy',
            'kills', 'kilns', 'kilos', 'kilts', 'kinds', 'kines',
            'kings', 'kinks', 'kinky', 'kinos', 'kiosk', 'kited',
            'kiter', 'kites', 'kithe', 'kitty', 'kiwis', 'knack',
            'knaps', 'knave', 'knead', 'kneed', 'kneel', 'knees',
            'knelt', 'knife', 'knish', 'knits', 'knobs', 'knock',
            'knoll', 'knops', 'knosp', 'knots', 'known', 'knows',
            'knurl', 'kudos', 'kyack', 'kyaks', 'kyats', 'label',
            'labor', 'laced', 'lacer', 'laces', 'lacks', 'laded',
            'laden', 'lades', 'ladle', 'lager', 'laics', 'laird',
            'lairs', 'lairy', 'laith', 'laked', 'laker', 'lakes',
            'lamed', 'lamen', 'lamer', 'lames', 'lamia', 'lammy',
            'lamps', 'lanai', 'lance', 'lands', 'lanky', 'lansa',
            'larch', 'lards', 'lardy', 'lares', 'large', 'largo',
            'larks', 'larky', 'larry', 'larva', 'larum', 'lases',
            'lasso', 'lassy', 'laste', 'lasts', 'latch', 'lated',
            'laten', 'later', 'lates', 'lathe', 'lathi', 'laths',
            'lathy', 'latic', 'latis', 'laton', 'laude', 'lauds',
            'laugh', 'laura', 'laure', 'laurs', 'laury', 'lause',
            'laved', 'laven', 'laver', 'laves', 'lavin', 'lavor',
            'lavis', 'lavos', 'lavra', 'lavvy', 'lawer', 'lawes',
            'lawly', 'lawna', 'lawne', 'lawny', 'lawry', 'lawsy',
            'laxed', 'laxen', 'laxer', 'laxes', 'laxly', 'laxon',
            'layed', 'layer', 'layin', 'lazar', 'lazed', 'lazes',
            'lazoy', 'leach', 'leads', 'leafy', 'leaks', 'leaky',
            'leans', 'leant', 'leaps', 'leapt', 'learn', 'lease',
            'leash', 'least', 'leave', 'ledge', 'leech', 'leeks',
            'leers', 'leeward', 'lefts', 'lefty', 'legal', 'legen',
            'leger', 'leges', 'leggy', 'legit', 'lemon', 'lemur',
            'lends', 'lenes', 'lengs', 'lenis', 'lens', 'lento',
            'leone', 'leper', 'lepta', 'lepus', 'leres', 'lerps',
            'leshy', 'leses', 'lesis', 'lesks', 'less', 'lessa',
            'lesses', 'lest', 'letgo', 'lethe', 'letla', 'letme',
            'letts', 'letup', 'leucine', 'leud', 'leucine', 'leuds',
            'levant', 'levee', 'level', 'lever', 'leves', 'levied',
            'levier', 'levies', 'levin', 'levins', 'levite', 'levity',
            'levogs', 'levs', 'levulose', 'levy', 'lewd', 'lewdly',
            'lewer', 'lewdest', 'lewises', 'lezes', 'lexeme', 'lexemes',
            'lexes', 'lexicon', 'lexis', 'ley', 'leys', 'liar',
            'liars', 'liber', 'libero', 'libers', 'libers', 'libra',
            'librae', 'libras', 'libre', 'libretto', 'libs', 'libyan',
            'lice', 'licence', 'license', 'licences', 'licenses', 'lich',
            'lichen', 'lichee', 'lichens', 'liches', 'lichey', 'lichis',
            'lichs', 'licit', 'licitly', 'lick', 'licked', 'licker',
            'lickers', 'licking', 'lickings', 'licks', 'licorish', 'lictor',
            'lictors', 'lid', 'lidded', 'lidding', 'lidless', 'lidos',
            'lids', 'lie', 'lied', 'lieder', 'lieder', 'lief',
            'liefer', 'liefest', 'liefly', 'liege', 'lieges', 'liegeman',
            'liegerent', 'lieger', 'liegers', 'liegess', 'lien', 'liens',
            'lienal', 'lieneries', 'lienery', 'liene', 'lienes', 'lienitis',
            'lienly', 'lieno', 'lienography', 'lienologic', 'lienological', 'lienologies',
            'lienology', 'lienomotor', 'lienotoxin', 'liens', 'lient', 'lienteric',
            'lientery', 'lieny', 'liepoa', 'lier', 'lierne', 'liernes',
            'liers', 'lies', 'lieu', 'lieus', 'life', 'lifebelt',
            'lifeblood', 'lifeboat', 'lifeboats', 'lifebuoy', 'lifeguard', 'lifeguards',
            'lifeful', 'lifeguardless', 'lifeguardship', 'lifehood', 'lifeholds', 'lifehold',
            'lifeholder', 'lifeholders', 'lifeholds', 'lifehood', 'lifehoods', 'lifein',
            'lifeless', 'lifelessly', 'lifelessness', 'lifelike', 'lifelikeliness', 'lifelikely',
            'lifeliness', 'lifeline', 'lifelines', 'lifelinker', 'lifelinking', 'lifelines',
            'lifeliness', 'lifelong', 'lifelongs', 'lifemanship', 'lifemen', 'lifemates',
            'lifemate', 'lifepath', 'lifepaths', 'lifepersons', 'lifepoint', 'lifepoints',
            'lifer', 'liferaft', 'liferafts', 'lifers', 'lifesaver', 'lifesavers',
            'lifesaving', 'lifesavings', 'lifeset', 'lifesets', 'lifeship', 'lifeships',
            'lifeshort', 'lifespan', 'lifespans', 'lifesping', 'lifespring', 'lifesprings',
            'lifeless', 'lifestart', 'lifestock', 'lifestocks', 'lifestyles', 'lifestyle',
            'lifestyles', 'lifesum', 'lifesums', 'lifesustaining', 'lifesustainer', 'lifesustainers',
            'lifetable', 'lifetables', 'lifetaker', 'lifetakers', 'lifetaking', 'lifetakings',
            'lifetales', 'lifetal', 'lifeteacher', 'lifeteachers', 'lifeteachings', 'lifetime',
            'lifetimelike', 'lifetimes', 'lifetimism', 'lifetimist', 'lifetimists', 'lifetimize',
            'lifetimized', 'lifetimizing', 'lifetimization', 'lifetoime', 'lifetome', 'lifetouch',
            'lifetouching', 'lifetree', 'lifetrees', 'lifetruck', 'lifetrucks', 'lifetype',
            'lifetypes', 'lifetyping', 'lifetypings', 'lifeunsustaining', 'lifeway', 'lifeways',
            'lifeweary', 'lifeweary', 'lifeweartiness', 'lifeweary', 'lifewearsomeness', 'lifeweaving',
            'lifewebs', 'lifeweb', 'lifeweeks', 'lifeweek', 'lifewell', 'lifewells',
            'lifework', 'lifeworking', 'lifeworkings', 'lifeworks', 'lifeworlds', 'lifeworld',
            'lifeworthy', 'lifeworshiper', 'lifeworthier', 'lifeworthiest', 'lifeworthily', 'lifeworthiness',
            'lifeworthy', 'lifewriting', 'lifewritings', 'lifezeit', 'lifezeits', 'liffey',
            'liffeyess', 'liffeys', 'lift', 'liftable', 'liftables', 'liftableness',
            'liftable', 'liftableness', 'liftably', 'liftablys', 'liftage', 'liftages',
            'liftback', 'liftbacks', 'lifted', 'lifter', 'lifters', 'liftgate',
            'liftgates', 'liftglass', 'liftglasses', 'lifting', 'liftingly', 'liftingness',
            'liftings', 'liftless', 'liftlessly', 'liftlessness', 'liftlessly', 'liftlessnesss',
            'liftlock', 'liftlocks', 'liftoff', 'liftoffs', 'lifts', 'liftway',
            'liftways', 'lifty', 'lig', 'ligamen', 'ligamens', 'ligament',
            'ligamental', 'ligaments', 'ligamentous', 'ligand', 'ligands', 'ligand',
            'ligans', 'ligan', 'ligase', 'ligases', 'ligases', 'ligates',
            'ligating', 'ligation', 'ligational', 'ligations', 'ligating', 'ligati',
            'ligatie', 'ligating', 'ligating', 'ligating', 'ligating', 'ligating',
            'ligatures', 'ligature', 'ligatureless', 'ligatures', 'ligatures', 'ligation',
        }

        if name in words:
            reasons.append('word')

        # Fun patterns/misspellings
        fun_patterns = [
            'bussy', 'catty', 'ditzy', 'dizzy', 'fatty', 'gassy',
            'giddy', 'goofy', 'gotta', 'handy', 'happy', 'hippy',
            'jazzy', 'jolly', 'kinda', 'kitty', 'loopy', 'messy',
            'missy', 'mopey', 'moody', 'nasty', 'pansy', 'perky',
            'picky', 'pithy', 'potty', 'puppy', 'pussy', 'putty',
            'sassy', 'silly', 'sissy', 'soggy', 'sorry', 'spicy',
            'wimpy', 'zippy', 'buddy', 'curry', 'daddy', 'dabby',
            'daffy', 'daily', 'dairy', 'dandy', 'dilly', 'dizzy',
            'dotty', 'droll', 'dummy', 'dumpy', 'durny', 'duddy',
            'fluky', 'foamy', 'foggy', 'folky', 'folly', 'forky',
            'forty', 'fully', 'furry', 'fuzzy', 'gabby', 'gaily',
            'gammy', 'ganny', 'gaspy', 'giddy', 'girly', 'glazy',
            'godly', 'golly', 'gooey', 'goony', 'gormy', 'gowny',
            'grady', 'gravy', 'grimy', 'griny', 'gropy', 'gummy',
            'gunky', 'gusty', 'gypsy', 'haggy', 'hairy', 'hammy',
            'hanky', 'hardy', 'harky', 'harpy', 'harry', 'hasty',
            'hatty', 'hauby', 'haunt', 'hawky', 'hazel', 'heady',
            'healy', 'heary', 'hearty', 'hefty', 'heiny', 'henry',
            'herby', 'herky', 'hiffy', 'hippy', 'hoagy', 'hoaky',
            'hoary', 'hobly', 'hodgy', 'hokey', 'holly', 'homey',
            'honey', 'honky', 'hooby', 'hooey', 'hooky', 'hooly',
            'hooty', 'hoppy', 'horny', 'horsy', 'hotly', 'hotty',
            'houby', 'houdi', 'huffy', 'hulky', 'humby', 'humid',
            'humpy', 'hunky', 'hunny', 'hurby', 'hurky', 'hurry',
            'hurty', 'husky', 'iamby', 'icily', 'ickey', 'idaly',
            'idily', 'igaly', 'igley', 'igloo', 'ihavy', 'iholy',
            'ikily', 'ikily', 'imapy', 'imlay', 'impay', 'imply',
            'inlay', 'inlay', 'inlay', 'ipily', 'ipily', 'iraly',
            'irily', 'isaly', 'isily', 'itily', 'iully', 'ivaly',
            'ivily', 'ivory', 'jabby', 'jacky', 'jaggy', 'jakey',
            'jamby', 'jammy', 'janky', 'janty', 'jarby', 'jarky',
            'jarvy', 'jasty', 'jaunt', 'jauny', 'jaury', 'jaury',
            'jaury', 'jausy', 'javay', 'javy', 'jawby', 'jawky',
            'jawny', 'jawsy', 'jawty', 'jazzy', 'jelly', 'jenny',
            'jeeny', 'jeery', 'jeery', 'jeery', 'jeety', 'jelly',
            'jelon', 'jelty', 'jemly', 'jerby', 'jerky', 'jergy',
            'jerny', 'jerry', 'jersy', 'jersy', 'jersy', 'jessy',
            'jesty', 'jetly', 'jetty', 'jewby', 'jewel', 'jewsy',
            'jiffy', 'jilay', 'jiley', 'jilly', 'jimby', 'jimmy',
            'jimpy', 'jinal', 'jinky', 'jinny', 'jinsy', 'jirly',
            'jirny', 'jirsy', 'jisly', 'jispy', 'jissy', 'jitly',
            'jitny', 'jitsy', 'jitty', 'joaly', 'joary', 'joaty',
            'joazy', 'jobby', 'jobly', 'joby', 'jocy', 'jodly',
            'joely', 'joemy', 'joeny', 'joery', 'joesy', 'joety',
            'joey', 'joffy', 'joily', 'jointy', 'joiry', 'joisy',
            'jojoy', 'jojly', 'jokey', 'joksy', 'joky', 'jolby',
            'jolly', 'jolny', 'jolsy', 'jolty', 'jomby', 'jomly',
            'jomny', 'jonby', 'jonky', 'jonny', 'jonsy', 'jonty',
            'joody', 'joory', 'joory', 'joosy', 'jooty', 'joozy',
            'joply', 'jopsy', 'jopty', 'joqly', 'joqsy', 'jorby',
            'jorky', 'jorny', 'jorsy', 'jorty', 'joshy', 'jossy',
            'josty', 'josy', 'jotby', 'jotly', 'jotny', 'jotsy',
            'jotty', 'jouby', 'jouly', 'jousy', 'jousy', 'jouty',
            'jouzy', 'jovey', 'jovly', 'jovny', 'jovsy', 'jovty',
            'jovvy', 'jowby', 'jowey', 'jowky', 'jowly', 'jowny',
            'jowsy', 'jowty', 'joxey', 'joxsy', 'joyed', 'joyey',
            'joyful', 'joyey', 'joyle', 'joyly', 'joyney', 'joyney',
            'joysey', 'joysey', 'joyssy', 'joyssy', 'joysy', 'joysty',
            'joytes', 'jozey', 'jozsy', 'jubby', 'jubcy', 'jubdy',
            'jubey', 'jubey', 'jubey', 'jubey', 'jubey', 'jubey',
            'jubey', 'jubey', 'jubey', 'jubey', 'jubey', 'jubey',
            'jubey', 'jubey', 'jubey', 'jubey', 'jubey', 'jubey',
        }

        if name in fun_patterns:
            reasons.append('fun_pattern')

        # Check for number patterns
        if any(c.isdigit() for c in name):
            reasons.append('has_numbers')

            # Special pattern: 0x0 style
            if '0' in name and 'x' in name:
                reasons.append('hex_like')

        return len(reasons) > 0, reasons

    def scrape(self):
        """Main scraping loop."""
        print("\n" + "="*60)
        print("Starting domain scrape")
        print("="*60)

        # Try without strict filters first (sometimes they filter everything)
        filter_sets = [
            {
                'name': 'without has_number/available filters',
                'filters': {
                    'has_number': '',
                    'available': '',
                    'has_hyphen': '0',
                }
            },
            {
                'name': 'basic (just price filters)',
                'filters': {
                    'has_number': '',
                    'available': '',
                    'has_hyphen': '',
                    'price_renewal': '',
                }
            },
            {
                'name': 'with has_number only',
                'filters': {
                    'has_number': '1',
                    'available': '',
                    'has_hyphen': '0',
                }
            },
        ]

        for filter_config in filter_sets:
            print(f"\n--- Trying: {filter_config['name']} ---")

            for start in range(0, 5000, 100):
                print(f"Offset {start:5d}...", end=' ')

                batch, total = self.fetch_batch(start, 100, **filter_config['filters'])

                if not batch:
                    print("no data")
                    break

                print(f"{len(batch)} results")

                for item in batch:
                    parsed = self.parse_domain_info(item)
                    if parsed:
                        self.all_domains.append(parsed)

                time.sleep(0.2)

                if len(self.all_domains) > 100:
                    break

            if len(self.all_domains) > 100:
                break

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
        print(f"  - domains_found.json ({len(interesting)} entries)")
        print(f"  - domains_found.csv ({len(interesting)} entries)")

        return interesting


if __name__ == '__main__':
    scraper = DomainScraper()

    if scraper.setup_session():
        scraper.scrape()
        scraper.save_results()
    else:
        print("Failed to setup session")
        exit(1)
