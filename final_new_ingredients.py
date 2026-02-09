#!/usr/bin/env python3
"""
Filter out duplicates and generate final list of new ingredients.
"""

import sys
sys.path.insert(0, '/Users/nathanpool/Documents/Hobbies/Programming/PythonProjects/MealLogger')

from usda_service import INGREDIENT_GRAMS_PER_CUP as existing
from new_ingredients_for_grams_per_cup import NEW_INGREDIENTS

# Find truly new ingredients
new_only = {}
for key, value in NEW_INGREDIENTS.items():
    if key not in existing:
        new_only[key] = value

print(f"Existing ingredients: {len(existing)}")
print(f"New ingredients found: {len(NEW_INGREDIENTS)}")
print(f"Truly new (not duplicates): {len(new_only)}")
print("\n" + "="*80)
print("FINAL LIST - ADD TO INGREDIENT_GRAMS_PER_CUP:")
print("="*80 + "\n")

# Group by category for readability
categories = {
    "CANNED FRUITS": [],
    "CANNED VEGETABLES": [],
    "FROZEN VEGETABLES": [],
    "FROZEN FRUITS": [],
    "ASIAN INGREDIENTS": [],
    "BEAN SPROUTS": [],
    "LATIN INGREDIENTS": [],
    "EUROPEAN CHEESES": [],
    "CONDIMENTS & SAUCES": [],
    "SPREADS & BUTTERS": [],
    "CANNED PROTEINS": [],
    "CANNED BEANS": [],
    "SOUPS & BROTHS": [],
    "BEVERAGES": [],
    "PREPARED FOODS": [],
    "GRAVIES": [],
    "DAIRY": [],
    "DESSERTS": [],
    "CEREALS & GRAINS": [],
    "OILS": [],
    "BAKING": [],
    "SNACKS": [],
    "MISCELLANEOUS": [],
}

for key, value in sorted(new_only.items()):
    categorized = False
    k = key.lower()

    if "canned" in k and ("fruit" in k or "peach" in k or "pear" in k or "pineapple" in k or "tangerine" in k or "cherry" in k or "fig" in k):
        categories["CANNED FRUITS"].append((key, value))
        categorized = True
    elif "canned" in k and ("vegetable" not in k and "soup" not in k and "bean" not in k and "chili" not in k and "chicken" not in k and "sardine" not in k and "tuna" not in k):
        categories["CANNED VEGETABLES"].append((key, value))
        categorized = True
    elif "frozen" in k and ("vegetable" in k or "spinach" in k or "broccoli" in k or "corn" in k or "peas" in k or "succotash" in k or "beans, snap" in k):
        categories["FROZEN VEGETABLES"].append((key, value))
        categorized = True
    elif "frozen" in k and ("berr" in k or "peach" in k or "mango" in k or "fruit" in k):
        categories["FROZEN FRUITS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["noodles", "soy sauce", "seaweed", "shiitake", "enoki", "cloud ear", "kimchi", "pak-choi", "pe-tsai", "napa", "wasabi", "vermicelli", "coconut cream", "miso"]):
        categories["ASIAN INGREDIENTS"].append((key, value))
        categorized = True
    elif "sprouted" in k:
        categories["BEAN SPROUTS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["queso", "masa", "refried", "salsa", "enchilada", "mexican", "latino", "on the border"]):
        categories["LATIN INGREDIENTS"].append((key, value))
        categorized = True
    elif "cheese" in k:
        categories["EUROPEAN CHEESES"].append((key, value))
        categorized = True
    elif any(x in k for x in ["sauce", "pickle", "gravy, mushroom", "eggplant, pickled"]):
        categories["CONDIMENTS & SAUCES"].append((key, value))
        categorized = True
    elif any(x in k for x in ["butter", "jam", "marmalade", "molasses", "peanut butter", "almond butter", "margarine"]):
        categories["SPREADS & BUTTERS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["sardine", "tuna", "chicken, canned"]):
        categories["CANNED PROTEINS"].append((key, value))
        categorized = True
    elif "beans" in k and "canned" in k or "chickpeas" in k or "chili" in k:
        categories["CANNED BEANS"].append((key, value))
        categorized = True
    elif "soup" in k or "broth" in k:
        categories["SOUPS & BROTHS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["beverage", "juice", "coffee", "tea", "milk,", "lemonade", "nectar", "cocoa"]):
        categories["BEVERAGES"].append((key, value))
        categorized = True
    elif any(x in k for x in ["bread,", "crouton", "macaroni", "rice and", "potato", "stuffing", "stew"]):
        categories["PREPARED FOODS"].append((key, value))
        categorized = True
    elif "gravy" in k:
        categories["GRAVIES"].append((key, value))
        categorized = True
    elif any(x in k for x in ["cream,", "yogurt"]):
        categories["DAIRY"].append((key, value))
        categorized = True
    elif any(x in k for x in ["ice cream", "pudding", "gelatin", "sherbet", "cake,", "candies"]):
        categories["DESSERTS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["cereal", "oats", "bulgur", "pancakes"]):
        categories["CEREALS & GRAINS"].append((key, value))
        categorized = True
    elif "oil," in k:
        categories["OILS"].append((key, value))
        categorized = True
    elif any(x in k for x in ["biscuit", "flour", "syrup"]):
        categories["BAKING"].append((key, value))
        categorized = True
    elif "snack" in k:
        categories["SNACKS"].append((key, value))
        categorized = True

    if not categorized:
        categories["MISCELLANEOUS"].append((key, value))

# Print organized output
for cat_name, items in categories.items():
    if items:
        print(f"    # ============ {cat_name} ============")
        for key, value in sorted(items):
            print(f'    "{key}": {value},')
        print()

print(f"\n# Total truly new entries: {len(new_only)}")
