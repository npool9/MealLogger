from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from view import View


class MealLogger:
    """
    The controller of the meal logger
    """

    def __init__(self):
        """
        Initialize the Meal Logger controller
        """
        self._options = Options()
        self._options.headless = True
        self._driver = webdriver.Chrome(options=self._options)
        self._view = View()


if __name__ == "__main__":
    meal_logger = MealLogger()
    meal_name = meal_logger._view.ask_for_meal()
