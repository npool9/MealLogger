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
        # units that can act as descriptors at the end of a listed ingredient
        self._valid_descriptor_units = json.load(open("units/descriptor_units.json"))
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
        unit = self.find_unit(unparsed_ingredient)
        print(str(unit) + ':', unparsed_ingredient)

    def find_unit(self, unparsed_ingredient):
        """
        Find the unit in the full ingredient
        :param unparsed_ingredient: the full ingredient of the recipe
        :return: the unit (str), None if no unit
        """
        # search for valid unit
        unit_found = False
        descriptor_unit_found = False
        # unit_formats = [surround_by_spaces, in_parentheses]
        for key in self._valid_units:
            for unit in self._valid_units[key]:
                if self.surround_by_spaces(unit, unparsed_ingredient) or self.in_parentheses(unit, unparsed_ingredient):
                    return key  # the parent unit
        for key in self._valid_descriptor_units:
            for unit in self._valid_descriptor_units[key]:
                if unparsed_ingredient.endswith(unit):
                    return key  # the parent descriptor unit
        return None

    def surround_by_spaces(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit is surrounded by spaces
        :param unit: a valid unit
        :param unparsed_ingredient: the full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\d*\s" + unit + "\s", unparsed_ingredient)

    def in_parentheses(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit in parentheses next to the amount
        :param unit: a valid unit
        :param unparsed_ingredient: the full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\(~?\d*" + unit + "\)", unparsed_ingredient)
