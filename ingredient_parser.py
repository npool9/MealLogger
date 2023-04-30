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
        print("Full Ingredient:", unparsed_ingredient)
        ingredient_dict = {"unit": None, "amount": None, "name": None}
        ingredient_dict["unit"], inds, found_unit = self.find_ingredient_unit(unparsed_ingredient)
        start_ind, end_ind = inds
        ingredient_dict["name"] = self.find_ingredient_name(found_unit, unparsed_ingredient, end_ind)
        ingredient_dict["amount"] = self.find_ingredient_amount(found_unit, unparsed_ingredient, start_ind, end_ind)
        # Make sure amount isn't in name
        if ingredient_dict["amount"] + ' ' in ingredient_dict["name"]:
            ingredient_dict["name"] = ingredient_dict["name"].replace(ingredient_dict["amount"] + ' ', '')
        print("Ingredient Dict:", ingredient_dict, '\n')

    def find_ingredient_unit(self, unparsed_ingredient):
        """
        Find the unit in the full ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :return:
            1. the parent unit (str) (None if no unit)
            2. the unit span, tuple of the start and end indices of the unit in the full ingredient string
            3. the found version of the unit (i.e. not the parent unit)
        """
        # search for valid unit
        # unit_formats = [surround_by_spaces, in_parentheses]
        for key in self._valid_units:
            for unit in self._valid_units[key]:
                matches = [self.surround_by_spaces(unit, unparsed_ingredient), self.in_parentheses(unit, unparsed_ingredient), self.right_beside_num(unit, unparsed_ingredient)]
                matches = [m for m in matches if m]  # Get matches
                try:
                    match = matches[0]  # Get first match
                    return key, match.span(1), unit  # return the parent unit is "key"
                except IndexError:  # no match
                    match = None
        for key in self._valid_descriptor_units:
            for unit in self._valid_descriptor_units[key]:
                if unparsed_ingredient.endswith(unit):
                    return key, (len(unparsed_ingredient)-len(unit), len(unparsed_ingredient)), unit  # the parent descriptor unit is "key"
                elif unparsed_ingredient.startswith(unit):
                    return key, (0, len(unit)), unit   # the parent descriptor unit is "key"
        return None, (0, 0), None

    def find_ingredient_name(self, unit, unparsed_ingredient, ind):
        """
        Find just the ingredient name in the full, unparsed ingredient
        :param unit: the unit of the ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :param ind: the index of the end of the unit in the unparsed ingredient
        :return: the ingredient name
        """
        # TODO: this needs to be fixed -- consider "Juice from" scenario
        stop_chars = ['(', ',']
        start_chars = ['(', ')']
        if unit:  # unit found
            ingredient_name = unparsed_ingredient[ind:].strip()
        else:  # No unit, there will just be a count/amount
            # remove the first word from the ingredient, that is likely the amount
            temp_list = unparsed_ingredient.split(' ')
            first_word = temp_list[0]  # keeping in case we want tot unit test
            ingredient_name = ' '.join(temp_list[1:])
        # post-processing
        for c in start_chars:
            if ingredient_name.startswith(c):
                ingredient_name = ingredient_name[ingredient_name.index(')')+1:].strip()
        for c in stop_chars:
            if c in ingredient_name:
                ingredient_name = ingredient_name[:ingredient_name.rindex(c)]
        # Last ditch effort to get ingredient name
        # Examples: "... to taste", etc.
        if not ingredient_name.strip() and unit in self._valid_descriptor_units:
            ingredient_name = unparsed_ingredient.replace(unit, '')
        return ingredient_name.strip()

    def find_ingredient_amount(self, unit, unparsed_ingredient, start_ind, end_ind):
        """
        Find the ingredient amount in the full, unparsed ingredient
        :param unit: the unit of the ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :param start_ind: the index of the start of the unit in the unparsed ingredient
        :param end_ind: the index of the end of the unit in the unparsed ingredient
        :return: the ingredient amount
        """
        # If no number anywhere in ingredient, return 1
        if not self.check_for_number(unparsed_ingredient):
            return str(1)
        if unit:
            # Look immediately adjacent to the unit
            # print("Unit indices:", (start_ind, end_ind))
            left = unparsed_ingredient[:start_ind].strip().split(' ')
            right = unparsed_ingredient[end_ind:].strip().split(' ')
            left = ' '.join(left[-2:])
            right = ' '.join(right[:2])
            if self.check_for_number(left):
                # print("Left:", left)
                ingredient_amount = left
            else:
                # print("Right:", right)
                ingredient_amount = right
        else:
            # print("No unit for this one:", unparsed_ingredient)
            # Get first word
            ingredient_amount = unparsed_ingredient.split(' ')[0]
        match = self.parse_for_amount(ingredient_amount)
        if match:
            # print("Found amount " + str(match.group()) + ": " + unparsed_ingredient)
            return match.group()
        else:
            print("Unit:", unit)
            raise Exception("Could not find ingredient amount: ", unparsed_ingredient)


    def surround_by_spaces(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit is surrounded by spaces
        :param unit: a valid unit
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\d*\s(" + unit + ")\s", unparsed_ingredient)

    def in_parentheses(self, unit, unparsed_ingredient):
        """
        Units can be formatted in a variety of ways in a recipe
        This one checks to see if the unit in parentheses next to the amount
        :param unit: a valid unit
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        unit = unit.replace('.', "\.")
        return re.search("\(~?\d*\.?\d*\s?(" + unit + ")\)", unparsed_ingredient)

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
        return re.search("\d+(" + unit + ")\s", unparsed_ingredient)

    def parse_for_amount(self, parsed_ingredient):
        """
        The RegEx for parsing the amount from an abridged version of the full ingredient
        :param parsed_ingredient: the ingredient but some unnecessary info has been removed
        :return: a match object for the regular expression
        """
        return re.search("(\d+)?\s?\d+\/?\.?\d*", parsed_ingredient)

    def check_for_number(self, unparsed_ingredient):
        """
        Check for the existence of any number in the full ingredient
        :param unparsed_ingredient: a full ingredient of the recipe
        :return: a match object for the regular expression
        """
        return re.search("\d+", unparsed_ingredient)
