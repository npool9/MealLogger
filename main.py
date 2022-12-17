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
        self._view = View()
        self._model = Model()


def run():
    """
    The runner function to kick off the application and control it
    """
    meal_logger = MealLogger()
    meal_name = meal_logger._view.ask_for_meal()
    meal, exists = meal_logger._model.check_for_meal(meal_name)
    print("Meal:", meal)
    if not exists:
        # Get list of ingredients from a website
        print("Meal does not exist")
        print("Searching for meal...")
        meal.meal_name = meal_name
        ingredient_list = meal_logger._model.find_meal(meal)
        print("Found ingredients list")
        # TODO
        print("Building meal object...")
        meal_logger._model.build_meal(meal, ingredient_list)
    else:  # meal exists
        print("Meal exists")
        pass


if __name__ == "__main__":
    run()
