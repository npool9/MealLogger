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

    def search_food(self, food_keywords: str, food_type: str="foundation"):
        """
        Search for non-generic (branded) food nutrient information by keyword(s) provided
        For now, we'll just pull the first result
        :param food_keywords: the keywords to search for food in USDA database
        :param food_type: foundation (cheddar cheese) vs. branded (kraft cheddar)
        :return: list of nutrients in food
        """
        food_keywords = food_keywords.replace(' ', "%20")
        if food_type == "branded":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&api_key={self.api_key}"
        elif food_type == "foundation":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=Foundation&api_key={self.api_key}"
        else:
            raise Exception(f"Invalid food type: {food_type} not in [branded, foundation]")
        r = requests.get(url)
        print("USDA Endpoint:", url)
        if r.status_code != 200:
            raise Exception(f"Couldn't get food search response for \"{food_keywords}\"")
        r = r.json()
        food_info = r["foods"][0]
        nutrients = food_info["foodNutrients"]
        keys_to_remove = ["nutrientId", "nutrientNumber", "derivationCode", "derivationDescription", "derivationId",
                          "foodNutrientSourceId", "foodNutrientSourceCode", "foodNutrientSourceDescription", "rank",
                          "indentLevel", "foodNutrientId", "dataPoints", "min", "max", "median"]
        for nut in nutrients:
            for key in keys_to_remove:
                nut.pop(key, None)
        return {food_info["description"]: nutrients}

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
    nut = usda_service.search_food("kraft shredded cheese", "branded")
    print(nut)