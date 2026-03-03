from recipe_search import RecipeSearch
from recipe_parser import RecipeParser
import requests
from bs4 import BeautifulSoup
import re


class FitMenCook(RecipeSearch):
    """
    Inherits properties and functions from RecipeSearch class
    Utilities for navigating and retrieving data from the FitMenCook recipe website
    """

    def __init__(self, meal):
        """
        Initialize utilities for FitMenCook website navigation
        :param meal: the initialized meal object -- mostly null attributes
        """
        super().__init__(meal)
        self._name = "FitMenCook"
        self._base_url = "https://fitmencook.com/"
        self._search_url = self._base_url + "?s="
        self._rp = RecipeParser()
        self._recipe_soup = None

    def search_for_meal(self):
        """
        Search for the meal name on the FitMenCook website
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        r = requests.get(search_url, headers=self._rp.HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        recipe_element = soup.find("figure", class_="fmc_grid_figure")
        if not recipe_element or not recipe_element.find("a"):
            raise ValueError(f"No recipes found on FitMenCook for '{self.meal_name}'")
        recipe_url = recipe_element.find("a")["href"]

        # Fetch recipe page once and cache it
        self._recipe_soup = self._rp.fetch_page(recipe_url)

        # Extract title — try h1 with fmc_title_1 class (works for both v1 and v2)
        h1 = self._recipe_soup.find("h1", class_="fmc_title_1")
        if h1:
            self.meal.name = h1.get_text(strip=True)
        else:
            # Fallback: use the first h1 on the page
            h1 = self._recipe_soup.find("h1")
            if h1:
                self.meal.name = h1.get_text(strip=True)

        return recipe_url

    def get_ingredients(self, meal):
        """
        Get list of ingredients
        :parameter meal: the (mostly) empty meal object
        :return: list of ingredients for the recipe with measurements (list of str)
        """
        recipe_url = self.search_for_meal()
        meal.recipe_url = recipe_url
        meal.website_name = self._name

        soup = self._recipe_soup or self._rp.fetch_page(recipe_url)
        ingredient_lines = []

        # Try JSON-LD first
        recipe_data = self._rp.get_recipe_jsonld(recipe_url, soup=soup)
        if recipe_data and recipe_data.get("recipeIngredient"):
            ingredient_lines = recipe_data["recipeIngredient"]

        # Fall back to FitMenCook-specific HTML scraping
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
        Extract ingredient strings from FitMenCook HTML.
        Handles V1 (fmc_ingredients ul li) and V2 (li.fmc_ing_item span.ing-text) formats.
        :param soup: BeautifulSoup object of the recipe page
        :return: list of ingredient strings, or empty list
        """
        ingredients = []

        # V2 format: li.fmc_ing_item with span.ing-text
        v2_items = soup.find_all('li', class_='fmc_ing_item')
        if v2_items:
            seen = set()
            for li in v2_items:
                span = li.find('span', class_='ing-text')
                if span:
                    text = re.sub(r'\s+', ' ', span.get_text(' ', strip=True)).strip()
                    if text and text not in seen:
                        seen.add(text)
                        ingredients.append(text)
            if ingredients:
                return ingredients

        # V1 format: div.fmc_ingredients > ul > li
        ings_div = soup.find('div', class_='fmc_ingredients')
        if ings_div:
            for li in ings_div.find_all('li'):
                if li.find_parent('li'):
                    continue
                text = re.sub(r'\s+', ' ', li.get_text(' ', strip=True)).strip()
                if text:
                    ingredients.append(text)

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
        for step_div in soup.find_all("div", class_="fmc_step_content"):
            text = step_div.get_text(strip=True)
            if text:
                steps.append(text)

        return '\n'.join(steps)

    def get_recipe_servings(self, meal):
        """
        Get the servings for this recipe
        :param meal: the meal object
        """
        soup = self._recipe_soup or self._rp.fetch_page(meal.recipe_url)

        # V1: dedicated servings element (e.g. "# of servings <span>1</span>")
        try:
            return soup.find("div", class_="fmc_nos").find("span").get_text(strip=True)
        except (AttributeError, TypeError):
            pass

        # V2: servings element (e.g. "3 Servings")
        servings_div = soup.find("div", class_="fmc_ing_servings")
        if servings_div:
            m = re.search(r'(\d+)', servings_div.get_text(strip=True))
            if m:
                return m.group(1)

        # V1 alternate: "Ingredients for X servings" heading
        for heading in soup.find_all(['h3', 'h4']):
            m = re.search(r'ingredients?\s+for\s+(\d+)\s+serving', heading.get_text(strip=True), re.IGNORECASE)
            if m:
                return m.group(1)

        print("Couldn't find number of servings")
        return None

    def get_serving_size_and_unit(self, meal):
        """
        Get the serving size and unit
        :param meal: the meal object
        """
        soup = self._recipe_soup or self._rp.fetch_page(meal.recipe_url)
        try:
            serving_size = soup.find("div", class_="fmc_ss").find("span").get_text(strip=True)
            serving_size, serving_unit = re.search(r'\d+', serving_size).group(0), re.search(r'[A-Za-z]+', serving_size).group(0)
        except (AttributeError, TypeError):
            print("Couldn't find serving size")
            serving_size, serving_unit = None, None
        return serving_size, serving_unit