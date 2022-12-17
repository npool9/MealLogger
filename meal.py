

class Meal(object):
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

    def describe(self):
        """
        Describe the meal object by printing out the details to the console
        """
        print("Meal Key:", self._meal_key)
        print("Meal Name:", self._meal_name)
        print("Calories:", self._calories)
        print("Carbs:", self._carbs)
        print("Fat:", self._fat)
        print("Protein:", self._protein)
        print("Sugar:", self._sugar)
        print("Fiber:", self._fiber)
        print("Sodium:", self._sodium)
        print("Website Name:", self._website_name)
        print("Recipe URL:", self._recipe_url)

    @property
    def meal_key(self):
        """
        Get the meal key value
        """
        return self._meal_key

    @meal_key.setter
    def meal_key(self, meal_key):
        """
        Set the meal key
        :parameter meal_key: the new meal key
        """
        self._meal_key = meal_key

    @property
    def meal_name(self):
        """
        Get the meal name value
        """
        return self._meal_name

    @meal_name.setter
    def meal_name(self, meal_name):
        """
        Set the meal name
        :parameter meal_name: the new meal naame
        """
        self._meal_name = meal_name

    @property
    def calories(self):
        """
        Get the calories value
        """
        return self._calories

    @calories.setter
    def calories(self, calories):
        """
        Set the calories
        :parameter calories: the new calorie measurement
        """
        self._calories = calories

    @property
    def carbs(self):
        """
        Get the carbs value
        """
        return self._carbs

    @calories.setter
    def calories(self, carbs):
        """
        Set the carbs
        :parameter carbs: the new carbs measurement
        """
        self._carbs = carbs

    @property
    def fat(self):
        """
        Get the fat value
        """
        return self._fat

    @fat.setter
    def fat(self, fat):
        """
        Set the fat
        :parameter fat: the new fat measurement
        """
        self._fat = fat

    @property
    def protein(self):
        """
        Get the protein value
        """
        return self._protein

    @protein.setter
    def protein(self, protein):
        """
        Set the protein
        :parameter protein: the new protein measurement
        """
        self._protein = protein

    @property
    def sugar(self):
        """
        Get the sugar value
        """
        return self._sugar

    @sugar.setter
    def sugar(self, sugar):
        """
        Set the sugar
        :parameter sugar: the new sugar measurement
        """
        self._sugar = sugar

    @property
    def fiber(self):
        """
        Get the fiber value
        """
        return self._fiber

    @fiber.setter
    def fiber(self, fiber):
        """
        Set the fiber
        :parameter fiber: the new fiber measurement
        """
        self._fiber = fiber

    @property
    def sodium(self):
        """
        Get the sodium value
        """
        return self._sodium

    @sodium.setter
    def sodium(self, sodium):
        """
        Set the sodium
        :parameter sodium: the new sodium measurement
        """
        self._sodium = sodium

    @property
    def website_name(self):
        """
        Get the website name value
        """
        return self._website_name

    @website_name.setter
    def website_name(self, website_name):
        """
        Set the website name
        :parameter website_name: the new website name
        """
        self._website_name = website_name

    @property
    def recipe_url(self):
        """
        Get the recipe url value
        """
        return self._recipe_url

    @recipe_url.setter
    def recipe_url(self, recipe_url):
        """
        Set the recipe url
        :parameter website_name: the new recipe url
        """
        self._recipe_url = recipe_url
