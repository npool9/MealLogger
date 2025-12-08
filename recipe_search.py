from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class RecipeSearch:
    """
    The parent class for all recipe website utilities that all recipe websites will inherit from
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
        self._driver = self.get_headless_driver(headless=False)

    def get_headless_driver(self, headless=True):
        options = Options()
        if headless:
            options.headless = True
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

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
