import re
from fractions import Fraction
from html import unescape
import requests
from bs4 import BeautifulSoup


class RecipeParser:

    def __init__(self):
        # ---------- (Reuse/extend unit maps & parsing helpers from your parser) ----------
        self.UNIT_ALIASES = {
            "teaspoon": ["tsp", "t", "teaspoons", "tsps"],
            "tablespoon": ["tbsp", "T", "tbl", "tablespoons", "tablespoon"],
            "cup": ["c", "cups", "cupful", "cup"],
            "gram": ["g", "grams", "gram", "gr"],
            "ounce": ["oz", "ounces", "ounce"],
            "pound": ["lb", "lbs", "pound", "pounds"],
            "milliliter": ["ml", "millilitre", "milliliters"],
            "liter": ["l", "litre", "liters", "litres"],
            "pinch": ["pinch", "pinches"],
            "dash": ["dash", "dashes"],
            "clove": ["clove", "cloves"],
            "can": ["can", "cans"],
            "slice": ["slice", "slices"],
            "package": ["package", "pkg", "packet", "packets", "packages"],
            "stick": ["stick", "sticks"],
            "piece": ["piece", "pieces"],
            "head": ["head", "heads"],
            "bunch": ["bunch", "bunches"]
        }
        self.UNIT_MAP = {}
        for can, aliases in self.UNIT_ALIASES.items():
            for a in aliases:
                self.UNIT_MAP[a.lower()] = can

        self.NUMBER_WORDS = {
            "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "half": 0.5, "quarter": 0.25, "dozen": 12
        }

        self.UNICODE_FRACTIONS = {
            '½': Fraction(1, 2), '⅓': Fraction(1, 3), '⅔': Fraction(2, 3),
            '¼': Fraction(1, 4), '¾': Fraction(3, 4), '⅛': Fraction(1, 8),
            '⅜': Fraction(3, 8), '⅝': Fraction(5, 8), '⅞': Fraction(7, 8)
        }

        self.RE_UNICODE_FRAC = re.compile('|'.join(map(re.escape, self.UNICODE_FRACTIONS.keys())))
        self.RE_FRACTION = re.compile(r'(?P<int>\d+)?\s*(?P<num>\d+)\s*/\s*(?P<den>\d+)')
        self.RE_RANGE = re.compile(r'(?P<a>\d+(?:[.,]\d+)?(?:\s*\d+/\d+)?)\s*(?:-|to|–|—)\s*(?P<b>\d+(?:[.,]\d+)?(?:\s*\d+/\d+)?)', re.I)
        self.RE_WORD_NUMBER = re.compile(r'\b(' + '|'.join(sorted(self.NUMBER_WORDS.keys(), key=len, reverse=True)) + r')\b', re.I)

    def parse_fractional_number(self, s: str):
        if not s: return None
        s = s.strip()
        # unicode -> decimals
        def repl(m):
            return str(float(self.UNICODE_FRACTIONS[m.group(0)]))
        s2 = self.RE_UNICODE_FRAC.sub(repl, s)
        # mixed fraction like "1 1/2"
        m = self.RE_FRACTION.search(s2)
        if m:
            whole = int(m.group('int')) if m.group('int') else 0
            return float(whole + Fraction(int(m.group('num')), int(m.group('den'))))
        if '/' in s2:
            try:
                return float(Fraction(s2))
            except Exception:
                pass
        m2 = re.search(r'(?P<number>\d+(?:[.,]\d+)?)', s2)
        if m2:
            return float(m2.group('number').replace(',', '.'))
        m3 = self.RE_WORD_NUMBER.search(s2)
        if m3:
            return float(self.NUMBER_WORDS[m3.group(0).lower()])
        return None

    def find_unit_and_name_after_amount(self, rest: str):
        rest = (rest or '').strip()
        if not rest: return None, ''
        tokens = rest.split()
        for take in (2,1):
            candidate = ' '.join(tokens[:take]).lower().rstrip('.,;()')
            candidate_clean = re.sub(r'[^a-zA-Z%/]+', '', candidate)
            if candidate_clean in self.UNIT_MAP:
                return self.UNIT_MAP[candidate_clean], ' '.join(tokens[take:]).strip()
        first = tokens[0].lower().rstrip('.,;()')
        if first in self.UNIT_MAP:
            return self.UNIT_MAP[first], ' '.join(tokens[1:]).strip()
        return None, rest

    def normalize_ingredient_name(self, name: str):
        name = name.strip()
        name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name)  # drop trailing parentheses notes
        name = re.sub(r'\s+', ' ', name)
        return unescape(name)

    def parse_ingredient_line(self, line: str):
        orig = (line or '').strip()
        if not orig: return None
        w = re.sub(r'^[\-\u2022]\s*', '', orig)  # strip bullets
        # handle ranges and amounts
        range_m = self.RE_RANGE.search(w)
        amt = None
        if range_m:
            a = self.parse_fractional_number(range_m.group('a'))
            b = self.parse_fractional_number(range_m.group('b'))
            amt = {'min': a, 'max': b}
            w = self.RE_RANGE.sub('', w, count=1).strip(',;: ')
        else:
            # unicode fraction or numeric start
            u = self.RE_UNICODE_FRAC.match(w.lstrip())
            if u:
                amt = self.parse_fractional_number(u.group(0))
                w = w[u.end():].strip()
            else:
                m = re.match(r'^\s*(?P<num>(?:\d+\s+\d+/\d+)|(?:\d+/\d+)|(?:\d+(?:[.,]\d+)?))\b', w)
                if m:
                    amt = self.parse_fractional_number(m.group('num'))
                    w = w[m.end():].strip()
                else:
                    m2 = self.RE_WORD_NUMBER.match(w)
                    if m2:
                        amt = float(self.NUMBER_WORDS[m2.group(0).lower()])
                        w = w[m2.end():].strip()
        unit, name = self.find_unit_and_name_after_amount(w)
        if not name:
            name = w
        # strip trailing notes in parentheses
        notes_m = re.search(r'\(([^)]+)\)\s*$', name)
        notes = None
        if notes_m:
            notes = notes_m.group(1)
            name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()
        name = self.normalize_ingredient_name(name)
        return {'original': orig, 'amount': amt, 'unit': unit, 'name': name or None, 'notes': notes}

    # ---------- New extraction: find Ingredients section by heading + collect lists ----------
    def extract_ingredient_lines_by_heading(self, html, heading_regex=re.compile(r'\bingredient', re.I)):
        """
        1) find headings (h1..h6) or strong tags whose text matches heading_regex
        2) gather subsequent sibling nodes until next heading of same-or-higher importance or until we hit "instructions"
        3) extract text lines from lists (<ul>/<ol>), paragraphs, and short lines
        4) preserve subsection titles (like 'Sauce', 'Curry Paste') if they appear as small headings or bold list items
        Returns list of tuples: (subsection_name_or_None, ingredient_line_str)
        """
        soup = BeautifulSoup(html, 'html.parser')
        candidates = []

        # find heading nodes that likely mark ingredients
        heading_nodes = []
        for tag_name in ['h1','h2','h3','h4','h5','h6','strong','b']:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(separator=' ', strip=True)
                if text and heading_regex.search(text):
                    heading_nodes.append(tag)

        # fallback: look for text "Ingredients for" or other markers in page
        if not heading_nodes:
            for tag in soup.find_all(text=heading_regex):
                if getattr(tag, 'parent', None):
                    heading_nodes.append(tag.parent)

        # For each heading found, gather siblings
        for head in heading_nodes:
            # walk next siblings until next big heading or instructions
            subsection = None
            for sib in head.next_siblings:
                if getattr(sib, 'name', None) in ['h1','h2','h3','h4','h5','h6']:
                    # stop when we hit next main heading
                    break
                # skip invisible/noise
                if getattr(sib, 'name', None) in [None]:  # text node
                    continue
                # If we encounter the instructions block, stop
                txt = sib.get_text(separator=' ', strip=True).lower()
                if 'instruction' in txt or 'method' in txt or 'direction' in txt or re.search(r'\bstep\b', txt):
                    break
                # if it's a list, extract <li>
                if sib.name in ['ul','ol']:
                    for li in sib.find_all('li', recursive=False):
                        # check if li is a subsection title (single short bold text)
                        li_text = li.get_text(separator=' ', strip=True)
                        # if li contains nested list, treat the li's leading text as subsection header
                        nested = li.find(['ul','ol'])
                        if nested:
                            # li_text upto nested tag is subsection name
                            # Extract first text node before nested list
                            head_text = ''
                            for child in li.contents:
                                if child == nested:
                                    break
                                if getattr(child, 'get_text', None):
                                    head_text += ' ' + child.get_text(separator=' ', strip=True)
                                else:
                                    head_text += ' ' + str(child).strip()
                            head_text = head_text.strip()
                            if head_text:
                                current_sub = head_text
                            else:
                                current_sub = None
                            # add nested list items under current_sub
                            for nli in nested.find_all('li', recursive=False):
                                textline = nli.get_text(separator=' ', strip=True)
                                if textline:
                                    candidates.append((current_sub, textline))
                        else:
                            # regular li -> either an ingredient or a small label
                            txt = li_text.strip()
                            # filter UI-only lines
                            if not self.looks_like_ui_label(txt):
                                candidates.append((None, txt if txt else ''))
                # sometimes ingredients are in paragraphs or divs
                elif sib.name in ['p','div','section']:
                    # find short lines inside
                    text = sib.get_text(separator='\n', strip=True)
                    for line in [l.strip() for l in text.splitlines() if l.strip()]:
                        if len(line) < 200 and (re.search(r'\d', line) or self.contains_unit_word(line) or self.looks_like_ingredient_text(line)):
                            if not self.looks_like_ui_label(line):
                                candidates.append((None, line))
        # dedupe-honor original order
        seen = set()
        cleaned = []
        for sub, line in candidates:
            key = (sub or '').strip() + '||' + line.strip()
            if key.lower() not in seen:
                seen.add(key.lower())
                cleaned.append((sub, line.strip()))
        return cleaned

    # small helpers for heuristics
    def contains_unit_word(self, s):
        return bool(re.search(r'\b(tsp|tbsp|cup|oz|ounce|g|gram|kg|ml|can|clove|slice|stick|package|lb|pound|cup)\b', s, re.I))

    def looks_like_ui_label(self, s):
        s2 = s.strip().lower()
        # filter out short non-ingredient UI labels
        ui_labels = ['optional','substitute','note','servings','ingredients for','show full recipe']
        if any(s2 == lbl or s2.startswith(lbl + ':') or s2.startswith(lbl + ' ') for lbl in ui_labels):
            return True
        # lines that are purely 'broccoli, carrots, red bell pepper' are okay — not UI label
        # filter out things like 'image' or 'print recipe' etc
        if re.match(r'^(image|print recipe|pin recipe|subscribe|download|nutrition)', s2):
            return True
        return False

    def looks_like_ingredient_text(self,s):
        # heuristic: ingredient lines often have digits, fractions, or unit words or are short (e.g., "spray coconut oil")
        if re.search(r'\d', s): return True
        if self.contains_unit_word(s): return True
        # also allow short noun phrases (2-6 words) that look like items (e.g., "spray coconut oil", "fresh cilantro")
        if 1 <= len(s.split()) <= 6:
            # avoid UI-y single words like "Garnish"
            if s.lower() in ['garnish', 'sauce', 'instructions', 'steps', 'notes']:
                return False
            return True
        return False

    # ---------- top-level: fetch page and parse ----------
    def parse_recipe_url(self, url):
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        html = r.text
        # First, try JSON-LD recipeIngredient (if site includes it) - high confidence
        soup = BeautifulSoup(html, 'html.parser')
        ingredients = []
        # Try ld+json
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                payload = json.loads(s.string or '{}')
                def walk(obj):
                    if not obj:
                        return []
                    res = []
                    if isinstance(obj, list):
                        for it in obj:
                            res += walk(it)
                    elif isinstance(obj, dict):
                        if obj.get('@type') and 'recipe' in obj.get('@type').lower():
                            for k in ('recipeIngredient','ingredients','ingredient'):
                                if k in obj and obj[k]:
                                    if isinstance(obj[k], list):
                                        res += [(None, i) for i in obj[k]]
                                    else:
                                        res.append((None, obj[k]))
                        for v in obj.values():
                            res += walk(v)
                    return res
                ld_items = walk(payload)
                if ld_items:
                    ingredients += ld_items
            except Exception:
                continue
        # If no JSON-LD or still empty, use heading-based extraction
        if not ingredients:
            extracted = self.extract_ingredient_lines_by_heading(html)
            ingredients += extracted

        # finally parse each ingredient line
        parsed = []
        for subsection, line in ingredients:
            # skip empty or obviously non-ingredient
            if not line or self.looks_like_ui_label(line): continue
            p = self.parse_ingredient_line(line)
            if p:
                p['subsection'] = subsection
                parsed.append(p)
        return parsed

# ---------- quick test ----------
if __name__ == "__main__":
    rp = RecipeParser()
    url = "https://fitmencook.com/recipes/panang-chicken-curry/"
    parsed = rp.parse_recipe_url(url)
    import pprint
    pprint.pprint(parsed, width=140)
