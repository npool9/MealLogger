from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from view import View
from model import Model


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
        self._model = Model()


def run():
    """
    The runner function to kick off the application and control it
    """
    meal_logger = MealLogger()
    meal_name = meal_logger._view.ask_for_meal()
    meal = meal_logger._model.check_for_meal(meal_name)
    


if __name__ == "__main__":
    run()
