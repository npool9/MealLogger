import json
import math
import re
import requests

# Mass units (already in weight, no volume conversion needed)
MASS_UNITS = {
    "g", "gram", "grams",
    "kg", "kilogram", "kilograms",
    "mg", "milligram", "milligrams",
    "oz", "ounce", "ounces", "onz",
    "lb", "lbs", "pound", "pounds",
}

# Volume unit conversions to cups
# Maps unit names (and abbreviations) to their equivalent in cups
# 1 cup = 240ml (US customary)
VOLUME_TO_CUPS = {
    # Cups
    "cup": 1.0,
    "cups": 1.0,
    "c": 1.0,
    "c.": 1.0,
    # Tablespoons (16 tbsp = 1 cup)
    "tablespoon": 1 / 16,
    "tablespoons": 1 / 16,
    "tbsp": 1 / 16,
    "tbsp.": 1 / 16,
    "tbs": 1 / 16,
    "tbs.": 1 / 16,
    "tbl": 1 / 16,
    "tbl.": 1 / 16,
    "tb": 1 / 16,
    "t": 1 / 16,
    # Note: sometimes "t" means teaspoon - context dependent
    # Teaspoons (48 tsp = 1 cup, or 3 tsp = 1 tbsp)
    "teaspoon": 1 / 48,
    "teaspoons": 1 / 48,
    "tsp": 1 / 48,
    "tsp.": 1 / 48,
    "ts": 1 / 48,
    "ts.": 1 / 48,
    # Fluid ounces (8 fl oz = 1 cup)
    "fluid ounce": 1 / 8,
    "fluid ounces": 1 / 8,
    "fl oz": 1 / 8,
    "fl. oz": 1 / 8,
    "fl. oz.": 1 / 8,
    "floz": 1 / 8,
    "fl-oz": 1 / 8,
    "fluid oz": 1 / 8,
    "fluid oz.": 1 / 8,
    # Milliliters (240ml = 1 cup)
    "milliliter": 1 / 240,
    "milliliters": 1 / 240,
    "millilitre": 1 / 240,
    "millilitres": 1 / 240,
    "ml": 1 / 240,
    "ml.": 1 / 240,
    "cc": 1 / 240,
    # cubic centimeter = 1ml
    # Liters (1L = ~4.227 cups)
    "liter": 4.227,
    "liters": 4.227,
    "litre": 4.227,
    "litres": 4.227,
    "l": 4.227,
    "l.": 4.227,
    # Deciliters (1dl = 100ml = 0.4227 cups)
    "deciliter": 0.4227,
    "deciliters": 0.4227,
    "decilitre": 0.4227,
    "decilitres": 0.4227,
    "dl": 0.4227,
    "dl.": 0.4227,
    # Pints (1 pint = 2 cups)
    "pint": 2.0,
    "pints": 2.0,
    "pt": 2.0,
    "pt.": 2.0,
    # Quarts (1 quart = 4 cups)
    "quart": 4.0,
    "quarts": 4.0,
    "qt": 4.0,
    "qt.": 4.0,
    "qts": 4.0,
    # Gallons (1 gallon = 16 cups)
    "gallon": 16.0,
    "gallons": 16.0,
    "gal": 16.0,
    "gal.": 16.0,
    "gals": 16.0,
    # Drops (approximate: ~60 drops = 1 tsp, so 2880 drops = 1 cup)
    "drop": 1 / 2880,
    "drops": 1 / 2880,
    # Dashes (approximate: ~8 dashes = 1 tsp)
    "dash": 1 / 384,
    "dashes": 1 / 384,
    # Pinches (approximate: ~16 pinches = 1 tsp)
    "pinch": 1 / 768,
    "pinches": 1 / 768,
    # Smidgens (approximate: ~32 smidgens = 1 tsp)
    "smidgen": 1 / 1536,
    "smidgens": 1 / 1536,
    "smidge": 1 / 1536,
}

# Unit conversion multipliers: (from_unit, to_unit) -> multiplier
UNIT_CONVERSIONS = {
    ("G", "MG"): 1000,
    ("G", "UG"): 1_000_000,
    ("MG", "G"): 0.001,
    ("MG", "UG"): 1000,
    ("UG", "G"): 0.000001,
    ("UG", "MG"): 0.001,
    ("KJ", "KCAL"): 0.239006,  # 1 kJ = 0.239 kcal
}

# IU conversions are nutrient-specific
IU_CONVERSIONS = {
    "vitamin a": 0.3,      # 1 IU = 0.3 µg RAE
    "vitamin d": 0.025,    # 1 IU = 0.025 µg
    "vitamin e": 0.67,     # 1 IU = 0.67 mg (d-alpha-tocopherol)
}

# =============================================================================
# FNDDS PORTION CODES: Maps numeric modifier codes to portion descriptions
# Source: USDA FNDDS Portions and Weights dataset
# =============================================================================
FNDDS_PORTION_CODES = {
    # Volume measurements
    "10205": "1 cup",
    "10206": "0.5 cup",
    "10207": "0.25 cup",
    "10208": "0.33 cup",
    "10209": "0.75 cup",
    "10210": "2 cups",
    "21000": "1 tablespoon",
    "21001": "0.5 tablespoon",
    "21002": "2 tablespoons",
    "21003": "3 tablespoons",
    "22000": "1 teaspoon",
    "22001": "0.5 teaspoon",
    "22002": "0.25 teaspoon",
    "22003": "2 teaspoons",
    "30000": "1 fl oz",
    "30001": "2 fl oz",
    "30002": "4 fl oz",
    "30003": "6 fl oz",
    "30004": "8 fl oz",
    "30005": "12 fl oz",
    "30006": "16 fl oz",
    # Common container sizes
    "60424": "1 can or bottle (16 fl oz)",
    "60533": "1 can or bottle (12 fl oz)",
    "60699": "1 drink",
    "63480": "guideline amount per fl oz",
    "64216": "1 bottle (40 fl oz)",
    # Special codes
    "90000": "quantity not specified",
}

# Pattern to extract amount and unit from portion descriptions
# Matches: "1 cup", "1/4 cup", "0.5 clove", "1 flour tortilla", "1 medium (2-3/4\" dia)"
PORTION_PATTERN = re.compile(
    r'^(\d+(?:/\d+)?(?:\.\d+)?)\s+'  # amount (required)
    r'([^(,]+)',  # unit name (everything until paren or comma)
    re.IGNORECASE
)


def parse_portion_amount(amount_str: str) -> float:
    """Parse an amount string, handling fractions like '1/4'."""
    if '/' in amount_str:
        num, denom = amount_str.split('/')
        return float(num) / float(denom)
    return float(amount_str)


def normalize_unit(unit: str) -> str:
    """
    Normalize a unit name to a standard singular form.
    E.g., 'cups' -> 'cup', 'cloves' -> 'clove', 'slices' -> 'slice'
    """
    unit = unit.lower().strip()
    # Specific irregular plurals (ves -> f only for these known words)
    ves_to_f = {'loaves': 'loaf', 'leaves': 'leaf', 'halves': 'half', 'knives': 'knife', 'shelves': 'shelf'}
    if unit in ves_to_f:
        return ves_to_f[unit]
    # ies -> y (berries -> berry)
    if unit.endswith('ies') and len(unit) > 3:
        return unit[:-3] + 'y'
    # es ending - only remove 'es' for sibilant endings (dishes, boxes, buzzes)
    if unit.endswith('es') and len(unit) > 3:
        stem = unit[:-2]
        if stem.endswith(('sh', 'ch', 'ss', 'x', 'z')):
            return stem
        # Otherwise just remove 's' (e.g., "slices" -> "slice", "cloves" -> "clove")
        return unit[:-1]
    # Regular 's' ending
    if unit.endswith('s') and len(unit) > 2:
        return unit[:-1]
    return unit


class USDAService:
    """
    Any operations that interact with the USDA API
    """

    def __init__(self):
        """
        Initialize
        """
        api_keys = json.load(open("api_keys.json", 'r'))
        self.api_key = api_keys["usda"]
        self.anthropic_api_key = api_keys.get("anthropic")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.food_search_endpoint = "/foods/search"
        self.food_details_endpoint = "/food"
        # Load grams-per-cup cache
        self.grams_cache_file = "grams_per_cup_cache.json"
        try:
            with open(self.grams_cache_file, 'r') as f:
                self.grams_cache = json.load(f)
        except FileNotFoundError:
            self.grams_cache = {}

    def get_food_portions(self, fdc_id: int) -> dict:
        """
        Get portion data for a food by its FDC ID using the food details endpoint.

        :param fdc_id: the USDA FoodData Central ID
        :return: dict of portion descriptions to gram weights
        """
        url = f"{self.base_url}{self.food_details_endpoint}/{fdc_id}?api_key={self.api_key}"
        r = requests.get(url)
        if r.status_code != 200:
            return {}
        food_info = r.json()

        portions = {}
        if "foodPortions" in food_info:
            for portion in food_info["foodPortions"]:
                gram_weight = portion.get("gramWeight")
                if not gram_weight:
                    continue

                # Try multiple fields to build portion description
                desc = portion.get("portionDescription", "").lower()

                # SR Legacy uses "modifier" (e.g., "cup", "tbsp")
                if not desc and "modifier" in portion:
                    amount = portion.get("amount", 1)
                    modifier = portion.get("modifier", "").lower()
                    desc = f"{amount} {modifier}".strip()

                # Foundation/other formats use measureUnit object
                if not desc and "measureUnit" in portion:
                    amount = portion.get("amount", 1)
                    measure_unit = portion.get("measureUnit", {})
                    unit_name = measure_unit.get("name", "").lower()
                    if unit_name:
                        desc = f"{amount} {unit_name}"

                if desc and gram_weight:
                    portions[desc] = gram_weight
        return portions

    def get_food_portion_conversions(self, fdc_id: int) -> dict:
        """
        Get all portion-to-gram conversions for a food by its FDC ID.
        Uses the same extraction logic as search_usda_cups.py.

        :param fdc_id: the USDA FoodData Central ID
        :return: nested dict like {"cup": {"sifted": 85.0, "": 130.0}, "tablespoon": {"": 15.0}}
                 Structure: {unit: {modifier: grams_per_unit}}
        """
        url = f"{self.base_url}{self.food_details_endpoint}/{fdc_id}?api_key={self.api_key}"
        r = requests.get(url)
        if r.status_code != 200:
            return {}
        food = r.json()

        portions = {}

        def add_portion(unit: str, modifier: str, grams_per_unit: float):
            """Add a portion to the nested portions dict."""
            if unit not in portions:
                portions[unit] = {}
            if modifier not in portions[unit]:
                portions[unit][modifier] = grams_per_unit

        # Check foodPortions (Foundation, SR Legacy, FNDDS details)
        if "foodPortions" in food:
            for portion in food["foodPortions"]:
                gram_weight = portion.get("gramWeight")
                if not gram_weight:
                    continue

                amount = portion.get("amount", 1)
                if not amount or amount <= 0:
                    continue

                unit = None
                modifier = ""

                # Get unit from measureUnit (preferred source)
                if portion.get("measureUnit"):
                    unit_name = portion["measureUnit"].get("name", "")
                    if unit_name and unit_name.lower() != "undetermined":
                        unit = normalize_unit(unit_name)

                # Get modifier from modifier field
                if portion.get("modifier"):
                    mod_value = str(portion["modifier"])
                    # Check if it's an FNDDS numeric code
                    if mod_value.isdigit():
                        # Parse the FNDDS code description for unit if we don't have one
                        desc = portion["portionDescription"]
                        match = PORTION_PATTERN.match(desc)
                        if match:
                            if not unit:
                                unit = normalize_unit(match.group(2))
                            try:
                                amount = parse_portion_amount(match.group(1))
                            except:
                                pass
                    else:
                        # String modifier (e.g., "sifted", "cooked")
                        modifier = mod_value.lower().strip()
                        # If no measureUnit, modifier might be the unit itself (SR Legacy)
                        if not unit:
                            unit = normalize_unit(mod_value)
                            modifier = ""

                # Try portionDescription if still no unit
                if not unit and portion.get("portionDescription"):
                    desc = portion["portionDescription"].lower()
                    match = PORTION_PATTERN.match(desc)
                    if match:
                        unit = normalize_unit(match.group(2))
                        try:
                            amount = parse_portion_amount(match.group(1))
                        except:
                            pass

                if unit and unit != "undetermined" and unit not in MASS_UNITS:
                    grams_per_unit = round(gram_weight / amount, 2)
                    add_portion(unit, modifier, grams_per_unit)

        # Check foodMeasures (from search/list results) -- Survey (FNDDS)
        if "foodMeasures" in food:
            for measure in food["foodMeasures"]:
                text = measure.get("disseminationText", "").lower()
                gram_weight = measure.get("gramWeight")

                if gram_weight and text:
                    match = PORTION_PATTERN.match(text)
                    if match:
                        try:
                            amount = parse_portion_amount(match.group(1))
                            unit = normalize_unit(match.group(2))
                            if unit and amount > 0 and unit not in MASS_UNITS:
                                grams_per_unit = round(gram_weight / amount, 2)
                                add_portion(unit, "", grams_per_unit)
                        except:
                            pass

        # Check householdServingFullText (Branded foods)
        if "householdServingFullText" in food:
            text = food["householdServingFullText"].lower()
            mass_serving_size = food.get("servingSize")
            mass_unit = food.get("servingSizeUnit", "").upper()

            if mass_serving_size and mass_unit in ["G", "GRAM", "GRAMS", "GRM", "GRMS", "GR", "GRS", "GS"]:
                match = PORTION_PATTERN.match(text)
                if match:
                    try:
                        amount = parse_portion_amount(match.group(1))
                        unit = normalize_unit(match.group(2))
                        if unit and amount > 0 and unit not in MASS_UNITS:
                            grams_per_unit = round(mass_serving_size / amount, 2)
                            add_portion(unit, "", grams_per_unit)
                    except:
                        pass
            portions = self.post_process_portions(portions)

        return portions

    def post_process_portions(self, portions):
        """
        Derive a cup conversion from other volume units if cup isn't already present.
        :param portions: portions dict (should not contain mass units)
        :return: portions dict, possibly with cup entry added
        """
        if "cup" in portions:
            return portions
        # Derive cups from other volume units (e.g., tablespoon -> cup)
        for unit in list(portions.keys()):
            if unit in VOLUME_TO_CUPS:
                for modifier, grams_per_unit in portions[unit].items():
                    cups_factor = VOLUME_TO_CUPS[unit]
                    grams_per_cup = grams_per_unit / cups_factor
                    if "cup" not in portions:
                        portions["cup"] = {}
                    portions["cup"][modifier] = grams_per_cup
        return portions

    def _build_search_url(self, food_keywords: str, food_type: str, page: int = 1, page_size: int = 10) -> str:
        """
        Build USDA food search URL with pagination parameters.
        :param food_keywords: search keywords
        :param food_type: foundation, sr_legacy, or branded
        :param page: page number (1-indexed)
        :param page_size: results per page
        :return: fully-formed URL string
        """
        food_keywords = food_keywords.replace(' ', "%20")
        if food_type == "branded":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&api_key={self.api_key}"
        elif food_type == "foundation":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=Foundation&api_key={self.api_key}"
        elif food_type == "sr_legacy":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=SR%20Legacy&api_key={self.api_key}"
        else:
            raise Exception(f"Invalid food type: {food_type} not in [branded, foundation, sr_legacy]")
        url += f"&pageSize={page_size}&pageNumber={page}"
        return url

    def search_foods_paginated(self, food_keywords: str, food_type: str = "branded", page: int = 1, page_size: int = 10):
        """
        Search USDA and return raw results with pagination metadata.
        :param food_keywords: keywords to search
        :param food_type: foundation, sr_legacy, or branded
        :param page: page number (1-indexed)
        :param page_size: results per page
        :return: dict with 'foods' list, 'totalHits', 'currentPage', 'totalPages'
        """
        url = self._build_search_url(food_keywords, food_type, page, page_size)
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Couldn't get food search response for \"{food_keywords}\"")
        data = r.json()
        total_hits = data.get("totalHits", 0)
        total_pages = math.ceil(total_hits / page_size) if total_hits > 0 else 1
        return {
            "foods": data.get("foods", []),
            "totalHits": total_hits,
            "currentPage": page,
            "totalPages": total_pages,
        }

    def build_food_result(self, food_info: dict) -> dict:
        """
        Take a single food dict from the USDA search API and return a
        processed result with nutrients and portion conversions.
        :param food_info: a single food dict from the 'foods' list
        :return: dict with 'name', 'fdcId', 'nutrients', 'portions'
        """
        portions = self.get_food_portion_conversions(food_info["fdcId"]) if "fdcId" in food_info else {}
        print(f"USDA: {food_info['description']} (fdcId: {food_info.get('fdcId')})")

        nutrients = list(food_info.get("foodNutrients", []))
        keys_to_remove = ["nutrientId", "nutrientNumber", "derivationCode", "derivationDescription", "derivationId",
                          "foodNutrientSourceId", "foodNutrientSourceCode", "foodNutrientSourceDescription", "rank",
                          "indentLevel", "foodNutrientId", "dataPoints", "min", "max", "median"]
        for nut in nutrients:
            for key in keys_to_remove:
                nut.pop(key, None)

        return {
            "name": food_info["description"],
            "fdcId": food_info.get("fdcId"),
            "nutrients": nutrients,
            "portions": portions,
        }

    def search_food(self, food_keywords: str, food_type: str="foundation", target_unit: str=None):
        """
        Search for food nutrient information and portion data by keyword(s).
        Auto-selects the first result.
        :param food_keywords: the keywords to search for food in USDA database
        :param food_type: foundation, sr_legacy, or branded
        :param target_unit: reserved for future use (e.g., grams to volume conversion)
        :return: dict with 'nutrients' and 'portions' keys
        """
        result = self.search_foods_paginated(food_keywords, food_type, page=1, page_size=10)
        foods = result["foods"]
        if not foods:
            raise Exception(f"No results found for \"{food_keywords}\"")
        return self.build_food_result(foods[0])

    def convert_nutrient_unit(self, value, from_unit, to_unit, nutrient_name=None):
        """
        Convert a nutrient value from one unit to another.
        :param value: the numeric value to convert
        :param from_unit: the source unit (e.g., 'G', 'MG', 'UG', 'IU')
        :param to_unit: the target unit
        :param nutrient_name: nutrient name (required for IU conversions)
        :return: converted value
        """
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        if from_unit == to_unit:
            return value
        # Standard unit conversions
        key = (from_unit, to_unit)
        if key in UNIT_CONVERSIONS:
            return value * UNIT_CONVERSIONS[key]
        # IU conversions require knowing the nutrient
        if from_unit == "IU" and nutrient_name:
            nutrient_lower = nutrient_name.lower()
            for nutrient_key, multiplier in IU_CONVERSIONS.items():
                if nutrient_key in nutrient_lower:
                    # IU converts to the base unit (UG for vitamins A/D, MG for vitamin E)
                    iu_value = value * multiplier
                    # If target unit differs from IU's natural target, chain convert
                    if nutrient_key in ["vitamin a", "vitamin d"] and to_unit == "MG":
                        return iu_value * 0.001  # UG -> MG
                    elif nutrient_key == "vitamin e" and to_unit == "UG":
                        return iu_value * 1000  # MG -> UG
                    return iu_value
        raise ValueError(f"No conversion available from {from_unit} to {to_unit} for {nutrient_name}")

    def parse_nutrients_to_ingredient_fields(self, nutrients, nutrient_map=None):
        """
        Parse USDA nutrients into Ingredient-compatible field values with unit conversion.
        :param nutrients: list of nutrient dicts from USDA API
        :param nutrient_map: dict mapping nutrient names to {field, expected_unit}
        :return: dict of {field_name: converted_value}
        """
        if nutrient_map is None:
            with open("nutrient_map.json", "r") as f:
                nutrient_map = json.load(f)
        result = {}
        for nutrient in nutrients:
            nutrient_name = nutrient.get("nutrientName")
            if nutrient_name not in nutrient_map:
                continue
            mapping = nutrient_map[nutrient_name]
            field_name = mapping["field"]
            expected_unit = mapping["expected_unit"]
            # Skip if we already have a value for this field (e.g., Energy from multiple sources)
            if field_name in result:
                continue
            usda_unit = nutrient.get("unitName", "").upper()
            value = nutrient.get("value")
            if value is None:
                continue
            # Convert if units don't match
            if usda_unit != expected_unit:
                try:
                    value = self.convert_nutrient_unit(value, usda_unit, expected_unit, nutrient_name)
                except ValueError as e:
                    print(f"Warning: {e}")
                    continue
            result[field_name] = value
        return result

    def estimate_grams_per_cup(self, ingredient_name: str) -> float | None:
        """
        Use Claude to estimate grams per cup for an ingredient.
        Results are cached to avoid repeated API calls.

        :param ingredient_name: name of the ingredient
        :return: estimated grams per cup, or None if failed
        """
        # Check cache first
        cache_key = ingredient_name.lower().strip()
        if cache_key in self.grams_cache:
            print(f"[CACHE] {ingredient_name}: {self.grams_cache[cache_key]}g/cup")
            return self.grams_cache[cache_key]

        if not self.anthropic_api_key:
            print("Anthropic API key not set")
            return None
        url = "https://api.anthropic.com/v1/messages"
        prompt = f"How many grams is 1 cup of {ingredient_name}? Reply with just the number, nothing else."
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            print(f"[CLAUDE API] Querying: {ingredient_name}...")
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"Claude API error: {r.status_code} - {r.text}")
                return None
            response = r.json()
            text = response["content"][0]["text"].strip()
            grams = float(text)
            # Save to cache
            self.grams_cache[cache_key] = grams
            with open(self.grams_cache_file, 'w') as f:
                json.dump(self.grams_cache, f, indent=2)
            print(f"[CLAUDE API] Result: {grams}g/cup (saved to cache)")
            return grams
        except Exception as e:
            print(f"Claude parsing error: {e}")
            return None

    def estimate_grams(self, amount: float, unit: str, ingredient_name: str) -> float | None:
        """
        Use Claude to estimate grams for any amount + unit + ingredient combination.
        For non-standard units like jar, can, bunch, etc.

        :param amount: numeric amount
        :param unit: unit string (e.g., "jar", "can", "bunch")
        :param ingredient_name: name of the ingredient
        :return: estimated grams, or None if failed
        """
        cache_key = f"{ingredient_name.lower().strip()}|{amount}|{unit.lower().strip()}"
        if cache_key in self.grams_cache:
            cached = self.grams_cache[cache_key]
            print(f"[CACHE] {amount} {unit} {ingredient_name}: {cached}g")
            return cached

        if not self.anthropic_api_key:
            print("Anthropic API key not set")
            return None
        url = "https://api.anthropic.com/v1/messages"
        prompt = (
            f"How many grams is {amount} {unit} of {ingredient_name}? "
            f"Reply with just the number, nothing else."
            f"If you need more info, just give your best estimate anyway."
        )
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            print(f"[CLAUDE API] Querying: {amount} {unit} of {ingredient_name}...")
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"Claude API error: {r.status_code} - {r.text}")
                return None
            response = r.json()
            text = response["content"][0]["text"].strip()
            grams = float(text)
            self.grams_cache[cache_key] = grams
            with open(self.grams_cache_file, 'w') as f:
                json.dump(self.grams_cache, f, indent=2)
            print(f"[CLAUDE API] Result: {amount} {unit} {ingredient_name} = {grams}g (saved to cache)")
            return grams
        except Exception as e:
            print(f"Claude parsing error: {e}")
            return None

    def convert_amount_to_grams(self, amount: float, unit: str, portions: dict, ingredient_name: str = None) -> float:
        """
        TODO: modifier is not supported yet
        Convert an ingredient amount to grams.

        :param amount: numeric amount (e.g., 2 for "2 cups")
        :param unit: unit string (e.g., "cup", "tbsp", "oz")
        :param portions: portion data from get_food_portion_conversions()
                         Structure: {"cup": {"": 120, "sifted": 85}, "tablespoon": {"": 7.5}}
        :return: amount in grams
        :raises ValueError: if no conversion found
        """
        # Weight unit mappings to grams
        WEIGHT_TO_GRAMS = {
            "g": 1.0, "gram": 1.0, "grams": 1.0,
            "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
            "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
            "oz": 28.3495, "ounce": 28.3495, "ounces": 28.3495, "onz": 28.3495,
            "lb": 453.592, "lbs": 453.592, "pound": 453.592, "pounds": 453.592,
        }
        unit_lower = unit.lower().strip()
        normalized = normalize_unit(unit_lower)
        # 1. Direct weight conversion
        if unit_lower in WEIGHT_TO_GRAMS:
            return amount * WEIGHT_TO_GRAMS[unit_lower]
        # 2. Lookup in portions dict
        if portions and normalized in portions:
            modifiers = portions[normalized]
            grams_per_unit = modifiers.get("", next(iter(modifiers.values())))
            return amount * grams_per_unit
        # 3. Derive from another volume unit via cups
        if normalized in VOLUME_TO_CUPS or unit_lower in VOLUME_TO_CUPS:
            requested_cups_factor = VOLUME_TO_CUPS.get(normalized) or VOLUME_TO_CUPS.get(unit_lower)
            if portions:
                for portion_unit, modifiers in portions.items():
                    if portion_unit in VOLUME_TO_CUPS:
                        portion_cups_factor = VOLUME_TO_CUPS[portion_unit]
                        grams_per_portion_unit = modifiers.get("", next(iter(modifiers.values())))
                        grams_per_cup = grams_per_portion_unit / portion_cups_factor
                        return amount * requested_cups_factor * grams_per_cup
            # 4. Estimate using Claude as last resort for volume units
            if ingredient_name:
                grams_per_cup = self.estimate_grams_per_cup(ingredient_name)
                if grams_per_cup:
                    return amount * requested_cups_factor * grams_per_cup
        # 5. General Claude fallback for non-standard units (jar, can, bunch, etc.)
        if ingredient_name:
            grams = self.estimate_grams(amount, unit, ingredient_name)
            if grams:
                return grams
        raise ValueError(f"Cannot convert '{amount} {unit}' to grams: no conversion found")

if __name__ == "__main__":
    usda_service = USDAService()
    result = usda_service.search_food("kraft shredded cheese", "branded")
    print("Name:", result["name"])
    print("Portions:", result["portions"])
    print("Nutrients:", result["nutrients"])