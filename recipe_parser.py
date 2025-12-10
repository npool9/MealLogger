# perfected_recipe_parser.py
# Robust RecipeParser: JSON-LD, WPRM, glued units (2oz/10-oz), percentages, hyphenated amounts,
# nested subsections, notes, and confidence levels.
#
# Requires: requests, beautifulsoup4
# pip install requests beautifulsoup4

import re
from fractions import Fraction
from html import unescape
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Any


class RecipeParser:
    def __init__(self):
        # canonical units and many aliases (extendable)
        self.UNIT_ALIASES = {
            "teaspoon": ["tsp", "t", "teaspoons", "tsps", "tsp."],
            "tablespoon": ["tbsp", "T", "tbl", "tablespoons", "tablespoon", "tbsp."],
            "cup": ["c", "cups", "cupful", "cup", "cups."],
            "gram": ["g", "grams", "gram", "gr", "g."],
            "kilogram": ["kg", "kilograms", "kilogram", "kg."],
            "ounce": ["oz", "ounces", "ounce", "oz."],
            "fluid_ounce": ["fl oz", "floz", "fl. oz", "fl-oz"],
            "pint": ["pt", "pint", "pints"],
            "quart": ["qt", "quart", "quarts"],
            "gallon": ["gal", "gallon", "gallons"],
            "pound": ["lb", "lbs", "pound", "pounds", "lb."],
            "milliliter": ["ml", "millilitre", "milliliters", "ml."],
            "liter": ["l", "litre", "liters", "litres", "l."],
            "pinch": ["pinch", "pinches"],
            "dash": ["dash", "dashes"],
            "clove": ["clove", "cloves"],
            "can": ["can", "cans"],
            "slice": ["slice", "slices"],
            "package": ["package", "pkg", "packet", "packets", "packages"],
            "stick": ["stick", "sticks"],
            "piece": ["piece", "pieces"],
            "head": ["head", "heads"],
            "bunch": ["bunch", "bunches"],
            "stalk": ["stalk", "stalks"],
            "sprig": ["sprig", "sprigs"],
            "bag": ["bag", "bags"],
            "box": ["box", "boxes"],
            "jar": ["jar", "jars"],
        }
        # unit lookup
        self.UNIT_MAP = {}
        for canon, aliases in self.UNIT_ALIASES.items():
            for a in aliases:
                self.UNIT_MAP[a.lower()] = canon

        # number words
        self.NUMBER_WORDS = {
            "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "half": 0.5, "quarter": 0.25, "dozen": 12
        }

        # unicode fractions
        self.UNICODE_FRACTIONS = {
            '½': Fraction(1, 2), '⅓': Fraction(1, 3), '⅔': Fraction(2, 3),
            '¼': Fraction(1, 4), '¾': Fraction(3, 4), '⅛': Fraction(1, 8),
            '⅜': Fraction(3, 8), '⅝': Fraction(5, 8), '⅞': Fraction(7, 8)
        }

        # regexes
        self.RE_UNICODE_FRAC = re.compile('|'.join(map(re.escape, self.UNICODE_FRACTIONS.keys())))
        self.RE_FRACTION = re.compile(r'(?P<int>\d+)?\s*(?P<num>\d+)\s*/\s*(?P<den>\d+)')
        self.RE_RANGE = re.compile(
            r'(?P<a>\d+(?:[.,]\d+)?(?:\s*\d+/\d+)?|\d+\s*%?)\s*(?:-|to|–|—)\s*(?P<b>\d+(?:[.,]\d+)?(?:\s*\d+/\d+)?|\d+\s*%?)',
            re.I
        )
        self.RE_WORD_NUMBER = re.compile(
            r'\b(' + '|'.join(sorted(self.NUMBER_WORDS.keys(), key=len, reverse=True)) + r')\b',
            re.I
        )
        # number + unit glued to each other at start (e.g., '2oz', '10-oz')
        self.RE_NUMUNIT = re.compile(r'^\s*(?P<num>\d+(?:[.,]\d+)?)(?:\s*-\s*)?(?P<unit>[A-Za-z%./]+)\b')
        # percentage at start like "93%" possibly followed by descriptor
        self.RE_PERCENT = re.compile(r'^\s*(?P<pct>\d+(?:[.,]\d+)?)\s*%(\s+|$)')
        # hyphenated like '10-oz' anywhere
        self.RE_HYPHEN_NUMUNIT = re.compile(r'(?P<num>\d+(?:[.,]\d+)?)-(?P<unit>[A-Za-z%./]+)\b')

        # heuristics: UI labels to filter
        self.UI_LABELS = set([
            'optional', 'substitute', 'note', 'servings', 'ingredients for',
            'show full recipe', 'print recipe', 'nutrition', 'calories'
        ])

    # ---------------------- low-level number parsing ----------------------
    def parse_fractional_number(self, s: Optional[str]) -> Optional[float]:
        if not s:
            return None
        s = s.strip()
        # replace unicode fractions with decimals
        def repl(m):
            return str(float(self.UNICODE_FRACTIONS[m.group(0)]))
        s2 = self.RE_UNICODE_FRAC.sub(repl, s)
        # mixed fraction like "1 1/2"
        m = self.RE_FRACTION.search(s2)
        if m:
            whole = int(m.group('int')) if m.group('int') else 0
            return float(whole + Fraction(int(m.group('num')), int(m.group('den'))))
        # simple fraction like "3/4"
        if '/' in s2:
            try:
                return float(Fraction(s2))
            except Exception:
                pass
        # plain number
        m2 = re.search(r'(?P<number>\d+(?:[.,]\d+)?)', s2)
        if m2:
            try:
                return float(m2.group('number').replace(',', '.'))
            except Exception:
                pass
        # words like "half"
        m3 = self.RE_WORD_NUMBER.search(s2)
        if m3:
            return float(self.NUMBER_WORDS[m3.group(0).lower()])
        return None

    # ---------------------- unit detection ----------------------
    def _map_unit_candidate(self, token: str) -> Optional[str]:
        if not token:
            return None
        t = token.lower().rstrip('.').strip()
        # try direct
        if t in self.UNIT_MAP:
            return self.UNIT_MAP[t]
        # try with spaces removed (e.g., 'floz' already in map, but check)
        t2 = t.replace(' ', '')
        if t2 in self.UNIT_MAP:
            return self.UNIT_MAP[t2]
        return None

    def find_unit_and_name_after_amount(self, rest: str) -> Tuple[Optional[str], str]:
        """
        Look at the start of `rest` and return (unit_canonical, remainder_name)
        tolerant to punctuation and two-word units ("fl oz").
        """
        rest = (rest or '').strip()
        if not rest:
            return None, ''

        # try two-word unit first
        tokens = rest.split()
        for take in (2, 1):
            candidate = ' '.join(tokens[:take]).lower().rstrip('.,;()')
            # keep letters, %, ., / and spaces
            candidate_clean = re.sub(r'[^a-zA-Z%./\s]+', '', candidate).strip()
            mapped = self._map_unit_candidate(candidate_clean)
            if mapped:
                return mapped, ' '.join(tokens[take:]).strip()

        # as fallback, if the first token is punctuation-stripped and maps
        first = tokens[0].lower().rstrip('.,;()')
        mapped_first = self._map_unit_candidate(re.sub(r'[^a-zA-Z%./]+', '', first))
        if mapped_first:
            return mapped_first, ' '.join(tokens[1:]).strip()

        # also check pattern like "oz." at the very start (regex)
        m = re.match(r'^(?P<u>[A-Za-z%./]+)\b', rest)
        if m:
            maybe = m.group('u').rstrip('.')
            if self._map_unit_candidate(maybe):
                return self._map_unit_candidate(maybe), rest[m.end():].strip()

        return None, rest

    # ---------------------- normalize name ----------------------
    def normalize_ingredient_name(self, name: Optional[str]) -> Optional[str]:
        if name is None:
            return None
        name = name.strip()
        # strip trailing parentheses describing packaging/notes
        name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name)
        name = re.sub(r'\s+', ' ', name)
        return unescape(name).strip()

    # ---------------------- parse single ingredient line ----------------------
    def parse_ingredient_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single ingredient line into structure:
          { original, amount (float or {'min','max'}), unit, name, notes, subsection, confidence }
        """
        orig = (line or '').strip()
        if not orig:
            return None

        w = re.sub(r'^[\-\u2022]\s*', '', orig)  # strip bullets

        # quick: if starts with percentage as descriptor (e.g., "93% lean ground turkey"),
        pct_m = self.RE_PERCENT.match(w)
        if pct_m:
            name = w
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', name)
            if notes_m:
                notes = notes_m.group(1)
                name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name)
            return {
                'original': orig,
                'amount': None,
                'unit': None,
                'name': self.normalize_ingredient_name(name),
                'notes': notes,
                'confidence': 'med'
            }

        # ranges
        range_m = self.RE_RANGE.search(w)
        if range_m:
            a_raw = range_m.group('a')
            b_raw = range_m.group('b')
            a_val = self.parse_fractional_number(a_raw)
            b_val = self.parse_fractional_number(b_raw)
            amt = {'min': a_val, 'max': b_val}
            w_after = self.RE_RANGE.sub('', w, count=1).strip(',;: ')
            unit, name = self.find_unit_and_name_after_amount(w_after)
            if not name:
                name = w_after
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', name)
            if notes_m:
                notes = notes_m.group(1)
                name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()
            return {
                'original': orig, 'amount': amt, 'unit': unit, 'name': self.normalize_ingredient_name(name),
                'notes': notes, 'confidence': 'med'
            }

        # glued number+unit
        nun = self.RE_NUMUNIT.match(w)
        if nun:
            num_s = nun.group('num')
            unit_tok = nun.group('unit').rstrip('.').lower()
            amt_val = self.parse_fractional_number(num_s)
            unit_mapped = self._map_unit_candidate(unit_tok)
            remainder = w[nun.end():].strip()
            remainder = re.sub(r'^[,:;\-\s]+', '', remainder)
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', remainder)
            if notes_m:
                notes = notes_m.group(1)
                remainder = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', remainder).strip()
            if unit_mapped:
                return {
                    'original': orig, 'amount': amt_val, 'unit': unit_mapped,
                    'name': self.normalize_ingredient_name(remainder), 'notes': notes,
                    'confidence': 'med'
                }

        # hyphenated number-unit
        hyp = self.RE_HYPHEN_NUMUNIT.search(w)
        if hyp:
            num_s = hyp.group('num')
            unit_tok = hyp.group('unit').rstrip('.').lower()
            amt_val = self.parse_fractional_number(num_s)
            unit_mapped = self._map_unit_candidate(unit_tok)
            w2 = (w[:hyp.start()] + w[hyp.end():]).strip()
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', w2)
            if notes_m:
                notes = notes_m.group(1)
                w2 = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', w2).strip()
            return {
                'original': orig, 'amount': amt_val, 'unit': unit_mapped,
                'name': self.normalize_ingredient_name(w2), 'notes': notes, 'confidence': 'med'
            }

        # unicode fraction at start
        u = self.RE_UNICODE_FRAC.match(w.lstrip())
        if u:
            amt_val = self.parse_fractional_number(u.group(0))
            w_rem = w[u.end():].strip()
            unit, name = self.find_unit_and_name_after_amount(w_rem)
            if not name:
                name = w_rem
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', name)
            if notes_m:
                notes = notes_m.group(1)
                name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()
            return {
                'original': orig, 'amount': amt_val, 'unit': unit,
                'name': self.normalize_ingredient_name(name), 'notes': notes, 'confidence': 'med'
            }

        # standard mixed/decimal
        m = re.match(r'^\s*(?P<num>(?:\d+\s+\d+/\d+)|(?:\d+/\d+)|(?:\d+(?:[.,]\d+)?))\b', w)
        if m:
            amt_val = self.parse_fractional_number(m.group('num'))
            w_rem = w[m.end():].strip()
            unit, name = self.find_unit_and_name_after_amount(w_rem)
            if not name:
                name = w_rem
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', name)
            if notes_m:
                notes = notes_m.group(1)
                name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()
            return {
                'original': orig, 'amount': amt_val, 'unit': unit,
                'name': self.normalize_ingredient_name(name), 'notes': notes, 'confidence': 'med'
            }

        # word-number
        m2 = self.RE_WORD_NUMBER.match(w)
        if m2:
            amt_val = float(self.NUMBER_WORDS[m2.group(0).lower()])
            w_rem = w[m2.end():].strip()
            unit, name = self.find_unit_and_name_after_amount(w_rem)
            if not name:
                name = w_rem
            notes = None
            notes_m = re.search(r'\(([^)]+)\)\s*$', name)
            if notes_m:
                notes = notes_m.group(1)
                name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()
            return {
                'original': orig, 'amount': amt_val, 'unit': unit,
                'name': self.normalize_ingredient_name(name), 'notes': notes, 'confidence': 'med'
            }

        # fallback: treat as name
        notes = None
        notes_m = re.search(r'\(([^)]+)\)\s*$', w)
        name = w
        if notes_m:
            notes = notes_m.group(1)
            name = re.sub(r'\s*\((?:[^()]*)\)\s*$', '', name).strip()

        return {
            'original': orig, 'amount': None, 'unit': None,
            'name': self.normalize_ingredient_name(name), 'notes': notes, 'confidence': 'low'
        }


    # ---------------------- extraction of ingredient lines ----------------------
    def extract_ingredients_from_html(self, html: str) -> List[Tuple[Optional[str], str, str]]:
        """
        Return list of triples: (subsection, raw_line, confidence_source)
        FIXED VERSION:
           - Detects true ingredient list container (WPRM, Tasty, MV-Create, SimpleRecipePro, WP standard)
           - Stops as soon as the ingredient list ends
           - Prevents scraping unrelated text blocks, ads, comments, SEO garbage
        """
        soup = BeautifulSoup(html, 'html.parser')
        candidates: List[Tuple[Optional[str], str, str]] = []

        # -------------------------------
        # 1) Strongest signal: JSON-LD
        # -------------------------------
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string or "{}")
            except Exception:
                continue

            def walk(node):
                if isinstance(node, dict):
                    yield node
                    for v in node.values():
                        yield from walk(v)
                elif isinstance(node, list):
                    for x in node:
                        yield from walk(x)

            for obj in walk(data):
                if not isinstance(obj, dict):
                    continue
                if 'recipeIngredient' in obj:
                    for line in obj['recipeIngredient']:
                        if isinstance(line, str) and line.strip():
                            candidates.append((None, line.strip(), 'json-ld'))
                    return candidates  # JSON-LD is trusted → exit early

        # -----------------------------------------------------
        # 2) Locate the real ingredient container
        # -----------------------------------------------------
        ingredient_container_selectors = [
            ".wprm-recipe-ingredients-container",
            ".wprm-recipe-ingredients",
            ".tasty-recipes-ingredients",
            ".mv-create-ingredients",
            ".simple-recipe-pro-ingredients",
            ".recipe-ingredients",
            "[itemprop='recipeIngredient']",
            "[itemprop='ingredients']",
            ".ingredients",
            "ul.ingredients",
        ]

        container = None
        for sel in ingredient_container_selectors:
            c = soup.select_one(sel)
            if c:
                container = c
                break

        if container:
            # Extract ONLY li items inside this container
            lines = []
            for li in container.find_all("li"):
                txt = li.get_text(" ", strip=True)
                if txt:
                    lines.append(txt)

            # Hard-stop if empty container (avoid false positives)
            if lines:
                for ln in lines:
                    candidates.append((None, ln, 'selector'))
                return candidates

        # -----------------------------------------------------
        # 3) Secondary fallback: tight heuristic scan
        # -----------------------------------------------------
        # Only accept lines that appear in CLOSE PROXIMITY to other ingredient-like lines.
        text_nodes = []
        for el in soup.find_all(text=True):
            line = el.strip()
            if len(line) < 2:
                continue
            text_nodes.append(line)

        def looks_like_ing(l):
            if re.search(r'\b\d+\s*(cup|tsp|tbsp|oz|ounce|g|gram|kg|ml|lb|pound|can|clove|package)\b', l, re.I):
                return True
            if re.match(r'^\d', l):
                return True
            return False

        # collect only sequences of 3+ ingredient-like lines
        block = []
        final_blocks = []

        for line in text_nodes:
            if looks_like_ing(line):
                block.append(line)
            else:
                if len(block) >= 3:  # real ingredient list
                    final_blocks.append(block)
                block = []

        if len(block) >= 3:
            final_blocks.append(block)

        if final_blocks:
            # Take only the largest block (most likely real ingredients)
            main = max(final_blocks, key=len)
            for ln in main:
                candidates.append((None, ln, 'heuristic'))
            return candidates

        # As a last fallback, return nothing instead of junk
        return []

    def _find_group_label(self, node) -> Optional[str]:
        ancestor = node
        for _ in range(4):
            ancestor = ancestor.parent
            if ancestor is None:
                break
            if ancestor.get('class'):
                cls = ' '.join(ancestor.get('class'))
                if 'group-name' in cls or 'ingredient-group' in cls or 'wprm-recipe-group-name' in cls:
                    h = ancestor.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
                    if h:
                        return h.get_text(separator=' ', strip=True)
            h = ancestor.find(['h1', 'h2', 'h3', 'h4'])
            if h and len(h.get_text(strip=True).split()) <= 6:
                return h.get_text(separator=' ', strip=True)
        return None

    def _looks_like_ingredient_line(self, s: str) -> bool:
        s2 = s.strip()
        if not s2:
            return False
        # filter UI labels
        low = s2.lower()
        for lbl in self.UI_LABELS:
            if low == lbl or low.startswith(lbl + ':') or low.startswith(lbl + ' '):
                return False
        if re.search(r'\d', s2):
            return True
        if re.search(r'\b(tsp|tbsp|cup|oz|ounce|g|gram|kg|ml|can|clove|slice|stick|package|lb|pound|stalk|sprig|bag|box)\b', s2, re.I):
            return True
        if 1 <= len(s2.split()) <= 7:
            if s2.lower() in ['garnish', 'sauce', 'instructions', 'steps', 'notes']:
                return False
            return True
        return False

    # ---------------------- top-level parse url ----------------------
    def parse_recipe_url(self, url: str) -> List[Dict[str, Any]]:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        html = r.text

        raw_candidates = self.extract_ingredients_from_html(html)

        parsed = []
        for subsection, raw_line, source in raw_candidates:
            if not raw_line or raw_line.strip().lower() in self.UI_LABELS:
                continue
            parsed_item = self.parse_ingredient_line(raw_line)
            if not parsed_item:
                continue
            parsed_item['subsection'] = subsection
            if source == 'json-ld':
                parsed_item['confidence'] = 'high'
            elif source == 'selector' and parsed_item.get('confidence') == 'low':
                parsed_item['confidence'] = 'med'
            if not parsed_item.get('name'):
                parsed_item['name'] = parsed_item.get('original')
            parsed.append(parsed_item)
        return parsed


# ----------------------------- Example usage -----------------------------
if __name__ == "__main__":
    rp = RecipeParser()
    url = "https://fitmencook.com/recipes/gochujang-ramen-recipe/"
    parsed = rp.parse_recipe_url(url)
    import pprint
    pprint.pprint(parsed, width=160)
