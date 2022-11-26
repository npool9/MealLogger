from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class RecipeSearch:
    """
    The parent class for all recipe webiste uilities that all recipe websites will inherit from
    """

    def __init__(self, meal):
        """
        Define base urls
        """
        self.meal = meal
        self.meal_name = self.meal._meal_name
        self.base_url = None
        self.search_url = None
        # Webscraping Utilities
        self._options = Options()
        self._options.headless = True
        self._driver = webdriver.Chrome(options=self._options)

    def search_for_meal(self):
        """
        Search for the meal name
        :return: the corresponding recipe url (str)
        """
        pass

    def get_ingredients(self):
        """
        Get a list of ingredients (strings) for the meal provided
        :return: list of ingredients (list of str)
        """
        pass
