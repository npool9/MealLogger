class Ingredient(object):
    """
    Ingredient object definition
    """

    def __init__(
        self,
        id=None,
        name=None,
        calories_per_gram=None,
        protein_per_gram=None,
        carbs_per_gram=None,
        fat_per_gram=None,
        fiber_per_gram=None,
        sugar_per_gram=None,
        saturated_fat_per_gram=None,
        trans_fat_per_gram=None,
        cholesterol_per_gram=None,
        sodium_per_gram=None,
        potassium_per_gram=None,
        calcium_per_gram=None,
        iron_per_gram=None,
        vitamin_a_per_gram=None,
        vitamin_c_per_gram=None,
        vitamin_d_per_gram=None,
        # Transient fields (not stored in ingredients table, used for bridge table)
        amount=None,
        unit=None,
        amount_grams=None,
        notes=None
    ):
        self._id = id
        self._name = name
        self._calories_per_gram = calories_per_gram
        self._protein_per_gram = protein_per_gram
        self._carbs_per_gram = carbs_per_gram
        self._fat_per_gram = fat_per_gram
        self._fiber_per_gram = fiber_per_gram
        self._sugar_per_gram = sugar_per_gram
        self._saturated_fat_per_gram = saturated_fat_per_gram
        self._trans_fat_per_gram = trans_fat_per_gram
        self._cholesterol_per_gram = cholesterol_per_gram
        self._sodium_per_gram = sodium_per_gram
        self._potassium_per_gram = potassium_per_gram
        self._calcium_per_gram = calcium_per_gram
        self._iron_per_gram = iron_per_gram
        self._vitamin_a_per_gram = vitamin_a_per_gram
        self._vitamin_c_per_gram = vitamin_c_per_gram
        self._vitamin_d_per_gram = vitamin_d_per_gram
        # Transient fields
        self.amount = amount
        self.unit = unit
        self.amount_grams = amount_grams
        self.notes = notes

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def calories_per_gram(self):
        return self._calories_per_gram

    @calories_per_gram.setter
    def calories_per_gram(self, value):
        self._calories_per_gram = value

    @property
    def protein_per_gram(self):
        return self._protein_per_gram

    @protein_per_gram.setter
    def protein_per_gram(self, value):
        self._protein_per_gram = value

    @property
    def carbs_per_gram(self):
        return self._carbs_per_gram

    @carbs_per_gram.setter
    def carbs_per_gram(self, value):
        self._carbs_per_gram = value

    @property
    def fat_per_gram(self):
        return self._fat_per_gram

    @fat_per_gram.setter
    def fat_per_gram(self, value):
        self._fat_per_gram = value

    @property
    def fiber_per_gram(self):
        return self._fiber_per_gram

    @fiber_per_gram.setter
    def fiber_per_gram(self, value):
        self._fiber_per_gram = value

    @property
    def sugar_per_gram(self):
        return self._sugar_per_gram

    @sugar_per_gram.setter
    def sugar_per_gram(self, value):
        self._sugar_per_gram = value

    @property
    def saturated_fat_per_gram(self):
        return self._saturated_fat_per_gram

    @saturated_fat_per_gram.setter
    def saturated_fat_per_gram(self, value):
        self._saturated_fat_per_gram = value

    @property
    def trans_fat_per_gram(self):
        return self._trans_fat_per_gram

    @trans_fat_per_gram.setter
    def trans_fat_per_gram(self, value):
        self._trans_fat_per_gram = value

    @property
    def cholesterol_per_gram(self):
        return self._cholesterol_per_gram

    @cholesterol_per_gram.setter
    def cholesterol_per_gram(self, value):
        self._cholesterol_per_gram = value

    @property
    def sodium_per_gram(self):
        return self._sodium_per_gram

    @sodium_per_gram.setter
    def sodium_per_gram(self, value):
        self._sodium_per_gram = value

    @property
    def potassium_per_gram(self):
        return self._potassium_per_gram

    @potassium_per_gram.setter
    def potassium_per_gram(self, value):
        self._potassium_per_gram = value

    @property
    def calcium_per_gram(self):
        return self._calcium_per_gram

    @calcium_per_gram.setter
    def calcium_per_gram(self, value):
        self._calcium_per_gram = value

    @property
    def iron_per_gram(self):
        return self._iron_per_gram

    @iron_per_gram.setter
    def iron_per_gram(self, value):
        self._iron_per_gram = value

    @property
    def vitamin_a_per_gram(self):
        return self._vitamin_a_per_gram

    @vitamin_a_per_gram.setter
    def vitamin_a_per_gram(self, value):
        self._vitamin_a_per_gram = value

    @property
    def vitamin_c_per_gram(self):
        return self._vitamin_c_per_gram

    @vitamin_c_per_gram.setter
    def vitamin_c_per_gram(self, value):
        self._vitamin_c_per_gram = value

    @property
    def vitamin_d_per_gram(self):
        return self._vitamin_d_per_gram

    @vitamin_d_per_gram.setter
    def vitamin_d_per_gram(self, value):
        self._vitamin_d_per_gram = value

    def describe(self):
        """Print all ingredient properties in a readable format"""
        print(f"\n--- {self.name} ---")
        print(f"  Calories:       {self.calories_per_gram}kcal")
        print(f"  Protein:        {self.protein_per_gram}g")
        print(f"  Carbs:          {self.carbs_per_gram}g")
        print(f"  Fat:            {self.fat_per_gram}g")
        print(f"  Fiber:          {self.fiber_per_gram}g")
        print(f"  Sugar:          {self.sugar_per_gram}g")
        print(f"  Saturated Fat:  {self.saturated_fat_per_gram}g")
        print(f"  Trans Fat:      {self.trans_fat_per_gram}g")
        print(f"  Cholesterol:    {self.cholesterol_per_gram}g")
        print(f"  Sodium:         {self.sodium_per_gram}g")
        print(f"  Potassium:      {self.potassium_per_gram}g")
        print(f"  Calcium:        {self.calcium_per_gram}g")
        print(f"  Iron:           {self.iron_per_gram}g")
        print(f"  Vitamin A:      {self.vitamin_a_per_gram}g")
        print(f"  Vitamin C:      {self.vitamin_c_per_gram}g")
        print(f"  Vitamin D:      {self.vitamin_d_per_gram}g")
        print("-------------------\n")
