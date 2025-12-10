

class Meal(object):
    """
    A meal object
    """

    def __init__(self, id=None, name=None, description=None, servings=None, serving_size=None, serving_unit=None,
                 recipe_url=None, created_at=None):
        """
        Initialize the meal object
        """
        self._id = id
        self._name = name
        self._description = description
        self._servings = servings
        self._serving_size = serving_size
        self._serving_unit = serving_unit
        self._recipe_url = recipe_url
        self._created_at = created_at

    def describe(self):
        """
        Describe the meal object by printing out the details to the console
        """
        print("Meal ID:", self._id)
        print("Meal Name:", self._name)
        print("Description:", self._description)
        print("Servings:", self._servings)
        print("Serving Size:", self._serving_size)
        print("Serving Unit:", self._serving_unit)
        print("Recipe URL:", self._recipe_url)
        print("Created At:", self._created_at)

    @property
    def id(self):
        """
        Get the meal key value
        """
        return self._id

    @id.setter
    def id(self, id):
        """
        Set the meal key
        :parameter meal_key: the new meal key
        """
        self._id = id

    @property
    def name(self):
        """
        Get the meal name value
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        Set the meal name
        :parameter name: the new meal name
        """
        self._name = name

    @property
    def description(self):
        """
        Get the description
        """
        return self._description

    @description.setter
    def description(self, description):
        """
        Set the website name
        :parameter website_name: the new website name
        """
        self._description = description

    @property
    def servings(self):
        """
        Get the servings value
        """
        return self._servings

    @servings.setter
    def servings(self, servings):
        """
        Set the servings value
        """
        self._servings = servings

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
        :parameter recipe_url: the new recipe url
        """
        self._recipe_url = recipe_url

    @property
    def serving_size(self):
        """
        Get the serving size
        """
        return self._serving_size

    @serving_size.setter
    def serving_size(self, serving_size):
        """
        Set the serving size
        """
        self._serving_size = serving_size

    @property
    def serving_unit(self):
        """
        Get the serving unit
        """
        return self._serving_unit

    @serving_unit.setter
    def serving_unit(self, serving_unit):
        """
        Set the serving unit
        """
        self._serving_unit = serving_unit

    @property
    def created_at(self):
        """
        Get the created_at value
        """
        return self._created_at

    @created_at.setter
    def created_at(self, created_at):
        """
        Set the created_at
        :parameter created_at: the new created_at
        """
        self._created_at = created_at