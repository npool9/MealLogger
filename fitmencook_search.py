from recipe_search import RecipeSearch
from selenium.webdriver.common.by import By


class FitMenCook(RecipeSearch):
    """
    Inherits properties and functions from RecipeSearch class
    Utilities for navigating and retrieving data from the FitMenCook recipe website
    """

    def __init__(self, meal_name):
        """
        Initialize utilities for FitMenCook website navigation
        """
        super().__init__(meal_name)
        self._name = "FitMenCook"
        self._base_url = "https://fitmencook.com/"
        self._search_url = self._base_url + "?s="

    def search_for_meal(self):
        """
        Search for the meal name on the FitMenCook website
        :param meal_name: the name of the meal (str)
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        self._driver.get(search_url)
        recipe_element = self._driver.find_element_by_xpath('//*[@class="fit-post"]')
        recipe_element.click()  # click on first element result
        return self._driver.current_url

    def get_ingredients(self, meal):
        """
        Get list of ingredients
        :parameter meal: the (mostly) empty meal object
        :return: list of ingredients for the recipe with measurements (list of str)
        """
        recipe_url = self.search_for_meal()
        meal.recipe_url = recipe_url
        meal.website_name = self._name
        ingredient_list_element = self._driver.find_element_by_xpath('//*[@class="recipe-ingredients gap-bottom-small"]/ul')
        ingredients = ingredient_list_element.find_elements(By.XPATH, "li")
        ingredients = [ingredient.text for ingredient in ingredients]
        return ingredients
