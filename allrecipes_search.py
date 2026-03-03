from recipe_search import RecipeSearch
from recipe_parser import RecipeParser
import requests
from bs4 import BeautifulSoup
import re


class AllRecipes(RecipeSearch):
    """
    Inherits properties and functions from RecipeSearch class
    Utilities for navigating and retrieving data from the AllRecipes website
    """

    def __init__(self, meal):
        """
        Initialize utilities for AllRecipes website navigation
        :param meal: the initialized meal object -- mostly null attributes
        """
        super().__init__(meal)
        self._name = "AllRecipes"
        self._base_url = "https://www.allrecipes.com/"
        self._search_url = self._base_url + "search?q="
        self._rp = RecipeParser()
        self._recipe_soup = None

    def search_for_meal(self):
        """
        Search for the meal name on AllRecipes
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        r = requests.get(search_url, headers=self._rp.HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Find first recipe card link
        recipe_card = soup.find("a", class_="mntl-card-list-card--extendable")
        if not recipe_card or not recipe_card.get("href"):
            raise ValueError(f"No recipes found on AllRecipes for '{self.meal_name}'")
        recipe_url = recipe_card["href"]

        # Fetch recipe page once and cache it
        self._recipe_soup = self._rp.fetch_page(recipe_url)

        # Extract title from the page
        h1 = self._recipe_soup.find("h1")
        if h1:
            self.meal.name = h1.get_text(strip=True)

        return recipe_url

    def load_url(self, url):
        """
        Load a recipe page directly by URL, skipping search.
        :param url: direct URL to the recipe page
        :return: the url
        """
        self._recipe_soup = self._rp.fetch_page(url)

        h1 = self._recipe_soup.find("h1")
        if h1:
            self.meal.name = h1.get_text(strip=True)

        return url

    def get_ingredients(self, meal, recipe_url=None):
        """
        Get list of ingredients
        :param meal: the (mostly) empty meal object
        :param recipe_url: optional direct URL to skip search
        :return: list of ingredients for the recipe with measurements (list of str)
        """
        if recipe_url:
            self.load_url(recipe_url)
        else:
            recipe_url = self.search_for_meal()
        meal.recipe_url = recipe_url
        meal.website_name = self._name

        soup = self._recipe_soup or self._rp.fetch_page(recipe_url)
        ingredient_lines = []

        # Try JSON-LD first
        recipe_data = self._rp.get_recipe_jsonld(recipe_url, soup=soup)
        if recipe_data and recipe_data.get("recipeIngredient"):
            ingredient_lines = recipe_data["recipeIngredient"]

        # Fall back to AllRecipes-specific HTML scraping
        if not ingredient_lines:
            ingredient_lines = self._extract_ingredients_from_html(soup)

        if not ingredient_lines:
            print(f"Warning: No ingredients found for {recipe_url}")
            return []

        ingredients = self._rp.parse_recipe(ingredient_lines)
        print(ingredients)
        return ingredients

    def _extract_ingredients_from_html(self, soup):
        """
        Extract ingredient strings from AllRecipes HTML using structured data attributes.
        :param soup: BeautifulSoup object of the recipe page
        :return: list of ingredient strings, or empty list
        """
        ingredients = []
        for li in soup.find_all('li', class_='mm-recipes-structured-ingredients__list-item'):
            qty_span = li.find('span', attrs={'data-ingredient-quantity': 'true'})
            unit_span = li.find('span', attrs={'data-ingredient-unit': 'true'})
            name_span = li.find('span', attrs={'data-ingredient-name': 'true'})

            parts = []
            if qty_span and qty_span.get_text(strip=True):
                parts.append(qty_span.get_text(strip=True))
            if unit_span and unit_span.get_text(strip=True):
                parts.append(unit_span.get_text(strip=True))
            if name_span and name_span.get_text(strip=True):
                parts.append(name_span.get_text(strip=True))

            if parts:
                ingredients.append(' '.join(parts))

        return ingredients

    def get_recipe_steps(self, meal):
        """
        Get the description of the given recipe
        :param meal: the meal object
        """
        soup = self._recipe_soup or self._rp.fetch_page(meal.recipe_url)

        # Try JSON-LD first
        rec = self._rp.get_recipe_jsonld(meal.recipe_url, soup=soup)
        if rec and rec.get("recipeInstructions"):
            steps = []
            for instruction in rec["recipeInstructions"]:
                if isinstance(instruction, dict):
                    steps.append(instruction.get("text", ""))
                else:
                    steps.append(str(instruction))
            if any(steps):
                return '\n'.join(steps)

        # Fallback: extract steps from HTML
        steps = []
        steps_container = soup.find("div", class_="mm-recipes-steps__content")
        if steps_container:
            for li in steps_container.find_all("li"):
                p = li.find("p", class_="mntl-sc-block-html")
                if p:
                    text = p.get_text(strip=True)
                    if text:
                        steps.append(text)

        return '\n'.join(steps)

    def get_recipe_servings(self, meal):
        """
        Get the servings for this recipe
        :param meal: the meal object
        """
        soup = self._recipe_soup or self._rp.fetch_page(meal.recipe_url)

        # Try JSON-LD recipeYield
        rec = self._rp.get_recipe_jsonld(meal.recipe_url, soup=soup)
        if rec and rec.get("recipeYield"):
            yield_val = rec["recipeYield"]
            # recipeYield can be a string or array
            if isinstance(yield_val, list):
                yield_val = yield_val[0]
            m = re.search(r'(\d+)', str(yield_val))
            if m:
                return m.group(1)

        # Fallback: recipe details section
        details = soup.find("div", class_="mm-recipes-details")
        if details:
            for item in details.find_all("div", class_="mm-recipes-details__item"):
                label = item.find("div", class_="mm-recipes-details__label")
                if label and "serving" in label.get_text(strip=True).lower():
                    value = item.find("div", class_="mm-recipes-details__value")
                    if value:
                        m = re.search(r'(\d+)', value.get_text(strip=True))
                        if m:
                            return m.group(1)

        print("Couldn't find number of servings")
        return None

    def get_serving_size_and_unit(self, meal):
        """
        Get the serving size and unit.
        AllRecipes does not provide an explicit serving size (weight/volume),
        only "Servings Per Recipe".
        :param meal: the meal object
        """
        return None, None