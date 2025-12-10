from recipe_search import RecipeSearch
from recipe_parser import RecipeParser
import requests
from bs4 import BeautifulSoup
import re


class FitMenCook(RecipeSearch):
    """
    Inherits properties and functions from RecipeSearch class
    Utilities for navigating and retrieving data from the FitMenCook recipe website
    """

    def __init__(self, meal):
        """
        Initialize utilities for FitMenCook website navigation
        :param meal: the initialized meal object -- mostly null attributes
        """
        super().__init__(meal)
        self._name = "FitMenCook"
        self._base_url = "https://fitmencook.com/"
        self._search_url = self._base_url + "?s="
        self._rp = RecipeParser()

    def search_for_meal(self):
        """
        Search for the meal name on the FitMenCook website
        :return: the url to the recipe (str)
        """
        search_url = self._search_url + self.meal_name.replace(' ', '+')
        r = requests.get(search_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        recipe_element = soup.find("figure", class_="fmc_grid_figure")
        recipe_url = recipe_element.find("a")["href"]

        r = requests.get(recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        self.meal.name = soup.find("h1", class_="fmc_title_1 title_spacing_3").get_text(strip=True)
        return recipe_url

    def get_ingredients(self, meal):
        """
        Get list of ingredients
        :parameter meal: the (mostly) empty meal object
        :return: list of ingredients for the recipe with measurements (list of str)
        """
        recipe_url = self.search_for_meal()
        meal.recipe_url = recipe_url
        meal.website_name = self._name
        ingredients = self._rp.parse_recipe_url(recipe_url)
        return ingredients

    def get_recipe_steps(self, meal):
        """
        Get the description of the given recipe
        :param meal: the meal object
        """
        r = requests.get(meal.recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        # --------------------------------------------------
        # 1. Try JSON-LD (the most reliable format)
        # --------------------------------------------------
        steps = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string.strip())
            except Exception:
                continue
            # Flatten lists
            def walk(obj):
                if isinstance(obj, list):
                    for item in obj:
                        yield from walk(item)
                elif isinstance(obj, dict):
                    yield obj
                    for v in obj.values():
                        yield from walk(v)
            for node in walk(data):
                if isinstance(node, dict) and node.get("@type", "").lower() == "recipe":
                    instr = node.get("recipeInstructions")
                    if instr:
                        # recipeInstructions may be:
                        # 1) list of steps (HowToStep objects)
                        # 2) single long string
                        if isinstance(instr, list):
                            for step in instr:
                                if isinstance(step, dict) and "text" in step:
                                    steps.append(step["text"].strip())
                                elif isinstance(step, str):
                                    steps.append(step.strip())
                        elif isinstance(instr, str):
                            # Break into lines
                            steps.extend([s.strip() for s in instr.split("\n") if s.strip()])
                    if steps:
                        return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        # --------------------------------------------------
        # 2. Fallback: Find instructions section by heading
        # --------------------------------------------------
        heading_regex = re.compile(r"(instruction|direction|method|how to)", re.I)
        # Find headings that look like "Instructions"
        candidate_headings = []
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"]:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(strip=True).lower()
                if heading_regex.search(text):
                    candidate_headings.append(tag)
        # If no headings found, fallback to any block with numbered steps
        if not candidate_headings:
            paragraphs = soup.find_all(["p", "li"])
            for elem in paragraphs:
                t = elem.get_text(" ", strip=True)
                if re.match(r"^\d+[\).]", t):  # "1.) Step text"
                    steps.append(t)
            if steps:
                return "\n".join(steps)
        # --------------------------------------------------
        # 3. Extract text after the heading until next major section
        # --------------------------------------------------
        for head in candidate_headings:
            for sibling in head.find_all_next():
                # Stop if we hit another major section
                if sibling.name in ["h1", "h2", "h3"] and sibling != head:
                    break
                # Collect list items
                if sibling.name in ["ol", "ul"]:
                    for li in sibling.find_all("li"):
                        t = li.get_text(" ", strip=True)
                        if t and len(t) < 500:
                            steps.append(t)
                    break
                # Collect paragraph-style steps
                if sibling.name == "p":
                    t = sibling.get_text(" ", strip=True)
                    if re.search(r"\d", t) and len(t) < 500:
                        steps.append(t)
            if steps:
                break
        # --------------------------------------------------
        # 4. Format output
        # --------------------------------------------------
        steps = [s.strip() for s in steps if s.strip()]
        if not steps:
            return ""
        # Add numbering if missing
        output = []
        for i, step in enumerate(steps, 1):
            if re.match(r"^\d+\.", step):
                output.append(step)
            else:
                output.append(f"{i}. {step}")
        return "\n".join(output)

    def get_recipe_servings(self, meal):
        """
        Get the servings for this recipep
        :param meal: the meal object
        """
        r = requests.get(meal.recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        try:
            n_servings = soup.find("div", class_="fmc_nos").find("span").get_text(strip=True)
        except:
            print("Couldn't find number of servings")
            n_servings = None
        return n_servings

    def get_serving_size_and_unit(self, meal):
        """
        Get the serving size and unit
        :param meal: the meal object
        """
        r = requests.get(meal.recipe_url, timeout=15)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        try:
            serving_size = soup.find("div", class_="fmc_ss").find("span").get_text(strip=True)
            serving_size, serving_unit = re.search(r'\d+', serving_size).group(0), re.search(r'[A-Za-z]', serving_size).group(0)
        except:
            print("Couldn't find serving size")
            serving_size, serving_unit = None, None
        return serving_size, serving_unit