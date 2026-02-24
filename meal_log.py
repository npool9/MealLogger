class MealLog:
    """
    A meal log entry representing when a meal was eaten
    """

    def __init__(self, id=None, meal_id=None, date_eaten=None, servings_consumed=1,
                 calories=None, protein=None, carbs=None, fat=None,
                 fiber=None, sugar=None, saturated_fat=None, trans_fat=None,
                 cholesterol=None, sodium=None, potassium=None, calcium=None,
                 iron=None, vitamin_a=None, vitamin_c=None, vitamin_d=None,
                 created_at=None):
        """
        Initialize the meal log object
        """
        self._id = id
        self._meal_id = meal_id
        self._date_eaten = date_eaten
        self._servings_consumed = servings_consumed
        self._calories = calories
        self._protein = protein
        self._carbs = carbs
        self._fat = fat
        self._fiber = fiber
        self._sugar = sugar
        self._saturated_fat = saturated_fat
        self._trans_fat = trans_fat
        self._cholesterol = cholesterol
        self._sodium = sodium
        self._potassium = potassium
        self._calcium = calcium
        self._iron = iron
        self._vitamin_a = vitamin_a
        self._vitamin_c = vitamin_c
        self._vitamin_d = vitamin_d
        self._created_at = created_at

    def describe(self):
        """
        Describe the meal log entry by printing details to the console
        """
        print(f"Meal Log ID: {self._id}")
        print(f"Meal ID: {self._meal_id}")
        print(f"Date Eaten: {self._date_eaten}")
        print(f"Servings Consumed: {self._servings_consumed}")
        print(f"Calories: {self._calories}")
        print(f"Protein: {self._protein}g")
        print(f"Carbs: {self._carbs}g")
        print(f"Fat: {self._fat}g")
        print(f"Created At: {self._created_at}")

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def meal_id(self):
        return self._meal_id

    @meal_id.setter
    def meal_id(self, value):
        self._meal_id = value

    @property
    def date_eaten(self):
        return self._date_eaten

    @date_eaten.setter
    def date_eaten(self, value):
        self._date_eaten = value

    @property
    def servings_consumed(self):
        return self._servings_consumed

    @servings_consumed.setter
    def servings_consumed(self, value):
        self._servings_consumed = value

    @property
    def calories(self):
        return self._calories

    @calories.setter
    def calories(self, value):
        self._calories = value

    @property
    def protein(self):
        return self._protein

    @protein.setter
    def protein(self, value):
        self._protein = value

    @property
    def carbs(self):
        return self._carbs

    @carbs.setter
    def carbs(self, value):
        self._carbs = value

    @property
    def fat(self):
        return self._fat

    @fat.setter
    def fat(self, value):
        self._fat = value

    @property
    def fiber(self):
        return self._fiber

    @fiber.setter
    def fiber(self, value):
        self._fiber = value

    @property
    def sugar(self):
        return self._sugar

    @sugar.setter
    def sugar(self, value):
        self._sugar = value

    @property
    def saturated_fat(self):
        return self._saturated_fat

    @saturated_fat.setter
    def saturated_fat(self, value):
        self._saturated_fat = value

    @property
    def trans_fat(self):
        return self._trans_fat

    @trans_fat.setter
    def trans_fat(self, value):
        self._trans_fat = value

    @property
    def cholesterol(self):
        return self._cholesterol

    @cholesterol.setter
    def cholesterol(self, value):
        self._cholesterol = value

    @property
    def sodium(self):
        return self._sodium

    @sodium.setter
    def sodium(self, value):
        self._sodium = value

    @property
    def potassium(self):
        return self._potassium

    @potassium.setter
    def potassium(self, value):
        self._potassium = value

    @property
    def calcium(self):
        return self._calcium

    @calcium.setter
    def calcium(self, value):
        self._calcium = value

    @property
    def iron(self):
        return self._iron

    @iron.setter
    def iron(self, value):
        self._iron = value

    @property
    def vitamin_a(self):
        return self._vitamin_a

    @vitamin_a.setter
    def vitamin_a(self, value):
        self._vitamin_a = value

    @property
    def vitamin_c(self):
        return self._vitamin_c

    @vitamin_c.setter
    def vitamin_c(self, value):
        self._vitamin_c = value

    @property
    def vitamin_d(self):
        return self._vitamin_d

    @vitamin_d.setter
    def vitamin_d(self, value):
        self._vitamin_d = value

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value):
        self._created_at = value
