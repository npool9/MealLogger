import re
import json


# TODO
class IngredientParser:
    """
    A tool for parsing an ingredient for its name and its measurement
    """

    def __init__(self):
        """
        Initialize the ingredient parser
        """
        self._valid_units = json.load(open("units/units.json"))
        print(self._valid_units)
        self._ingredient = None
        self._unit = None
        self._amount = 0

    def parse(self, unparsed_ingredient):
        """
        Parse the full ingredient into its informative parts (ingredient, unit, amount)
        :param unparsed_ingredient: the unparsed ingredient of the recipe
            e.g. 4 tablespoons olive oil
        Good luck!
        """
        pass

    def find_unit(self, unparsed_ingrdient):
        """
        Find the unit in the full ingredient
        :param unparsed_ingredient: the full ingredient of the recipe
        """
        pass
