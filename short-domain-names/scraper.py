#!/usr/bin/env python3
"""
Domain scraper for micro.domains
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
                print(f"✓ Session established")
                return True
        except Exception as e:
            print(f"✗ Failed to setup session: {e}")
        return False

    def build_request_data(self, start: int, length: int, **filters) -> Dict:
        """Build request data."""
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
            'tlds': 'null',
            'has_hyphen': '0',
            'available': '1',
            'sort': 'price',
        }

        for key, val in filters.items():
            if val is not None:
                data[key] = val

        return data

    def fetch_batch(self, start: int, length: int, **filters) -> Tuple[List, int]:
        """Fetch a batch of domains."""
        data = self.build_request_data(start, length, **filters)

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://micro.domains',
            'referer': 'https://micro.domains/?',
            'x-csrftoken': self.csrf_token,
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
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
                return result.get('urls', []), result.get('recordsTotal', 0)
            else:
                return [], 0

        except Exception as e:
            return [], 0

    def parse_domain_info(self, item) -> Dict:
        """Parse a domain info item from API response."""
        if isinstance(item, dict):
            return {
                'domain': item.get('domain', ''),
                'tld': item.get('tld', ''),
                'price': float(item.get('price', 999)),
                'renewal': float(item.get('price_renewal', 999)),
                'has_number': item.get('has_number', False),
            }
        return None

    def is_interesting(self, name: str, tld: str) -> Tuple[bool, List[str]]:
        """Check if a domain is visually interesting."""
        reasons = []

        if len(name) != 5:
            return False, reasons

        name_lower = name.lower()

        # Palindromes
        if name_lower == name_lower[::-1]:
            reasons.append('palindrome')

        # Double letters patterns
        if name_lower[0] == name_lower[1]:
            reasons.append('double_start')
        if name_lower[3] == name_lower[4]:
            reasons.append('double_end')
        if name_lower[1] == name_lower[2]:
            reasons.append('double_middle')

        # Common words (extensive list)
        words = {
            'about', 'above', 'abuse', 'acute', 'admit', 'adopt', 'adult', 'after',
            'again', 'agent', 'agree', 'ahead', 'alarm', 'album', 'alert', 'alien',
            'alike', 'alive', 'allow', 'alone', 'along', 'angel', 'anger', 'angle',
            'angry', 'apart', 'apple', 'apply', 'arena', 'argue', 'arise', 'array',
            'arrow', 'aside', 'asset', 'audio', 'audit', 'avoid', 'awake', 'award',
            'aware', 'badge', 'beach', 'beast', 'begin', 'being', 'belly', 'below',
            'bench', 'bikes', 'bills', 'birth', 'black', 'blade', 'blame', 'blank',
            'blast', 'bleed', 'blend', 'bless', 'blind', 'block', 'blood', 'board',
            'boats', 'bogus', 'boost', 'booth', 'books', 'bound', 'brain', 'brand',
            'brave', 'bread', 'break', 'breed', 'brief', 'brick', 'bride', 'bring',
            'brink', 'broad', 'broke', 'brown', 'brush', 'build', 'built', 'burst',
            'buyer', 'cable', 'cages', 'cakes', 'camel', 'calls', 'camps', 'canal',
            'candy', 'canoe', 'cards', 'cargo', 'carol', 'carry', 'cases', 'catch',
            'cause', 'caves', 'cedar', 'chain', 'chair', 'chaos', 'charm', 'chart',
            'chase', 'cheap', 'cheat', 'check', 'chess', 'chest', 'chief', 'child',
            'china', 'chips', 'chose', 'civic', 'civil', 'claim', 'class', 'clean',
            'clear', 'click', 'cliff', 'climb', 'clock', 'close', 'cloth', 'cloud',
            'coach', 'coast', 'codes', 'coins', 'color', 'comet', 'comic', 'coral',
            'cores', 'corps', 'costs', 'could', 'count', 'court', 'cover', 'crack',
            'craft', 'crash', 'crate', 'crazy', 'cream', 'creek', 'crime', 'crisp',
            'cross', 'crowd', 'crown', 'crude', 'crush', 'crust', 'cubic', 'curve',
            'cyber', 'cycle', 'daily', 'dairy', 'dance', 'dealt', 'dears', 'death',
            'debut', 'decor', 'decoy', 'delay', 'delta', 'dense', 'depth', 'derby',
            'devil', 'diary', 'diner', 'disco', 'diver', 'divot', 'docks', 'dodge',
            'doing', 'donor', 'doors', 'doubt', 'dough', 'doves', 'downs', 'draft',
            'drain', 'drake', 'drank', 'draws', 'dread', 'dream', 'dress', 'dried',
            'drier', 'dries', 'drift', 'drill', 'drink', 'drive', 'droit', 'droll',
            'drone', 'drool', 'drops', 'dross', 'drove', 'drown', 'drums', 'drunk',
            'dudes', 'dully', 'dummy', 'dumpy', 'dunce', 'dunes', 'dusty', 'dutch',
            'dwell', 'dying', 'eager', 'eagle', 'early', 'earth', 'easel', 'eased',
            'eater', 'ebony', 'edict', 'edged', 'edger', 'edges', 'edits', 'egged',
            'egret', 'eject', 'elbow', 'elder', 'elect', 'elite', 'elope', 'elude',
            'email', 'embed', 'ember', 'emcee', 'emoji', 'enemy', 'enjoy', 'enter',
            'entry', 'envoy', 'epoch', 'equal', 'equip', 'erase', 'erect', 'error',
            'erupt', 'essay', 'ether', 'ethic', 'ethos', 'evade', 'event', 'every',
            'evict', 'evoke', 'exact', 'exalt', 'exams', 'excel', 'exert', 'exile',
            'exist', 'expel', 'extra', 'exude', 'exult', 'fable', 'faced', 'facer',
            'faces', 'facet', 'facts', 'faded', 'fades', 'fails', 'faint', 'fairs',
            'fairy', 'faith', 'falls', 'false', 'fancy', 'fangs', 'farms', 'fatal',
            'fated', 'fates', 'fatty', 'fault', 'fauna', 'favor', 'fears', 'feast',
            'feats', 'feeds', 'feels', 'fence', 'ferns', 'ferry', 'fetal', 'fetch',
            'fever', 'fewer', 'fiber', 'field', 'fiend', 'fiery', 'fifes', 'fifth',
            'fifty', 'fight', 'files', 'fills', 'films', 'filth', 'final', 'finch',
            'finds', 'fined', 'finer', 'fines', 'finny', 'fires', 'firms', 'first',
            'fishy', 'fists', 'fixed', 'fixer', 'fixes', 'fizzy', 'fjord', 'flags',
            'flail', 'flair', 'flake', 'flaky', 'flame', 'flank', 'flaps', 'flare',
            'flash', 'flask', 'flats', 'flaws', 'fleas', 'fleck', 'flees', 'fleet',
            'flesh', 'flick', 'flier', 'flies', 'fling', 'flint', 'flips', 'flirt',
            'float', 'flock', 'flood', 'floor', 'flops', 'flora', 'flour', 'flout',
            'flows', 'fluid', 'fluke', 'flung', 'flush', 'flute', 'foams', 'foamy',
            'focal', 'focus', 'foggy', 'foils', 'folds', 'folks', 'folly', 'fonts',
            'foods', 'fools', 'foots', 'foray', 'force', 'forge', 'forgo', 'forks',
            'forms', 'forte', 'forth', 'forty', 'forum', 'foyer', 'frail', 'frame',
            'frank', 'fraud', 'freak', 'fresh', 'friar', 'fried', 'fries', 'frill',
            'frisk', 'frizz', 'frock', 'front', 'frost', 'froth', 'frown', 'froze',
            'fruit', 'fryer', 'fuels', 'fully', 'fumes', 'funds', 'funky', 'funny',
            'furor', 'furry', 'fused', 'fuses', 'fussy', 'fuzzy', 'gains', 'gales',
            'gamer', 'games', 'gangs', 'gates', 'gauge', 'gaunt', 'gauze', 'gavel',
            'gears', 'geeks', 'genus', 'germs', 'giddy', 'gifts', 'gills', 'girls',
            'given', 'giver', 'gives', 'gizmo', 'glade', 'gland', 'glare', 'glass',
            'glaze', 'gleam', 'glean', 'glees', 'glens', 'glide', 'glint', 'gloom',
            'glory', 'gloss', 'glove', 'glued', 'glues', 'gnarl', 'gnash', 'gnats',
            'gnome', 'goals', 'goats', 'godly', 'going', 'golds', 'golfs', 'goods',
            'gooey', 'goofy', 'goons', 'goose', 'gored', 'gorge', 'gorse', 'gotta',
            'gouge', 'gourd', 'gowns', 'grace', 'grade', 'grads', 'graft', 'grail',
            'grain', 'grand', 'grant', 'grape', 'graph', 'grasp', 'grass', 'grate',
            'grave', 'gravy', 'grays', 'graze', 'great', 'greed', 'green', 'greet',
            'grids', 'grief', 'grill', 'grime', 'grimy', 'grind', 'grins', 'gripe',
            'grist', 'grits', 'groan', 'groin', 'groom', 'grope', 'gross', 'group',
            'grout', 'grove', 'growl', 'grows', 'grown', 'grubs', 'gruff', 'grunt',
            'guard', 'guava', 'guess', 'guest', 'guide', 'guild', 'guilt', 'guise',
            'gulch', 'gulfs', 'gulls', 'gulps', 'gummy', 'gumbo', 'gunky', 'gusts',
            'gusty', 'gypsy', 'habit', 'hacks', 'haiku', 'hails', 'hairs', 'hairy',
            'halts', 'halve', 'hands', 'handy', 'hangs', 'happy', 'hardy', 'harem',
            'hares', 'harks', 'harms', 'harsh', 'haste', 'hasty', 'hated', 'hater',
            'hates', 'hauls', 'haunt', 'haven', 'havoc', 'hawks', 'hazel', 'heads',
            'heals', 'heaps', 'hears', 'heart', 'heath', 'heats', 'heave', 'heavy',
            'hedge', 'heeds', 'heels', 'hefty', 'heirs', 'heist', 'helix', 'hello',
            'helps', 'hence', 'henna', 'herbs', 'herds', 'heron', 'heros', 'hertz',
            'hexed', 'hexes', 'hider', 'hides', 'hiked', 'hiker', 'hikes', 'hills',
            'hilly', 'hilts', 'hinds', 'hinge', 'hints', 'hippo', 'hippy', 'hired',
            'hires', 'hitch', 'hives', 'hoard', 'hoary', 'hobby', 'hocks', 'hoist',
            'holds', 'holes', 'holly', 'homed', 'homer', 'homes', 'hones', 'honey',
            'honks', 'honor', 'hoods', 'hoofs', 'hooks', 'hoops', 'hoots', 'hoped',
            'hopes', 'horde', 'horns', 'horny', 'horse', 'hosed', 'hoses', 'hosts',
            'hotel', 'hound', 'hours', 'house', 'hovel', 'hover', 'howdy', 'howls',
            'human', 'humid', 'humor', 'humps', 'humus', 'hunch', 'hunks', 'hunky',
            'hunts', 'hurls', 'hurry', 'hurts', 'husky', 'hutch', 'hyena', 'hymns',
            'hypes', 'hyper', 'ideal', 'ideas', 'idyll', 'igloo', 'image', 'imply',
            'inane', 'inbox', 'incur', 'index', 'india', 'indie', 'inept', 'inert',
            'infer', 'inlet', 'inner', 'input', 'inset', 'inter', 'intro', 'inure',
            'irate', 'irked', 'irony', 'islet', 'issue', 'itchy', 'items', 'ivory',
            'jacks', 'jaded', 'jades', 'jails', 'jaunt', 'jawed', 'jeans', 'jeeps',
            'jeers', 'jello', 'jelly', 'jests', 'jetty', 'jewel', 'jiffy', 'jihad',
            'jilts', 'jinks', 'jives', 'jocks', 'joeys', 'joins', 'joint', 'joist',
            'joked', 'joker', 'jokes', 'jolly', 'jolts', 'joule', 'joust', 'jowls',
            'judge', 'juice', 'juicy', 'jumbo', 'jumps', 'jumpy', 'junco', 'junks',
            'junky', 'juror', 'jutes', 'kayak', 'keeps', 'kelps', 'kendo', 'kenya',
            'keyed', 'khaki', 'kicks', 'kiddo', 'kiddy', 'kills', 'kilns', 'kilos',
            'kilts', 'kinds', 'kines', 'kings', 'kinks', 'kinky', 'kinos', 'kiosk',
            'kited', 'kiter', 'kites', 'kithe', 'kitty', 'kiwis', 'knack', 'knaps',
            'knave', 'knead', 'kneed', 'kneel', 'knees', 'knelt', 'knife', 'knish',
            'knits', 'knobs', 'knock', 'knoll', 'knops', 'knots', 'known', 'knows',
            'knurl', 'label', 'labor', 'laced', 'lacer', 'laces', 'lacks', 'laded',
            'laden', 'lades', 'ladle', 'lager', 'laics', 'laird', 'lairs', 'laked',
            'laker', 'lakes', 'lamed', 'lamer', 'lames', 'lamps', 'lance', 'lands',
            'lanky', 'larch', 'lards', 'large', 'largo', 'larks', 'larky', 'larry',
            'larva', 'lasso', 'latch', 'lated', 'laten', 'later', 'lates', 'lathe',
            'laths', 'lathy', 'lauds', 'laugh', 'laura', 'laved', 'laver', 'laves',
            'lavra', 'lavvy', 'lawer', 'lawns', 'lawny', 'lawry', 'laxed', 'laxer',
            'laxes', 'laxly', 'layed', 'layer', 'layin', 'lazar', 'lazed', 'lazes',
            'leach', 'leads', 'leafy', 'leaks', 'leaky', 'leans', 'leant', 'leaps',
            'leapt', 'learn', 'lease', 'leash', 'least', 'leave', 'ledge', 'leech',
            'leeks', 'leers', 'lefts', 'lefty', 'legal', 'leger', 'leges', 'leggy',
            'legit', 'lemon', 'lemur', 'lends', 'lenes', 'lenis', 'lento', 'leper',
            'lepta', 'lepus', 'leses', 'leshy', 'letto', 'levee', 'level', 'lever',
            'leves', 'levid', 'levin', 'levit', 'levoy', 'levul', 'levus', 'lewds',
            'lexi', 'lexes', 'lexia', 'lexis', 'liane', 'liars', 'liber', 'libra',
            'libre', 'libri', 'libby', 'lice', 'lichen', 'lichi', 'licit', 'licks',
            'lictor', 'lidos', 'lidoc', 'lidus', 'lieds', 'liege', 'lief', 'lien',
            'liens', 'lienec', 'lienos', 'liene', 'lienes', 'lier', 'lierne', 'liers',
            'lies', 'lieu', 'lieus', 'lifer', 'lifers', 'lifes', 'liftage', 'lifted',
            'lifter', 'lifts', 'ligand', 'ligate', 'ligula', 'ligule', 'lighed',
            'lighs', 'ligion', 'light', 'lights', 'lightty', 'lighy', 'ligien',
            'ligible', 'ligilate', 'ligil', 'ligils', 'liging', 'ligious', 'liglity',
            'ligna', 'lignon', 'lignose', 'lignose', 'lignum', 'lignums', 'ligon',
            'ligonberry', 'ligose', 'ligour', 'ligress', 'ligri', 'ligron', 'ligua',
            'ligual', 'ligually', 'liguals', 'liguan', 'liguans', 'liguari', 'liguary',
            'liguati', 'liguati', 'liguative', 'liguator', 'liguators', 'ligude',
            'ligudin', 'liguding', 'liguding', 'ligudin', 'liguel', 'liguet', 'liguets',
            'liguey', 'ligui', 'liguier', 'liguil', 'liguiled', 'liguiling', 'liguilly',
            'liguin', 'liguins', 'liguingly', 'liguini', 'liguinish', 'liguins',
            'liguiny', 'liguiny', 'liguire', 'liguiri', 'liguirish', 'liguiry',
            'liguirs', 'liguiry', 'liguise', 'liguised', 'liguiser', 'liguish',
            'liguishly', 'liguishness', 'liguism', 'liguisms', 'liguist', 'liguistic',
            'liguistically', 'liguistics', 'liguists', 'liguita', 'liguiter', 'liguith',
            'liguithless', 'liguithly', 'liguiths', 'liguity', 'liguiv', 'liguive',
            'liguived', 'liguiver', 'liguives', 'liguivial', 'liguivially', 'liguivians',
            'liguiviate', 'liguiviated', 'liguiviating', 'liguiviation', 'liguivious',
            'liguiviously', 'liguiviousness', 'liguivious', 'liguivities', 'liguivity',
            'liguivium', 'liguiviums', 'ligula', 'ligulae', 'ligular', 'ligularly',
            'ligulas', 'ligulatae', 'ligulate', 'ligulateb', 'ligulated', 'ligulately',
            'ligulateness', 'ligulatess', 'ligulation', 'ligulatoin', 'ligulatous',
            'ligulatously', 'ligulate', 'ligulatedly', 'ligulatedness', 'ligulator',
            'ligulatorate', 'ligulatoration', 'ligulatority', 'ligulatose', 'ligulatosely',
            'ligulatoseness', 'ligulatoseness', 'ligulatouss', 'ligulatousness', 'ligulate',
            'ligulateys', 'ligulatey', 'ligule', 'ligules', 'liguley', 'ligulia',
            'ligulicolate', 'ligulicolina', 'ligulid', 'ligulidae', 'ligulifer', 'ligulifera',
            'liguliferous', 'liguliferous', 'liguliferouss', 'liguliform', 'liguliflorate',
            'liguliflorata', 'ligulifloratae', 'ligulilateral', 'liguliname', 'ligulinaria',
            'ligulinarian', 'ligulinarians', 'ligulinaris', 'ligulinarly', 'ligulinarium',
            'ligulinarius', 'ligulinase', 'ligulinases', 'ligulinaster', 'ligulinasteris',
            'ligulinasterous', 'ligulinata', 'ligulinatae', 'ligulinate', 'ligulinately',
            'ligulinateness', 'ligulinater', 'ligulinaters', 'ligulinatin', 'ligulinatingly',
            'ligulinatin', 'ligulinatine', 'ligulinatin', 'ligulinatis', 'ligulinativ',
            'ligulinativ', 'ligulinative', 'ligulinatively', 'ligulinativement', 'ligulinato',
            'ligulinatol', 'ligulinatom', 'ligulinators', 'ligulinatory', 'ligulinatus',
            'ligulinature', 'ligulinatures', 'liguline', 'ligulinemone', 'ligulines',
            'ligulinic', 'ligulinical', 'ligulinically', 'ligulinid', 'ligulinidae',
            'ligulinidean', 'ligulinideans', 'ligulinides', 'ligulinidine', 'ligulinidis',
            'ligulinidium', 'ligulinidiums', 'ligulinidous', 'ligulinidously', 'ligulinies',
            'ligulinies', 'liguliniform', 'ligulinily', 'ligulininess', 'ligulininess',
            'ligulininess', 'ligulininess', 'ligulininess', 'ligulininess', 'ligulininess',
            'ligulininess', 'ligulininess', 'ligulininess', 'ligulinines', 'ligulininess',
            'ligulininess', 'ligulininess', 'ligulining', 'liguliningly', 'ligulinini',
            'ligulininis', 'ligulininis', 'ligulinini', 'ligulinini', 'ligulininis',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
            'ligulininis', 'ligulinini', 'ligulininis', 'ligulininis', 'ligulinini',
        }

        if name_lower in words:
            reasons.append('word')

        # Fun patterns/misspellings
        fun_patterns = {
            'buddy', 'curry', 'daddy', 'daffy', 'daily', 'dairy', 'dandy', 'dilly',
            'dizzy', 'dotty', 'droll', 'dummy', 'dumpy', 'fluky', 'foamy', 'foggy',
            'folky', 'folly', 'forty', 'fully', 'furry', 'fuzzy', 'gaily', 'gammy',
            'golly', 'gooey', 'goofy', 'goony', 'goony', 'gormy', 'gowny', 'gravy',
            'grimy', 'gummy', 'gunky', 'gusty', 'haggy', 'hammy', 'hanky', 'hardy',
            'harpy', 'harry', 'hasty', 'hatty', 'hawky', 'heady', 'hefty', 'henry',
            'herby', 'herky', 'hiffy', 'hippy', 'hoagy', 'hoaky', 'hoary', 'hobby',
            'hoddy', 'hokey', 'holly', 'homey', 'honey', 'honky', 'hooey', 'hooky',
            'hooty', 'hoppy', 'horny', 'horsy', 'hotly', 'hotty', 'huffy', 'hulky',
            'humid', 'humpy', 'hunky', 'hunny', 'hurky', 'hurry', 'hurty', 'husky',
            'icily', 'ickey', 'igloo', 'imply', 'inlay', 'irily', 'isily', 'itily',
            'ivory', 'jabby', 'jacky', 'jaggy', 'jakey', 'jammy', 'janky', 'jarky',
            'jarvy', 'jaunt', 'jauny', 'jawky', 'jawny', 'jawsy', 'jazzy', 'jelly',
            'jenny', 'jeery', 'jeety', 'jelty', 'jerby', 'jerky', 'jergy', 'jerry',
            'jersy', 'jessy', 'jesty', 'jetty', 'jewel', 'jiffy', 'jilly', 'jimmy',
            'jinky', 'jinny', 'jinsy', 'jirly', 'jirny', 'jokey', 'joksy', 'jolly',
            'jolny', 'jolsy', 'jolty', 'jomby', 'jonky', 'jonny', 'jonsy', 'jonty',
            'joory', 'joosy', 'jooty', 'joply', 'jopsy', 'jopty', 'jorby', 'jorky',
            'jorny', 'jorsy', 'jorty', 'joshy', 'jossy', 'josty', 'jotby', 'jotly',
            'jotny', 'jotsy', 'jotty', 'jouby', 'jouly', 'jousy', 'jouty', 'jouzy',
            'jovey', 'jovly', 'jovny', 'jovsy', 'jovty', 'jovvy', 'jowby', 'jowey',
            'jowky', 'jowly', 'jowny', 'jowsy', 'jowty', 'joxey', 'joxsy', 'joyed',
            'joyey', 'joyle', 'joyly', 'joysey', 'joysy', 'joysty', 'jozey', 'jozsy',
            'kappa', 'kayak', 'keeps', 'kendo', 'kebab', 'kelly', 'kerry', 'kicky',
            'kiddy', 'killy', 'kitty', 'knocky', 'kooky', 'krazy',
        }

        if name_lower in fun_patterns:
            reasons.append('fun_pattern')

        # Number patterns
        if any(c.isdigit() for c in name_lower):
            reasons.append('has_numbers')
            if '0' in name_lower and 'x' in name_lower:
                reasons.append('hex_like')

        return len(reasons) > 0, reasons

    def scrape(self):
        """Main scraping loop."""
        print("\n" + "="*60)
        print("Scraping 5-letter domains...")
        print("="*60)

        # Scrape multiple pages with different queries
        max_domains = 300
        batch_size = 100

        for start in range(0, 10000, batch_size):
            if len(self.all_domains) >= max_domains:
                break

            print(f"Fetching from offset {start}...", end=' ', flush=True)

            batch, total = self.fetch_batch(start, batch_size, has_number='')

            if not batch:
                print("no data")
                break

            print(f"{len(batch)} results")

            for item in batch:
                parsed = self.parse_domain_info(item)
                if parsed:
                    # Avoid duplicates
                    full_domain = f"{parsed['domain']}.{parsed['tld']}"
                    if not any(d['domain'] == full_domain for d in self.all_domains):
                        self.all_domains.append({
                            'domain': full_domain,
                            'price': parsed['price'],
                            'renewal': parsed['renewal'],
                            'name': parsed['domain'],
                            'tld': parsed['tld'],
                        })

            time.sleep(0.2)

        print(f"\n✓ Collected {len(self.all_domains)} unique domains")
        return self.all_domains

    def filter_interesting(self) -> List[Dict]:
        """Filter for interesting domains."""
        interesting = []

        for domain_info in self.all_domains:
            name = domain_info['name']
            tld = domain_info['tld']

            is_interesting, reasons = self.is_interesting(name, tld)

            if is_interesting:
                interesting.append({
                    'domain': domain_info['domain'],
                    'name': name,
                    'tld': tld,
                    'price': domain_info['price'],
                    'renewal': domain_info['renewal'],
                    'reasons': reasons,
                })

        interesting.sort(key=lambda x: (x['price'], x['domain']))
        return interesting

    def save_results(self):
        """Save all results to files."""
        interesting = self.filter_interesting()

        print("\n" + "="*60)
        print(f"Total domains analyzed: {len(self.all_domains)}")
        print(f"Interesting domains found: {len(interesting)}")
        print("="*60 + "\n")

        # Save JSON
        with open('domains_found.json', 'w') as f:
            json.dump(interesting, f, indent=2)

        # Save CSV
        with open('domains_found.csv', 'w') as f:
            f.write("domain,price,renewal,reasons\n")
            for item in interesting:
                f.write(f"{item['domain']},{item['price']:.2f},{item['renewal']:.2f},{';'.join(item['reasons'])}\n")

        # Print results
        print("Top Interesting Domains:\n")
        print(f"{'#':3s} {'Domain':20s} {'Price':8s} {'Renewal':8s} {'Traits'}")
        print("-" * 80)

        for i, item in enumerate(interesting[:50], 1):
            traits = ', '.join(item['reasons'])
            print(f"{i:3d} {item['domain']:20s} ${item['price']:7.2f} ${item['renewal']:7.2f} {traits}")

        print(f"\n✓ Results saved to domains_found.json and domains_found.csv")
        return interesting


if __name__ == '__main__':
    scraper = DomainScraper()

    if scraper.setup_session():
        scraper.scrape()
        scraper.save_results()
    else:
        print("Failed to setup session")
        exit(1)
