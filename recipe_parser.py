import json
import re
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

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    def fetch_page(self, url):
        """
        Fetch a URL and return a BeautifulSoup object.
        :param url: the url to fetch
        :return: BeautifulSoup object
        """
        response = requests.get(url, headers=self.HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    def get_recipe_jsonld(self, url, soup=None):
        """
        Extract Recipe JSON-LD structured data from a page.
        :param url: the url to the recipe (used if soup is not provided)
        :param soup: optional pre-fetched BeautifulSoup object
        :return: dict with Recipe JSON-LD data, or None
        """
        if soup is None:
            soup = self.fetch_page(url)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    item_type = item.get('@type', [])
                    if item_type == 'Recipe' or (isinstance(item_type, list) and 'Recipe' in item_type):
                        return item
                    if '@graph' in item:
                        for node in item['@graph']:
                            node_type = node.get('@type', [])
                            if node_type == 'Recipe' or (isinstance(node_type, list) and 'Recipe' in node_type):
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
            try:
                if qty_min == qty_max:
                    amount = float(qty_min)
                else:
                    amount = {"max": float(qty_max), "min": float(qty_min)}
            except (ValueError, TypeError):
                amount = None

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



# ----------------------------- Example usage -----------------------------
if __name__ == "__main__":
    rp = RecipeParser()
    url = "https://fitmencook.com/recipes/gochujang-ramen-recipe/"
    rec = rp.get_recipe_jsonld(url)
    if rec and "recipeIngredient" in rec:
        parsed = rp.parse_recipe(rec["recipeIngredient"])
        print(parsed)
