import json
import requests
from bs4 import BeautifulSoup
from ingredient_parser import parse_ingredient


class RecipeParser:

    def __init__(self):
        self.UNIT_MAP = {
            'tsp': 'teaspoon', 'teaspoons': 'teaspoon', 't': 'teaspoon',
            'tbsp': 'tablespoon', 'tablespoons': 'tablespoon', 'tbs': 'tablespoon',
            'cup': 'cup', 'cups': 'cup', 'c': 'cup',
            'oz': 'ounce', 'ounces': 'ounce',
            'lb': 'pound', 'lbs': 'pound', 'pounds': 'pound',
            'g': 'gram', 'grams': 'gram',
            'kg': 'kilogram', 'ml': 'milliliter', 'l': 'liter',
            'clove': 'clove', 'cloves': 'clove',
            'can': 'can', 'cans': 'can',
            'slice': 'slice', 'slices': 'slice',
        }

    def get_recipe_jsonld(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                # JSON-LD can be a single object or a list
                items = data if isinstance(data, list) else [data]
                for item in items:
                    # Check for Recipe type (could be nested in @graph)
                    if item.get('@type') == 'Recipe':
                        return item
                    if '@graph' in item:
                        for node in item['@graph']:
                            if node.get('@type') == 'Recipe':
                                return node
            except json.JSONDecodeError:
                continue
        return None

    def parse_ingredient_line(self, line):
        original = line.strip()
        parsed = parse_ingredient(original)

        # Extract amount (use first quantity if available)
        amount = None
        if parsed.amount:
            qty_min = parsed.amount[0].quantity
            qty_max = parsed.amount[0].quantity_max
            if qty_min == qty_max:
                amount = float(qty_min)
            else:
                amount = {"max": float(qty_max), "min": float(qty_min)}

        # Extract and normalize unit
        unit = None
        if parsed.amount and parsed.amount[0].unit:
            raw_unit = parsed.amount[0].unit #.lower()
            unit = self.UNIT_MAP.get(raw_unit, raw_unit)

        # Extract name
        name = parsed.name[0].text if parsed.name else ''

        # Extract notes from comment and preparation
        notes_parts = []
        if parsed.preparation:
            notes_parts.append(parsed.preparation.text)
        if parsed.comment:
            notes_parts.append(parsed.comment.text)
        notes = ', '.join(notes_parts) if notes_parts else None

        return {
            'original': original,
            'amount': amount,
            'unit': str(unit) if unit is not None else None,
            'name': name,
            'notes': notes
        }

    def parse_recipe(self, recipe: list) -> list:
        """
        Parse the full recipe (list of ingredients)
        :param recipe: list of ingredients
        :return: list of dictionaries, parsed ingredients with original, amount, unit, name, and notes keys
        """
        parsed_recipe = []
        for ing in recipe:
            parsed_recipe.append(self.parse_ingredient_line(ing))
        return parsed_recipe

    def parse_recipe_from_url(self, url):
        """
        Parse recipe from URL
        :param url: the url to the recipe
        :return: list of dictionaries, parsed ingredients with original, amount, unit, name, and notes keys/values
        """
        recipe = self.get_recipe_jsonld(url)
        if "recipeIngredient" in recipe:
            recipe = recipe["recipeIngredient"]
        recipe = self.parse_recipe(recipe)
        return recipe


# ----------------------------- Example usage -----------------------------
if __name__ == "__main__":
    rp = RecipeParser()
    url = "https://fitmencook.com/recipes/gochujang-ramen-recipe/"
    rec = rp.get_recipe_jsonld(url)
    if "recipeIngredient" in rec:
        rec = rec["recipeIngredient"]
    rec = rp.parse_recipe(rec)
    print(rec)
