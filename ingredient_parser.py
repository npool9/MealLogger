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
        :param unparsed_ingredient: one of the unparsed ingredients of the recipe
            e.g. 4 tablespoons olive oil
        Good luck!
        """
        unit, end_ind = self.find_unit(unparsed_ingredient)
        self.find_ingredient(unit, unparsed_ingredient, end_ind)

    def find_unit(self, unparsed_ingredient):
        """
        Find the unit in the full ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: the unit (str) (None if no unit), and the index at which it exists (0 if no unit)
        """
        # search for valid unit
        unit_found = False
        descriptor_unit_found = False
        # unit_formats = [surround_by_spaces, in_parentheses]
        for key in self._valid_units:
            for unit in self._valid_units[key]:
                matches = [self.surround_by_spaces(unit, unparsed_ingredient), self.in_parentheses(unit, unparsed_ingredient), self.right_beside_num(unit, unparsed_ingredient)]
                matches = [m for m in matches if m]  # Get matches
                try:
                    match = matches[0]  # Get first match
                    return key, match.end()  # return the parent unit
                except IndexError:  # no match
                    match = None
        for key in self._valid_descriptor_units:
            for unit in self._valid_descriptor_units[key]:
                if unparsed_ingredient.endswith(unit):
                    return key, len(unparsed_ingredient)  # the parent descriptor unit
        return None, 0

    def find_ingredient(self, unit, unparsed_ingredient, ind):
        """
        Find just the ingredient name in the full, unparsed ingredient
        :param unit: the unit of the ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :param ind: the index of the end of the unit in the unparsed ingredient
        :return: the ingredient
        """
        stop_chars = ['(', ',']
        start_chars = ['(']
        if unit:  # unit found
            ingredient = unparsed_ingredient[ind:].strip()
        else:  # No unit, there will just be a count/amount
            # remove the first word from the ingredient, that is likely the amount
            temp_list = unparsed_ingredient.split(' ')
            first_word = temp_list[0]  # keeping in case we want tot unit test
            ingredient = ' '.join(temp_list[1:])
        # post-processing
        for c in start_chars:
            if ingredient.startswith(c):
                ingredient = ingredient[ingredient.index(')')+1:].strip()
        for c in stop_chars:
            if c in ingredient:
                ingredient = ingredient[:ingredient.rindex(c)]
        print(ingredient)
        return ingredient


    def surround_by_spaces(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit is surrounded by spaces
        :param unit: a valid unit
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\d*\s" + unit + "\s", unparsed_ingredient)

    def in_parentheses(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit in parentheses next to the amount
        :param unit: a valid unit
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\(~?\d*" + unit + "\)", unparsed_ingredient)

    def right_beside_num(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit is right next to the amount number
          e.g. 1lb
        :param unit: a valid unit
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\d+" + unit + "\s", unparsed_ingredient)
