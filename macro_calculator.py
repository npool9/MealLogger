# TODO; pass everything through the ingredient parser
class MacroCalculator:
    """
    Functions to calculate the macros of a meal
    """

    def __init__(self, ingredients):
        """
        Initialize the macro calculator
        :param ingredients: list of ingredient and their measurements (as str)
        """
        self._ingredients = ingredients


if __name__ == "__main__":
    test_list = ["1/2 cup of skim milk", "3 large eggs", "1 potato", "2 tablespoons of frank's red hot sauce"]
    calculator = MacroCalculator(test_list)
