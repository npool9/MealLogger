import json
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

# Fallback volume-to-gram conversions (approximate, based on water density)
# These are used when USDA doesn't provide specific portion data
FALLBACK_VOLUME_TO_GRAMS = {
    # Volume units
    "cup": 240,
    "cups": 240,
    "c": 240,
    "tablespoon": 15,
    "tablespoons": 15,
    "tbsp": 15,
    "tbs": 15,
    "teaspoon": 5,
    "teaspoons": 5,
    "tsp": 5,
    "fluid ounce": 30,
    "fluid ounces": 30,
    "fl oz": 30,
    "milliliter": 1,
    "milliliters": 1,
    "ml": 1,
    "liter": 1000,
    "liters": 1000,
    "l": 1000,
    "pint": 473,
    "pints": 473,
    "quart": 946,
    "quarts": 946,
    "gallon": 3785,
    "gallons": 3785,
    # Weight units
    "ounce": 28.35,
    "ounces": 28.35,
    "oz": 28.35,
    "pound": 453.6,
    "pounds": 453.6,
    "lb": 453.6,
    "lbs": 453.6,
    "kilogram": 1000,
    "kilograms": 1000,
    "kg": 1000,
    "gram": 1,
    "grams": 1,
    "g": 1,
}


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
        # Extract portion data (unit to gram conversions)
        portions = {}
        if "foodMeasures" in food_info:
            for measure in food_info["foodMeasures"]:
                unit = measure.get("disseminationText", "").lower()
                gram_weight = measure.get("gramWeight")
                if unit and gram_weight:
                    portions[unit] = gram_weight
        if "foodPortions" in food_info:
            for portion in food_info["foodPortions"]:
                desc = portion.get("portionDescription", "").lower()
                gram_weight = portion.get("gramWeight")
                if desc and gram_weight:
                    portions[desc] = gram_weight
        # For branded foods, also grab servingSize
        if "servingSize" in food_info and "servingSizeUnit" in food_info:
            unit = food_info["servingSizeUnit"].lower()
            portions[f"1 {unit}"] = food_info["servingSize"]

        # If no portions found, fetch from food details endpoint
        if not portions and "fdcId" in food_info:
            portions = self.get_food_portions(food_info["fdcId"])

        return {
            "name": food_info["description"],
            "fdcId": food_info.get("fdcId"),
            "nutrients": nutrients,
            "portions": portions
        }

    def convert_amount_to_grams(self, amount: float, unit: str, portions: dict) -> float:
        """
        Convert an ingredient amount to grams using USDA portion data,
        with fallback to standard volume/weight conversions.

        :param amount: the numeric amount (e.g., 2 for "2 cups")
        :param unit: the unit to convert from (e.g., "cup", "tbsp")
        :param portions: dict of portion descriptions to gram weights from search_food
        :return: amount in grams
        :raises ValueError: if no conversion found for the unit
        """
        unit_lower = unit.lower().strip()

        # If already in grams, return as-is
        if unit_lower in ("g", "gram", "grams"):
            return amount

        # Try USDA portions first (ingredient-specific, most accurate)
        for portion_desc, gram_weight in portions.items():
            if unit_lower in portion_desc or portion_desc in unit_lower:
                return amount * gram_weight

        # Try matching with "1 unit" pattern
        search_patterns = [
            f"1 {unit_lower}",
            unit_lower,
            f"{unit_lower}s",  # plural
            unit_lower.rstrip('s'),  # singular
        ]
        for pattern in search_patterns:
            for portion_desc, gram_weight in portions.items():
                if pattern in portion_desc:
                    return amount * gram_weight

        # Fallback to standard conversions (approximate)
        if unit_lower in FALLBACK_VOLUME_TO_GRAMS:
            print(f"Note: Using approximate conversion for '{unit}' (not ingredient-specific)")
            return amount * FALLBACK_VOLUME_TO_GRAMS[unit_lower]

        raise ValueError(f"No gram conversion found for unit '{unit}'. Available portions: {list(portions.keys())}")

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