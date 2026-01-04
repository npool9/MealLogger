import json
import requests


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

    def search_foundation_food(self, food_keywords: str):
        """
        Search for foundation (generic, non-branded) food nutrient information by keyword(s) provided
        For now, we'll just pull the first result
        :param food_keywords: the keywords to search for food in USDA database
        :return: list of nutrients in food
        """
        food_keywords = food_keywords.replace(' ', "%20")
        url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=Foundation&api_key={self.api_key}"
        r = requests.get(url)
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

    def search_food(self, food_keywords: str):
        """
        Search for non-generic (branded) food nutrient information by keyword(s) provided
        For now, we'll just pull the first result
        :param food_keywords: the keywords to search for food in USDA database
        :return: list of nutrients in food
        """
        food_keywords = food_keywords.replace(' ', "%20")
        url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&api_key={self.api_key}"
        r = requests.get(url)
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

if __name__ == "__main__":
    usda_service = USDAService()
    nut = usda_service.search_foundation_food("cheddar cheese")
    print(nut)