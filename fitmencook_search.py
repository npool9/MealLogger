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

    def search_for_meal(self):
        """
        Search for the meal name on the FitMenCook website
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        r = requests.get(search_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        recipe_element = soup.find("figure", class_="fmc_grid_figure")
        recipe_url = recipe_element.find("a")["href"]

        r = requests.get(recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        self.meal.name = soup.find("h1", class_="fmc_title_1 title_spacing_3").get_text(strip=True)
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
        ingredients = self._rp.parse_recipe_from_url(recipe_url)
        print(ingredients)
        return ingredients

    def get_recipe_steps(self, meal):
        """
        Get the description of the given recipe
        :param meal: the meal object
        """
        rp = RecipeParser()
        rec = rp.get_recipe_jsonld(meal.recipe_url)
        instructions = []
        if "recipeInstructions" in rec:
            instructions = rec["recipeInstructions"]
        return '\n'.join(instructions)

    def get_recipe_servings(self, meal):
        """
        Get the servings for this recipep
        :param meal: the meal object
        """
        r = requests.get(meal.recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        try:
            n_servings = soup.find("div", class_="fmc_nos").find("span").get_text(strip=True)
        except:
            print("Couldn't find number of servings")
            n_servings = None
        return n_servings

    def get_serving_size_and_unit(self, meal):
        """
        Get the serving size and unit
        :param meal: the meal object
        """
        r = requests.get(meal.recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        try:
            serving_size = soup.find("div", class_="fmc_ss").find("span").get_text(strip=True)
            serving_size, serving_unit = re.search(r'\d+', serving_size).group(0), re.search(r'[A-Za-z]', serving_size).group(0)
        except:
            print("Couldn't find serving size")
            serving_size, serving_unit = None, None
        return serving_size, serving_unit