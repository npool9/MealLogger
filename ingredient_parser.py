# TODO
class IngredientParser:
    """
    A tool for parsing an ingredient for its name and its measurement
    """

    def __init__(self):
        """
        Initialize the ingredient parser
        """
        # FIXME: exhaustive list of valid units of measurement (include abbreviations)
        self._valid_units = ["cup", "ounce"]
        self._ingredient = None
        self._unit = None
        self._amount = 0
