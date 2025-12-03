import json
import re
from collections import Counter

# Common 5-letter words
words = {
    'about', 'above', 'abuse', 'acute', 'admit', 'adopt', 'adult', 'after',
    'again', 'agent', 'agree', 'ahead', 'alarm', 'album', 'alert', 'alien',
    'alike', 'alive', 'allow', 'alone', 'along', 'angel', 'anger', 'angle',
    'angry', 'apart', 'apple', 'apply', 'arena', 'argue', 'arise', 'array',
    'arrow', 'aside', 'asset', 'audio', 'audit', 'avoid', 'awake', 'award',
    'aware', 'badge', 'beach', 'beast', 'began', 'begin', 'being', 'belly',
    'below', 'bench', 'bikes', 'bills', 'birth', 'black', 'blade', 'blame',
    'blank', 'blast', 'bleed', 'blend', 'bless', 'blind', 'block', 'blood',
    'board', 'boats', 'bogus', 'boost', 'booth', 'books', 'bound', 'brain',
    'brand', 'brave', 'bread', 'break', 'breed', 'brief', 'brick', 'bride',
    'bring', 'brink', 'broad', 'broke', 'brown', 'brush', 'build', 'built',
    'burst', 'buyer', 'cable', 'cages', 'cakes', 'camel', 'calls', 'camps',
    'canal', 'candy', 'canoe', 'cards', 'cargo', 'carol', 'carry', 'cases',
    'catch', 'cause', 'caves', 'cedar', 'chain', 'chair', 'chaos', 'charm',
    'chart', 'chase', 'cheap', 'cheat', 'check', 'chess', 'chest', 'chief',
    'child', 'china', 'chips', 'chose', 'civic', 'civil', 'claim', 'class',
    'clean', 'clear', 'click', 'cliff', 'climb', 'clock', 'close', 'cloth',
    'cloud', 'coach', 'coast', 'codes', 'coins', 'color', 'comet', 'comic',
    'coral', 'cores', 'corps', 'costs', 'could', 'count', 'court', 'cover',
    'crack', 'craft', 'crash', 'crate', 'crazy', 'cream', 'creek', 'crime',
    'crisp', 'cross', 'crowd', 'crown', 'crude', 'crush', 'crust', 'cubic',
    'curve', 'cyber', 'cycle', 'daily', 'dairy', 'dance', 'dealt', 'dears',
    'death', 'debut', 'decor', 'decoy', 'delay', 'delta', 'dense', 'depth',
    'derby', 'devil', 'diary', 'diner', 'disco', 'diver', 'divot', 'docks',
    'dodge', 'doing', 'donor', 'doors', 'doubt', 'dough', 'doves', 'downs',
    'draft', 'drain', 'drake', 'drank', 'draws', 'dread', 'dream', 'dress',
    'dried', 'drier', 'dries', 'drift', 'drill', 'drink', 'drive', 'droit',
    'droll', 'drone', 'drool', 'drops', 'dross', 'drove', 'drown', 'drums',
    'drunk', 'dudes', 'dully', 'dummy', 'dumpy', 'dunce', 'dunes', 'dusty',
    'dutch', 'dwell', 'dying', 'eager', 'eagle', 'early', 'earth', 'easel',
    'eased', 'eater', 'ebony', 'edict', 'edged', 'edger', 'edges', 'edits',
    'egged', 'egret', 'eject', 'elbow', 'elder', 'elect', 'elite', 'elope',
    'elude', 'email', 'embed', 'ember', 'emcee', 'emoji', 'enemy', 'enjoy',
    'enter', 'entry', 'envoy', 'epoch', 'equal', 'equip', 'erase', 'erect',
    'error', 'erupt', 'essay', 'ether', 'ethic', 'ethos', 'evade', 'event',
    'every', 'evict', 'evoke', 'exact', 'exalt', 'exams', 'excel', 'exert',
    'exile', 'exist', 'expel', 'extra', 'exude', 'exult', 'fable', 'faced',
    'facer', 'faces', 'facet', 'facts', 'faded', 'fades', 'fails', 'faint',
    'fairs', 'fairy', 'faith', 'falls', 'false', 'fancy', 'fangs', 'farms',
    'fatal', 'fated', 'fates', 'fatty', 'fault', 'fauna', 'favor', 'fears',
    'feast', 'feats', 'feeds', 'feels', 'fence', 'ferns', 'ferry', 'fetal',
    'fetch', 'fever', 'fewer', 'fiber', 'field', 'fiend', 'fiery', 'fifes',
    'fifth', 'fifty', 'fight', 'files', 'fills', 'films', 'filth', 'final',
    'finch', 'finds', 'fined', 'finer', 'fines', 'finny', 'fires', 'firms',
    'first', 'fishy', 'fists', 'fixed', 'fixer', 'fixes', 'fizzy', 'fjord',
    'flags', 'flail', 'flair', 'flake', 'flaky', 'flame', 'flank', 'flaps',
    'flare', 'flash', 'flask', 'flats', 'flaws', 'fleas', 'fleck', 'flees',
    'fleet', 'flesh', 'flick', 'flier', 'flies', 'fling', 'flint', 'flips',
    'flirt', 'float', 'flock', 'flood', 'floor', 'flops', 'flora', 'flour',
    'flout', 'flows', 'fluid', 'fluke', 'flung', 'flush', 'flute', 'foams',
    'foamy', 'focal', 'focus', 'foggy', 'foils', 'folds', 'folks', 'folly',
    'fonts', 'foods', 'fools', 'foots', 'foray', 'force', 'forge', 'forgo',
    'forks', 'forms', 'forte', 'forth', 'forty', 'forum', 'foyer', 'frail',
    'frame', 'frank', 'fraud', 'freak', 'fresh', 'friar', 'fried', 'fries',
    'frill', 'frisk', 'frizz', 'frock', 'front', 'frost', 'froth', 'frown',
    'froze', 'fruit', 'fryer', 'fuels', 'fully', 'fumes', 'funds', 'funky',
    'funny', 'furor', 'furry', 'fused', 'fuses', 'fussy', 'fuzzy', 'gains',
    'gales', 'gamer', 'games', 'gangs', 'gates', 'gauge', 'gaunt', 'gauze',
    'gavel', 'gears', 'geeks', 'genus', 'germs', 'giddy', 'gifts', 'gills',
    'girls', 'given', 'giver', 'gives', 'gizmo', 'glade', 'gland', 'glare',
    'glass', 'glaze', 'gleam', 'glean', 'glees', 'glens', 'glide', 'glint',
    'gloom', 'glory', 'gloss', 'glove', 'glued', 'glues', 'gnarl', 'gnash',
    'gnats', 'gnome', 'goals', 'goats', 'godly', 'going', 'golds', 'golfs',
    'goods', 'gooey', 'goofy', 'goons', 'goose', 'gored', 'gorge', 'gorse',
    'gotta', 'gouge', 'gourd', 'gowns', 'grace', 'grade', 'grads', 'graft',
    'grail', 'grain', 'grand', 'grant', 'grape', 'graph', 'grasp', 'grass',
    'grate', 'grave', 'gravy', 'grays', 'graze', 'great', 'greed', 'greek',
    'green', 'greet', 'grids', 'grief', 'grill', 'grime', 'grimy', 'grind',
    'grins', 'gripe', 'grist', 'grits', 'groan', 'groin', 'groom', 'grope',
    'gross', 'group', 'grout', 'grove', 'growl', 'grows', 'grown', 'grubs',
    'gruff', 'grunt', 'guard', 'guava', 'guess', 'guest', 'guide', 'guild',
    'guilt', 'guise', 'gulch', 'gulfs', 'gulls', 'gulps', 'gummy', 'gumbo',
    'gunky', 'gusts', 'gusty', 'gypsy', 'habit', 'hacks', 'haiku', 'hails',
    'hairs', 'hairy', 'halts', 'halve', 'hands', 'handy', 'hangs', 'happy',
    'hardy', 'harem', 'hares', 'harks', 'harms', 'harsh', 'haste', 'hasty',
    'hated', 'hater', 'hates', 'hauls', 'haunt', 'haven', 'havoc', 'hawks',
    'hazel', 'heads', 'heals', 'heaps', 'hears', 'heart', 'heath', 'heats',
    'heave', 'heavy', 'hedge', 'heeds', 'heels', 'hefty', 'heirs', 'heist',
    'helix', 'hello', 'helps', 'hence', 'henna', 'herbs', 'herds', 'heron',
    'heros', 'hertz', 'hexed', 'hexes', 'hider', 'hides', 'hiked', 'hiker',
    'hikes', 'hills', 'hilly', 'hilts', 'hinds', 'hinge', 'hints', 'hippo',
    'hippy', 'hired', 'hires', 'hitch', 'hives', 'hoard', 'hoary', 'hobby',
    'hocks', 'hoist', 'holds', 'holes', 'holly', 'homed', 'homer', 'homes',
    'hones', 'honey', 'honks', 'honor', 'hoods', 'hoofs', 'hooks', 'hoops',
    'hoots', 'hoped', 'hopes', 'horde', 'horns', 'horny', 'horse', 'hosed',
    'hoses', 'hosts', 'hotel', 'hound', 'hours', 'house', 'hovel', 'hover',
    'howdy', 'howls', 'human', 'humid', 'humor', 'humps', 'humus', 'hunch',
    'hunks', 'hunky', 'hunts', 'hurls', 'hurry', 'hurts', 'husky', 'hutch',
    'hyena', 'hymns', 'hypes', 'hyper', 'ideal', 'ideas', 'idyll', 'igloo',
    'image', 'imply', 'inane', 'inbox', 'incur', 'index', 'india', 'indie',
    'inept', 'inert', 'infer', 'inlet', 'inner', 'input', 'inset', 'inter',
    'intro', 'inure', 'irate', 'irked', 'irony', 'islet', 'issue', 'itchy',
    'items', 'ivory', 'jacks', 'jaded', 'jades', 'jails', 'jaunt', 'jawed',
    'jeans', 'jeeps', 'jeers', 'jello', 'jelly', 'jests', 'jetty', 'jewel',
    'jiffy', 'jihad', 'jilts', 'jinks', 'jives', 'jocks', 'joeys', 'joins',
    'joint', 'joist', 'joked', 'joker', 'jokes', 'jolly', 'jolts', 'joule',
    'joust', 'jowls', 'judge', 'juice', 'juicy', 'jumbo', 'jumps', 'jumpy',
    'junco', 'junks', 'junky', 'juror', 'jutes', 'kayak', 'keeps', 'kelps',
    'kendo', 'kenya', 'keyed', 'khaki', 'kicks', 'kiddo', 'kiddy', 'kills',
    'kilns', 'kilos', 'kilts', 'kinds', 'kines', 'kings', 'kinks', 'kinky',
    'kinos', 'kiosk', 'kited', 'kiter', 'kites', 'kithe', 'kitty', 'kiwis',
    'knack', 'knaps', 'knave', 'knead', 'kneed', 'kneel', 'knees', 'knelt',
    'knife', 'knish', 'knits', 'knobs', 'knock', 'knoll', 'knops', 'knots',
    'known', 'knows', 'knurl', 'label', 'labor', 'laced', 'lacer', 'laces',
    'lacks', 'laded', 'laden', 'lades', 'ladle', 'lager', 'laics', 'laird',
    'lairs', 'laked', 'laker', 'lakes', 'lamed', 'lamer', 'lames', 'lamps',
    'lance', 'lands', 'lanky', 'larch', 'lards', 'large', 'largo', 'larks',
    'larky', 'larry', 'larva', 'lasso', 'latch', 'later', 'lates', 'lathe',
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
    'light', 'lights', 'lighty', 'ligion', 'ligible', 'ligil', 'ligils',
    'liging', 'ligious', 'liglity', 'ligna', 'lignon', 'lignose', 'lignum',
}

fun_patterns = {
    'buddy', 'curry', 'daddy', 'daffy', 'daily', 'dairy', 'dandy', 'dilly',
    'dizzy', 'dotty', 'droll', 'dummy', 'dumpy', 'fluky', 'foamy', 'foggy',
    'folky', 'folly', 'forty', 'fully', 'furry', 'fuzzy', 'gaily', 'gammy',
    'golly', 'gooey', 'goofy', 'goony', 'gormy', 'gowny', 'gravy', 'grimy',
    'gummy', 'gunky', 'gusty', 'hammy', 'hanky', 'hardy', 'harpy', 'harry',
    'hasty', 'hatty', 'hawky', 'heady', 'hefty', 'henry', 'herby', 'herky',
    'hiffy', 'hippy', 'hoagy', 'hoaky', 'hoary', 'hobby', 'hokey', 'holly',
    'homey', 'honey', 'honky', 'hooey', 'hooky', 'hooty', 'hoppy', 'horny',
    'horsy', 'hotly', 'hotty', 'huffy', 'hulky', 'humid', 'humpy', 'hunky',
    'hunny', 'hurky', 'hurry', 'hurty', 'husky', 'icily', 'ickey', 'igloo',
    'imply', 'inlay', 'irily', 'isily', 'itily', 'ivory', 'jabby', 'jacky',
    'jaggy', 'jakey', 'jammy', 'janky', 'jarky', 'jarvy', 'jaunt', 'jauny',
    'jawky', 'jawny', 'jawsy', 'jazzy', 'jelly', 'jenny', 'jeery', 'jeety',
    'jelty', 'jerby', 'jerky', 'jergy', 'jerry', 'jersy', 'jessy', 'jesty',
    'jetty', 'jewel', 'jiffy', 'jilly', 'jimmy', 'jinky', 'jinny', 'jinsy',
    'jirly', 'jirny', 'jokey', 'joksy', 'jolly', 'jolny', 'jolsy', 'jolty',
    'jomby', 'jonky', 'jonny', 'jonsy', 'jonty', 'joory', 'joosy', 'jooty',
    'joply', 'jopsy', 'jopty', 'jorby', 'jorky', 'jorny', 'jorsy', 'jorty',
    'joshy', 'jossy', 'josty', 'jotby', 'jotly', 'jotny', 'jotsy', 'jotty',
    'jouby', 'jouly', 'jousy', 'jouty', 'jouzy', 'jovey', 'jovly', 'jovny',
    'jovsy', 'jovty', 'jovvy', 'jowby', 'jowey', 'jowky', 'jowly', 'jowny',
    'jowsy', 'jowty', 'joxey', 'joxsy', 'joyed', 'joyey', 'joyle', 'joyly',
    'joysey', 'joysy', 'joysty', 'jozey', 'jozsy', 'kappa', 'kayak', 'keeps',
    'kendo', 'kebab', 'kelly', 'kerry', 'kicky', 'kiddy', 'killy', 'kitty',
    'kooky', 'krazy',
}

all_domains = []

# Parse the JSON objects from the file
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
            except json.JSONDecodeError:
                pass

print(f"Total domains collected: {len(all_domains)}")

# Now filter for interesting ones
interesting = []

for item in all_domains:
    domain_name = item['name'].lower()
    reasons = []
    
    if len(domain_name) == 5:
        # Palindromes
        if domain_name == domain_name[::-1]:
            reasons.append('palindrome')
        
        # Double letters
        if domain_name[0] == domain_name[1]:
            reasons.append('double_start')
        if domain_name[3] == domain_name[4]:
            reasons.append('double_end')
        if domain_name[1] == domain_name[2]:
            reasons.append('double_middle')
        
        # Words
        if domain_name in words:
            reasons.append('word')
        
        # Fun patterns
        if domain_name in fun_patterns:
            reasons.append('fun_pattern')
        
        # Number patterns
        if any(c.isdigit() for c in domain_name):
            reasons.append('has_numbers')
            if '0' in domain_name and 'x' in domain_name:
                reasons.append('hex_like')
    
    if reasons:
        interesting.append({
            'domain': item['domain'],
            'name': domain_name,
            'tld': item['tld'],
            'price': item['price'],
            'renewal': item['renewal'],
            'reasons': reasons,
        })

# Sort by price
interesting.sort(key=lambda x: (x['price'], x['domain']))

print(f"Interesting domains found: {len(interesting)}\n")

# Show top 50
print("="*80)
print(f"{'#':3s} {'Domain':20s} {'Price':8s} {'Renewal':8s} {'Traits'}")
print("="*80)

for i, item in enumerate(interesting[:50], 1):
    traits = ', '.join(item['reasons'])
    print(f"{i:3d} {item['domain']:20s} ${item['price']:7.2f} ${item['renewal']:7.2f} {traits}")

# Save results
with open('domains_interesting.json', 'w') as f:
    json.dump(interesting[:50], f, indent=2)

print(f"\n✓ Top 50 interesting domains saved to domains_interesting.json")
