

class Meal:
    """
    A meal object
    """

    def __init__(self, meal_key, meal_name, calories, carbs, fat, protein,
        sugar, fiber, sodium, website_name, recip_url):
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
