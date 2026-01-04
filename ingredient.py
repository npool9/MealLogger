class Ingredient(object):
    """
    Ingredient object definition
    """

    def __init__(
        self,
        id=None,
        name=None,
        calories_per_unit=None,
        protein_per_unit=None,
        carbs_per_unit=None,
        fat_per_unit=None,
        fiber_per_unit=None,
        sugar_per_unit=None,
        saturated_fat_per_unit=None,
        trans_fat_per_unit=None,
        cholesterol_mg_per_unit=None,
        sodium_mg_per_unit=None,
        potassium_mg_per_unit=None,
        calcium_mg_per_unit=None,
        iron_mg_per_unit=None,
        vitamin_a_ug_per_unit=None,
        vitamin_c_mg_per_unit=None,
        vitamin_d_ug_per_unit=None,
        default_unit=None,
    ):
        self._id = id
        self._name = name
        self._calories_per_unit = calories_per_unit
        self._protein_per_unit = protein_per_unit
        self._carbs_per_unit = carbs_per_unit
        self._fat_per_unit = fat_per_unit
        self._fiber_per_unit = fiber_per_unit
        self._sugar_per_unit = sugar_per_unit
        self._saturated_fat_per_unit = saturated_fat_per_unit
        self._trans_fat_per_unit = trans_fat_per_unit
        self._cholesterol_mg_per_unit = cholesterol_mg_per_unit
        self._sodium_mg_per_unit = sodium_mg_per_unit
        self._potassium_mg_per_unit = potassium_mg_per_unit
        self._calcium_mg_per_unit = calcium_mg_per_unit
        self._iron_mg_per_unit = iron_mg_per_unit
        self._vitamin_a_ug_per_unit = vitamin_a_ug_per_unit
        self._vitamin_c_mg_per_unit = vitamin_c_mg_per_unit
        self._vitamin_d_ug_per_unit = vitamin_d_ug_per_unit
        self._default_unit = default_unit

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
    def calories_per_unit(self):
        return self._calories_per_unit

    @calories_per_unit.setter
    def calories_per_unit(self, value):
        self._calories_per_unit = value

    @property
    def protein_per_unit(self):
        return self._protein_per_unit

    @protein_per_unit.setter
    def protein_per_unit(self, value):
        self._protein_per_unit = value

    @property
    def carbs_per_unit(self):
        return self._carbs_per_unit

    @carbs_per_unit.setter
    def carbs_per_unit(self, value):
        self._carbs_per_unit = value

    @property
    def fat_per_unit(self):
        return self._fat_per_unit

    @fat_per_unit.setter
    def fat_per_unit(self, value):
        self._fat_per_unit = value

    @property
    def fiber_per_unit(self):
        return self._fiber_per_unit

    @fiber_per_unit.setter
    def fiber_per_unit(self, value):
        self._fiber_per_unit = value

    @property
    def sugar_per_unit(self):
        return self._sugar_per_unit

    @sugar_per_unit.setter
    def sugar_per_unit(self, value):
        self._sugar_per_unit = value

    @property
    def saturated_fat_per_unit(self):
        return self._saturated_fat_per_unit

    @saturated_fat_per_unit.setter
    def saturated_fat_per_unit(self, value):
        self._saturated_fat_per_unit = value

    @property
    def trans_fat_per_unit(self):
        return self._trans_fat_per_unit

    @trans_fat_per_unit.setter
    def trans_fat_per_unit(self, value):
        self._trans_fat_per_unit = value

    @property
    def cholesterol_mg_per_unit(self):
        return self._cholesterol_mg_per_unit

    @cholesterol_mg_per_unit.setter
    def cholesterol_mg_per_unit(self, value):
        self._cholesterol_mg_per_unit = value

    @property
    def sodium_mg_per_unit(self):
        return self._sodium_mg_per_unit

    @sodium_mg_per_unit.setter
    def sodium_mg_per_unit(self, value):
        self._sodium_mg_per_unit = value

    @property
    def potassium_mg_per_unit(self):
        return self._potassium_mg_per_unit

    @potassium_mg_per_unit.setter
    def potassium_mg_per_unit(self, value):
        self._potassium_mg_per_unit = value

    @property
    def calcium_mg_per_unit(self):
        return self._calcium_mg_per_unit

    @calcium_mg_per_unit.setter
    def calcium_mg_per_unit(self, value):
        self._calcium_mg_per_unit = value

    @property
    def iron_mg_per_unit(self):
        return self._iron_mg_per_unit

    @iron_mg_per_unit.setter
    def iron_mg_per_unit(self, value):
        self._iron_mg_per_unit = value

    @property
    def vitamin_a_ug_per_unit(self):
        return self._vitamin_a_ug_per_unit

    @vitamin_a_ug_per_unit.setter
    def vitamin_a_ug_per_unit(self, value):
        self._vitamin_a_ug_per_unit = value

    @property
    def vitamin_c_mg_per_unit(self):
        return self._vitamin_c_mg_per_unit

    @vitamin_c_mg_per_unit.setter
    def vitamin_c_mg_per_unit(self, value):
        self._vitamin_c_mg_per_unit = value

    @property
    def vitamin_d_ug_per_unit(self):
        return self._vitamin_d_ug_per_unit

    @vitamin_d_ug_per_unit.setter
    def vitamin_d_ug_per_unit(self, value):
        self._vitamin_d_ug_per_unit = value

    @property
    def default_unit(self):
        return self._default_unit

    @default_unit.setter
    def default_unit(self, value):
        self._default_unit = value
