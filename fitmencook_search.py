from recipe_search import RecipeSearch
from recipe_parser import RecipeParser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
        :param meal_name: the name of the meal (str)
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        self._driver.get(search_url)
        try:
            WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@class=\"fmc_grid_figure\"]"))
            )
        except:
            self._driver.quit()
            raise Exception("Recipe results did not load")
        recipe_element = self._driver.find_element(By.XPATH, '//*[@class="fmc_grid_figure"]')
        recipe_element.click()  # click on first element result
        print("Clicked on recipe")
        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@class=\"fmc_title_1 title_spacing_3\"]"))
            )
        except:
            self._driver.quit()
            raise Exception("Recipe results did not load")
        # replace meal name with full, official name
        self.meal._meal_name = self._driver.find_element(By.XPATH, '//*[@class="fmc_title_1 title_spacing_3"]').text
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
        ingredients = self._rp.parse_recipe_url(recipe_url)
        # ingredient_list_element = self._driver.find_element(By.XPATH, '//*[@class="fmc_ingredients"]/ul')
        # ingredients = ingredient_list_element.find_elements(By.XPATH, "li")
        # ingredients = [ingredient.text for ingredient in ingredients]
        return ingredients
