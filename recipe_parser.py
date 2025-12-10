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
        self.UI_LABELS = {'optional', 'substitute', 'note', 'servings', 'ingredients for', 'show full recipe',
                          'print recipe', 'nutrition', 'calories'}

        self.UNIT_PATTERN = re.compile(
            r"\b(cup|cups|tbsp|tablespoon|tsp|teaspoon|pound|lb|oz|gram|g|kg|ml|l|liters?)\b",
            re.IGNORECASE
        )
        self.AMOUNT_PATTERN = re.compile(r"\b(\d+\s*\d*\/?\d*)\b")

        self.STRONG_KEYS = [
            "ingredient", "ingredients", "fmc_ingredients",
            "recipe-ingredients", "wprm-recipe-ingredients",
            "ingredients-section"
        ]

    # ------------------------------------------------------------
    # FIND INGREDIENT CONTAINER
    # ------------------------------------------------------------
    def find_ingredient_container(self, soup):
        candidates = []

        # 1) STRONG: match class/id names
        # for key in self.STRONG_KEYS:
        #     matches = soup.find_all(
        #         lambda tag: (tag.has_attr("class") and any(key in c.lower() for c in tag["class"])) or
        #                     (tag.has_attr("id") and key in tag["id"].lower())
        #     )
        #     for tag in matches:
        #         candidates.append((tag, 100))  # strong score

        # 2) MEDIUM: any <section>, <div>, <ul> with lots of ingredient-like <li>
        for tag in soup.find_all(["div", "section"]):
            score = self.score_ingredient_container(tag)
            if score > 0:
                candidates.append((tag, score))

        if not candidates:
            return None

        # pick the highest-scoring container
        candidates.sort(key=lambda x: x[1], reverse=True)
        best, score = candidates[0]

        return best

    # ------------------------------------------------------------
    # SCORE A POTENTIAL INGREDIENT CONTAINER
    # ------------------------------------------------------------
    def score_ingredient_container(self, node):
        """
        Determine whether a DOM node is a good ingredient container.
        Higher scores = more likely to be the correct block.
        """
        # 1) Count descendant text lines
        all_text = node.get_text("\n", strip=True)
        text_lines = [l.strip() for l in all_text.split("\n") if l.strip()]
        # 2) Find LI items using controlled recursion
        li_nodes = self.find_li_with_depth(node, max_depth=2)
        pos = 0
        neg = 0
        # + Positive scoring
        ingredient_like_count = 0
        bad_li = 0
        for li in li_nodes:
            line = li.get_text(" ", strip=True)
            if self.looks_like_ingredient_line(line):
                ingredient_like_count += 1
                pos += 3
            else:
                bad_li += 1
                neg += 1
        # Penalize LI ratio
        if ingredient_like_count == 0:
            neg += 10  # avoid containers with long lists of junk
        # 3) Heading bonus
        heading_text = ""
        if node.find(["h1", "h2", "h3", "h4", "h5"], string=re.compile(r"ingredient", re.I)):
            pos += 2
        # 4) Penalty for overall container size
        descendants = len(list(node.descendants))
        neg += descendants * 0.02  # dynamic scaling
        # 5) Penalty for junk keywords in large text
        junk_hits = sum(self.contains_junk_keywords(l) for l in text_lines)
        neg += junk_hits * 3
        # 6) Penalty for very long containers
        if len(text_lines) > 60:
            neg += 10
        elif len(text_lines) > 120:
            neg += 30
        # 7) Very large number of LI elements (likely nav or sidebar)
        if len(li_nodes) > 25:
            neg += 8
        # Final score
        return pos - neg

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
        NOW IMPROVED TO STOP AT END OF INGREDIENT LIST.
        """
        soup = BeautifulSoup(html, 'html.parser')
        soup = self.find_ingredient_container(soup)
        # print("Found ingredient container:", soup["class"])
        if not soup:
            soup = soup.find("div", class_="fmc_ingredients")
        # soup = soup.find("div", class_="fmc_ingredients")
        candidates: List[Tuple[Optional[str], str, str]] = []

        # 1) JSON-LD recipeIngredient - HIGH confidence
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                payload = json.loads(script.string or '{}')
            except Exception:
                continue

            def walk(obj):
                if isinstance(obj, list):
                    for it in obj:
                        yield from walk(it)
                elif isinstance(obj, dict):
                    yield obj
                    for v in obj.values():
                        yield from walk(v)
                else:
                    return

            for node in walk(payload):
                if isinstance(node, dict) and 'recipe' in str(node.get('@type', '')).lower():
                    instr = node.get('recipeIngredient') or node.get('ingredients') or node.get('ingredient')
                    if instr:
                        if isinstance(instr, list):
                            for line in instr:
                                if isinstance(line, str) and line.strip():
                                    candidates.append((None, line.strip(), 'json-ld'))
                        elif isinstance(instr, str):
                            for l in instr.splitlines():
                                if l.strip():
                                    candidates.append((None, l.strip(), 'json-ld'))

        # 2) WPRM & common selectors (high/med confidence)
        selectors = [
            ".wprm-recipe-ingredient", ".wprm-recipe-ingredient-group",  # WPRM
            ".wprm-recipe-ingredients li",
            ".ingredients-list", ".ingredients", ".recipe-ingredients", ".ingredient-list",
            "[itemprop*=ingredient]", ".ingredient", ".ingredients li", "ul.ingredients", "ol.ingredients"
        ]
        for sel in selectors:
            for node in soup.select(sel):
                # If this node is an li, capture text
                if node.name == 'li':
                    text = node.get_text(separator=' ', strip=True)
                    if text:
                        parent_group = self._find_group_label(node)
                        candidates.append((parent_group, text, 'selector'))
                else:
                    lis = node.find_all('li')
                    if lis:
                        parent_group = None
                        head = node.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
                        if head:
                            parent_group = head.get_text(separator=' ', strip=True)
                        for li in lis:
                            text = li.get_text(separator=' ', strip=True)
                            if text:
                                candidates.append((parent_group, text, 'selector'))

        # ---------- NEW: Determine recipe container ----------
        recipe_containers = [
            ".wprm-recipe-container", ".tasty-recipes", ".mv-create-card",
            ".simple-recipe-pro", ".recipe-card", "#recipe-card",
            ".h-recipe", ".easyrecipe"
        ]

        container = None
        for sel in recipe_containers:
            c = soup.select_one(sel)
            if c:
                container = c
                break

        # headings that signal END of ingredient list
        stop_headings = re.compile(
            r'^(instructions?|steps?|directions?|method|preparation|notes?|nutrition)$',
            re.I
        )

        # ---------- 3) Heuristic fallback inside main container ----------
        if container:
            for node in container.find_all(text=True):
                line = node.strip()
                if not line:
                    continue

                # stop when we reach instructions
                if stop_headings.match(line.lower()):
                    break

                if self._looks_like_ingredient_line(line):
                    candidates.append((None, line, 'heuristic'))
        else:
            # ---------- 4) Fallback: visible text WITH boundary detection ----------
            visible_text = soup.get_text(separator='\n', strip=True)

            found_ingredients = False
            for line in [l.strip() for l in visible_text.splitlines() if l.strip()]:

                # detect start
                if not found_ingredients and self._looks_like_ingredient_line(line):
                    found_ingredients = True

                # detect end
                if found_ingredients and stop_headings.match(line.lower()):
                    break

                if found_ingredients and self._looks_like_ingredient_line(line):
                    candidates.append((None, line, 'heuristic'))

        # ---------- Deduplicate ----------
        seen = set()
        out = []
        for sub, line, source in candidates:
            key = ((sub or '') + '||' + line).lower()
            if key not in seen:
                seen.add(key)
                out.append((sub, line, source))
        return out


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

    def find_li_with_depth(self, node, max_depth=2):
        """Find <li> elements up to a limited depth inside node."""
        results = []
        def walk(n, depth):
            if depth > max_depth:
                return
            # If n is a list container, capture its direct <li> children
            if n.name in ("ul", "ol"):
                for li in n.find_all("li", recursive=False):
                    results.append(li)
            # Recurse into children (both tag and non-tag children)
            for child in getattr(n, "contents", []):
                if getattr(child, "name", None):  # Is a tag
                    walk(child, depth + 1)
        walk(node, depth=0)
        return results

    def looks_like_ingredient_line(self, text: str):
        if not text: return False
        t = text.lower()
        if re.search(r'\d', t): return True
        if self.contains_unit_word(t): return True
        if any(fr in t for fr in self.UNICODE_FRACTIONS): return True
        # 2–6 word ingredient-like noun phrases
        words = t.split()
        if 2 <= len(words) <= 7:
            if t not in ("subscribe", "nutrition", "instructions", "directions"):
                return True
        return False

    def contains_junk_keywords(self, text):
        t = text.lower()
        junk = [
            "print recipe", "pin recipe", "share", "facebook",
            "instagram", "copyright", "subscribe", "newsletter",
            "related recipes", "shop this post", "join", "login",
            "author", "comment", "review", "rating"
        ]
        return any(j in t for j in junk)

    # small helpers for heuristics
    def contains_unit_word(self, s):
        return bool(
            re.search(r'\b(tsp|tbsp|cup|oz|ounce|g|gram|kg|ml|can|clove|slice|stick|package|lb|pound|cup)\b', s, re.I))

    def looks_like_ui_label(self, s):
        s2 = s.strip().lower()
        # filter out short non-ingredient UI labels
        ui_labels = ['optional', 'substitute', 'note', 'servings', 'ingredients for', 'show full recipe']
        if any(s2 == lbl or s2.startswith(lbl + ':') or s2.startswith(lbl + ' ') for lbl in ui_labels):
            return True
        # lines that are purely 'broccoli, carrots, red bell pepper' are okay — not UI label
        # filter out things like 'image' or 'print recipe' etc
        if re.match(r'^(image|print recipe|pin recipe|subscribe|download|nutrition)', s2):
            return True
        return False

    def looks_like_ingredient_text(self, s):
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

# ----------------------------- Example usage -----------------------------
if __name__ == "__main__":
    rp = RecipeParser()
    url = "https://fitmencook.com/recipes/gochujang-ramen-recipe/"
    parsed = rp.parse_recipe_url(url)
    import pprint
    pprint.pprint(parsed, width=160)
