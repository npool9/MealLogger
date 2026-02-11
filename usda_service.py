import json
import re
import requests

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
# Matches: "1 cup", "1/4 cup", "0.5 clove", "3 large slices", "1 medium (2-3/4\" dia)"
PORTION_PATTERN = re.compile(
    r'^(\d+(?:/\d+)?(?:\.\d+)?)\s+'  # amount (required)
    r'(?:small|medium|large|extra large|extra-large)?\s*'  # optional size modifier
    r'([a-zA-Z][a-zA-Z\s]*?)(?:\s|$|,|\()',  # unit name (letters, capture until space/comma/paren)
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
        self.api_key = json.load(open("api_keys.json", 'r'))["usda"]
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.food_search_endpoint = "/foods/search"
        self.food_details_endpoint = "/food"

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
                    if mod_value.isdigit() and mod_value in FNDDS_PORTION_CODES:
                        # Parse the FNDDS code description for unit if we don't have one
                        desc = FNDDS_PORTION_CODES[mod_value].lower()
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

                if unit and unit != "undetermined":
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
                            if unit and amount > 0:
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
                        if unit and amount > 0:
                            grams_per_unit = round(mass_serving_size / amount, 2)
                            add_portion(unit, "", grams_per_unit)
                    except:
                        pass

        return portions

    def search_food(self, food_keywords: str, food_type: str="foundation"):
        """
        Search for food nutrient information and portion data by keyword(s).
        :param food_keywords: the keywords to search for food in USDA database
        :param food_type: foundation, sr_legacy, or branded
        :return: dict with 'nutrients' and 'portions' keys
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
        print("USDA URL:", url)
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Couldn't get food search response for \"{food_keywords}\"")
        r = r.json()
        food_info = r["foods"][0]
        # Extract nutrients
        nutrients = food_info["foodNutrients"]
        keys_to_remove = ["nutrientId", "nutrientNumber", "derivationCode", "derivationDescription", "derivationId",
                          "foodNutrientSourceId", "foodNutrientSourceCode", "foodNutrientSourceDescription", "rank",
                          "indentLevel", "foodNutrientId", "dataPoints", "min", "max", "median"]
        for nut in nutrients:
            for key in keys_to_remove:
                nut.pop(key, None)
        # Get portion conversions using the thorough extraction method
        portions = {}
        if "fdcId" in food_info:
            portions = self.get_food_portion_conversions(food_info["fdcId"])

        return {
            "name": food_info["description"],
            "fdcId": food_info.get("fdcId"),
            "nutrients": nutrients,
            "portions": portions
        }

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


if __name__ == "__main__":
    usda_service = USDAService()
    result = usda_service.search_food("kraft shredded cheese", "branded")
    print("Name:", result["name"])
    print("Portions:", result["portions"])
    print("Nutrients:", result["nutrients"])