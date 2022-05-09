

class Meal:
    """
    A meal object
    """

    def __init__(self, meal_key=None, meal_name=None, calories=None, carbs=None, fat=None, protein=None,
        sugar=None, fiber=None, sodium=None, website_name=None, recipe_url=None):
        """
        Initialize the meal object
        """
        self._meal_key = meal_key
        self._meal_name = meal_name
        self._calories = calories
        self._carbs = carbs
        self._fat = fat
        self._protein = protein
        self._sugar = sugar
        self._fiber = fiber
        self._sodium = sodium
        self._website_name = website_name
        self._recipe_url = recipe_url
