import json
import requests

# Unit conversion multipliers: (from_unit, to_unit) -> multiplier
UNIT_CONVERSIONS = {
    ("G", "MG"): 1000,
    ("G", "UG"): 1_000_000,
    ("MG", "G"): 0.001,
    ("MG", "UG"): 1000,
    ("UG", "G"): 0.000001,
    ("UG", "MG"): 0.001,
    ("KJ", "KCAL"): 0.239006,  # 1 kJ = 0.239 kcal
}

# IU conversions are nutrient-specific
IU_CONVERSIONS = {
    "vitamin a": 0.3,      # 1 IU = 0.3 µg RAE
    "vitamin d": 0.025,    # 1 IU = 0.025 µg
    "vitamin e": 0.67,     # 1 IU = 0.67 mg (d-alpha-tocopherol)
}

# Fallback volume-to-gram conversions
# Used when USDA doesn't provide specific portion data
# Sources:
#   1. USDA FoodData Central API - foodPortions/foodMeasures data (see search_usda_cups.py)
#   2. King Arthur Baking - industry-standard baking measurements
#   3. Standard density calculations (water=240g/cup, oil=218g/cup)
#   4. FAO/INFOODS Density Database - food density data
#   5. Cooking reference sites (MyFitnessPal, Nutritionix, USDA SR Legacy)
FALLBACK_VOLUME_TO_GRAMS = {
    # ============ VOLUME UNITS (water-based defaults) ============
    "cup": 240,
    "cups": 240,
    "c": 240,
    "tablespoon": 15,
    "tablespoons": 15,
    "tbsp": 15,
    "tbs": 15,
    "teaspoon": 5,
    "teaspoons": 5,
    "tsp": 5,
    "fluid ounce": 30,
    "fluid ounces": 30,
    "fl oz": 30,
    "milliliter": 1,
    "milliliters": 1,
    "ml": 1,
    "liter": 1000,
    "liters": 1000,
    "l": 1000,
    "pint": 473,
    "pints": 473,
    "quart": 946,
    "quarts": 946,
    "gallon": 3785,
    "gallons": 3785,

    # ============ WEIGHT UNITS ============
    "ounce": 28.35,
    "ounces": 28.35,
    "oz": 28.35,
    "pound": 453.6,
    "pounds": 453.6,
    "lb": 453.6,
    "lbs": 453.6,
    "kilogram": 1000,
    "kilograms": 1000,
    "kg": 1000,
    "gram": 1,
    "grams": 1,
    "g": 1,
}

# Ingredient-specific grams per cup
# Keys match USDA FoodData Central naming conventions
# Generated using search_usda_cups.py script and supplemented with:
#   - USDA FoodData Central API (Foundation + SR Legacy databases)
#   - King Arthur Baking measurements
#   - Standard cooking references
INGREDIENT_GRAMS_PER_CUP = {
    # ============ FLOURS ============
    "flour": 120,
    "flour, 00": 120,
    "flour, almond": 96,
    "flour, amaranth": 120,
    "flour, barley": 120,
    "flour, bread, white, enriched, unbleached": 120,
    "flour, coconut": 112,
    "flour, corn, yellow, fine meal, enriched": 138,
    "flour, oat, whole grain": 92,
    "flour, potato": 160,
    "flour, quinoa": 112,
    "flour, rice, brown": 158,
    "flour, rice, glutinous": 158,
    "flour, rice, white, unenriched": 158,
    "flour, soy, defatted": 88,
    "flour, soy, full-fat": 85,
    "flour, whole wheat, unenriched": 120,
    "rice flour, brown": 158,
    "rice flour, white, unenriched": 158,
    "barley flour or meal": 120,
    "cornmeal, blue (navajo)": 138,
    "cornmeal, white (navajo)": 138,
    "cornstarch": 128,

    # ============ SUGARS & SWEETENERS ============
    "sugars, granulated": 200,
    "sugars, brown": 220,
    "sugars, powdered": 120,
    "sugar": 200,
    "molasses": 328,
    "agave, cooked (southwest)": 336,
    "agave, dried (southwest)": 200,
    "syrups, maple": 322,
    "syrups, corn, dark": 328,
    "syrups, corn, light": 328,
    "syrup, maple, canadian": 322,
    "honey": 340,

    # ============ DAIRY ============
    "milk": 244,
    "milk, buttermilk, fluid, whole": 245,
    "milk, canned, condensed, sweetened": 306,
    "milk, canned, evaporated, nonfat, with added vitamin a and vitamin d": 252,
    "milk, canned, evaporated, with added vitamin a": 252,
    "milk, goat, fluid, with added vitamin d": 244,
    "buttermilk, low fat": 245,
    "cream, fluid, half and half": 242,
    "cream, fluid, heavy whipping": 238,
    "cream, half and half, lowfat": 242,
    "cream, heavy": 238,
    "cream, sour, full fat": 230,
    "cream, whipped, cream topping, pressurized": 60,
    "cream cheese, full fat, block": 232,
    "cheese, cheddar": 113,
    "cheese, swiss": 108,
    "cheese, american, restaurant": 113,
    "cheese, ricotta, whole milk": 246,
    "cheese, cottage, lowfat, 2% milkfat": 226,
    "cheese, cottage, creamed, with fruit": 226,
    "cheese, feta": 150,
    "cheese, feta, whole milk, crumbled": 150,
    "cheese, parmesan, grated": 100,
    "cheese, parmesan, grated, refrigerated": 100,
    "cheese, parmesan, hard": 100,
    "cheese, mozzarella, low moisture, part-skim": 113,
    "cheese, blue": 135,
    "cheese, brie": 150,
    "cheese, gouda": 108,
    "cheese, provolone": 108,
    "cheese, provolone, reduced fat": 108,
    "cheese, provolone, sliced": 108,
    "cottage cheese, full fat, large or small curd": 210,
    "yogurt, plain, whole milk": 245,
    "yogurt, plain, nonfat": 245,
    "yogurt, greek, plain, nonfat": 280,
    "yogurt, greek, strawberry, nonfat": 280,

    # ============ MILK ALTERNATIVES ============
    "almond milk, unsweetened, plain, refrigerated": 240,
    "almond milk, unsweetened, plain, shelf stable": 240,
    "oat milk, unsweetened, plain, refrigerated": 240,
    "soy milk, sweetened, plain, refrigerated": 243,
    "soy milk, unsweetened, plain, shelf stable": 243,
    "beverages, coconut milk, sweetened, fortified with calcium, vitamins a, b12, d2": 240,

    # ============ FATS & OILS ============
    "butter, stick, salted": 227,
    "butter, stick, unsalted": 227,
    "oil, canola": 218,
    "oil, coconut": 218,
    "oil, corn": 218,
    "oil, olive, extra light": 216,
    "oil, olive, extra virgin": 216,
    "oil, peanut": 216,
    "oil, avocado": 216,
    "oil, hazelnut": 216,

    # ============ EGGS ============
    "eggs, grade a, large, egg whole": 50,
    "eggs, grade a, large, egg white": 33,
    "eggs, grade a, large, egg yolk": 17,
    "egg, white, dried": 107,

    # ============ GRAINS & PASTA (dry) ============
    "rice, white, long grain, unenriched, raw": 185,
    "rice, brown, long grain, unenriched, raw": 190,
    "rice, black, unenriched, raw": 185,
    "rice, white, glutinous, unenriched, cooked": 175,
    "wild rice, raw": 160,
    "wild rice, dry, raw": 160,
    "wild rice, cooked": 164,
    "quinoa, uncooked": 170,
    "quinoa, cooked": 185,
    "couscous, dry": 173,
    "couscous, cooked": 157,
    "bulgur, dry": 140,
    "bulgur, dry, raw": 140,
    "bulgur, cooked": 182,
    "barley, hulled": 200,
    "farro, pearled, dry, raw": 200,
    "buckwheat, whole grain": 170,
    "pasta, cooked, enriched, with added salt": 140,
    "pasta, whole-wheat, dry (includes foods for usda's food distribution program)": 100,
    "noodles, egg, dry, enriched": 100,
    "noodles, egg, dry, unenriched": 100,
    "rice noodles, dry": 100,
    "rice noodles, cooked": 176,
    "spaghetti, spinach, cooked": 140,
    "oats, whole grain, rolled, old fashioned": 90,
    "oats, whole grain, steel cut": 170,
    "tapioca, pearl, dry": 152,

    # ============ LEGUMES ============
    "beans, dry, black (0% moisture)": 180,
    "beans, dry, pinto (0% moisture)": 180,
    "beans, dry, navy (0% moisture)": 180,
    "beans, dry, great northern (0% moisture)": 180,
    "beans, dry, small white (0% moisture)": 180,
    "beans, dry, cranberry (0% moisture)": 180,
    "beans, cannellini, dry": 180,
    "beans, white, mature seeds, raw": 180,
    "beans, pinto, canned, drained solids": 171,
    "beans, pinto, canned, sodium added, drained and rinsed": 171,
    "beans, navy, mature seeds, raw": 180,
    "beans, navy, canned, sodium added, drained and rinsed": 171,
    "beans, great northern, mature seeds, canned": 171,
    "beans, great northern, canned, sodium added, drained and rinsed": 171,
    "beans, snap, green, raw": 110,
    "beans, snap, green, canned, regular pack, drained solids": 135,
    "lima beans, immature seeds, raw": 156,
    "lima beans, large, mature seeds, canned": 170,
    "chickpeas, (garbanzo beans, bengal gram), dry": 200,
    "chickpeas (garbanzo beans, bengal gram), canned, sodium added, drained and rinsed": 164,
    "lentils, dry": 190,
    "lentils, raw": 190,
    "lentils, pink or red, raw": 190,
    "lentils, sprouted, raw": 77,
    "peas, green, raw": 145,
    "peas, green, split, mature seeds, raw": 200,
    "peas, green, sweet, canned, sodium added, sugar added, drained and rinsed": 160,
    "peas, edible-podded, raw": 63,
    "blackeye pea, dry": 170,
    "blackeye pea, canned, sodium added, drained and rinsed": 165,
    "edamame, frozen, unprepared": 155,
    "edamame, frozen, prepared": 155,

    # ============ NUTS & SEEDS ============
    "nuts, almonds, whole, raw": 143,
    "nuts, walnuts, english, halves, raw": 120,
    "nuts, pecans": 109,
    "nuts, pecans, halves, raw": 109,
    "nuts, cashew nuts, raw": 137,
    "nuts, hazelnuts or filberts": 135,
    "nuts, hazelnuts or filberts, raw": 135,
    "nuts, macadamia nuts, raw": 134,
    "nuts, macadamia nuts, dry roasted, with salt added": 134,
    "nuts, pine nuts, dried": 135,
    "nuts, pine nuts, pinyon, dried": 135,
    "nuts, pine nuts, raw": 135,
    "nuts, pistachio nuts, raw": 123,
    "peanuts, raw": 146,
    "nuts, almond butter, plain, with salt added": 256,
    "nuts, almond butter, plain, without salt added": 256,
    "nuts, cashew butter, plain, with salt added": 256,
    "nuts, cashew butter, plain, without salt added": 256,
    "almond butter, creamy": 256,
    "peanut butter, creamy": 258,
    "seeds, chia seeds, dried": 170,
    "chia seeds, dry, raw": 170,
    "seeds, hemp seed, hulled": 160,
    "seeds, pumpkin and squash seed kernels, dried": 129,
    "seeds, pumpkin seeds (pepitas), raw": 129,
    "seeds, sesame seed kernels, dried (decorticated)": 144,
    "seeds, sesame seeds, whole, dried": 144,
    "seeds, sunflower seed kernels, dried": 140,
    "seeds, sunflower seed kernels, dry roasted, with salt added": 140,
    "seeds, sunflower seed, kernel, raw": 140,
    "seeds, sunflower seed butter, without salt": 256,
    "seeds, sesame butter, tahini, from raw and stone ground kernels": 240,
    "seeds, sesame butter, tahini, type of kernels unspecified": 240,

    # ============ VEGETABLES ============
    "onions, yellow, raw": 160,
    "onions, white, raw": 160,
    "onions, red, raw": 160,
    "green onion, (scallion), bulb and greens, root removed, raw": 100,
    "onions, spring or scallions (includes tops and bulb), raw": 100,
    "garlic, raw": 136,
    "carrots, mature, raw": 128,
    "carrots, baby, raw": 128,
    "carrots, frozen, unprepared": 128,
    "celery, raw": 101,
    "peppers, bell, green, raw": 149,
    "peppers, bell, red, raw": 149,
    "peppers, bell, orange, raw": 149,
    "peppers, jalapeno, raw": 90,
    "peppers, jalapeno, seeded, raw": 90,
    "peppers, jalapeno, canned, solids and liquids": 136,
    "peppers, serrano, raw": 105,
    "peppers, serrano, seeded, raw": 105,
    "pepper, banana, raw": 124,
    "tomato, roma": 180,
    "tomatoes, grape, raw": 149,
    "tomatoes, crushed, canned": 240,
    "tomato, sauce, canned, with salt added": 245,
    "tomato, puree, canned": 250,
    "spinach, baby": 30,
    "spinach, mature": 30,
    "kale, raw": 67,
    "kale, frozen, unprepared": 130,
    "kale, frozen, cooked, boiled, drained, without salt": 130,
    "lettuce, green leaf, raw": 36,
    "lettuce, leaf, green, raw": 36,
    "lettuce, leaf, red, raw": 28,
    "lettuce, cos or romaine, raw": 47,
    "lettuce, iceberg, raw": 72,
    "arugula, raw": 20,
    "arugula, baby, raw": 20,
    "cabbage, green, raw": 89,
    "cabbage, red, raw": 89,
    "cabbage, bok choy, raw": 70,
    "broccoli, raw": 91,
    "cauliflower, raw": 100,
    "cauliflower, frozen, unprepared": 100,
    "mushroom, crimini": 70,
    "mushroom, enoki": 65,
    "mushroom, oyster": 86,
    "mushroom, king oyster": 86,
    "mushroom, beech": 70,
    "mushrooms, oyster, raw": 86,
    "squash, summer, zucchini, includes skin, raw": 124,
    "squash, summer, green, zucchini, includes skin, raw": 124,
    "squash, zucchini, baby, raw": 124,
    "squash, summer, scallop, raw": 113,
    "squash, winter, butternut, raw": 140,
    "squash, winter, acorn, raw": 140,
    "squash, spaghetti, peeled, seeded, raw": 101,
    "squash, pie pumpkin, peeled, seeded, raw": 116,
    "cucumber, with peel, raw": 119,
    "corn, sweet, yellow and white kernels,  fresh, raw": 154,
    "beets, raw": 136,
    "beet greens, raw": 38,
    "potatoes, gold, without skin, raw": 150,
    "potatoes, red, without skin, raw": 150,
    "sweet potatoes, orange flesh, without skin, raw": 133,
    "sweet potato, canned, mashed": 255,
    "sweet potato leaves, raw": 35,
    "yam, raw": 150,
    "mountain yam, hawaii, raw": 150,
    "asparagus, green, raw": 134,
    "asparagus, raw": 134,
    "asparagus, frozen, unprepared": 134,
    "artichokes, (globe or french), raw": 168,
    "eggplant, raw": 82,
    "eggplant, pickled": 100,
    "parsnips, raw": 133,
    "parsnips, cooked, boiled, drained, with salt": 156,
    "turnips, raw": 130,
    "radishes, raw": 116,
    "radishes, red, raw": 116,
    "radishes, oriental, dried": 116,
    "leeks, (bulb and lower leaf-portion), raw": 89,
    "leeks, bulb and greens, root removed, raw": 89,
    "shallots, raw": 160,
    "shallots, bulb, peeled, root removed, raw": 160,
    "watercress, raw": 34,
    "chives, raw": 48,
    "chives, freeze-dried": 5,

    # ============ FRUITS ============
    "apples, fuji, with skin, raw": 125,
    "apples, gala, with skin, raw": 125,
    "apples, honeycrisp, with skin, raw": 125,
    "bananas, ripe and slightly ripe, raw": 150,
    "bananas, overripe, raw": 150,
    "oranges, raw, navels": 180,
    "tangerines, (mandarin oranges), raw": 195,
    "clementines, raw": 185,
    "limes, raw": 67,
    "lime juice, raw": 246,
    "grapefruit juice, white, raw": 247,
    "grapefruit juice, pink, raw": 247,
    "grapefruit juice, red, not fortified, not from concentrate, refrigerated": 247,
    "grapefruit juice, white, canned or bottled, unsweetened": 247,
    "tangerine juice, raw": 247,
    "orange juice, no pulp, not fortified, from concentrate, refrigerated": 248,
    "strawberries, raw": 152,
    "blueberries, raw": 148,
    "raspberries, raw": 123,
    "raspberries, puree, seedless": 250,
    "blackberries, raw": 144,
    "blackberries, frozen, unsweetened": 151,
    "cranberries, raw": 100,
    "cranberry juice, unsweetened": 253,
    "grapes, green, seedless, raw": 151,
    "grapes, red, seedless, raw": 151,
    "cherries, sweet, dark red, raw": 138,
    "mango, ataulfo, peeled, raw": 165,
    "mango, tommy atkins, peeled, raw": 165,
    "pineapple, raw": 165,
    "peaches, yellow, raw": 154,
    "nectarines, raw": 143,
    "plums, raw": 165,
    "plum, black, with skin, raw": 165,
    "apricots, raw": 155,
    "apricot, with skin, raw": 155,
    "apricots, dried, sulfured, uncooked": 130,
    "melons, cantaloupe, raw": 177,
    "melons, honeydew, raw": 170,
    "watermelon, raw": 152,
    "watermelon, seedless, flesh only, raw": 152,
    "papayas, raw": 145,
    "kiwifruit (kiwi), green, peeled, raw": 177,
    "avocado, hass, peeled, raw": 230,
    "avocados, raw, california": 230,
    "pomegranates, raw": 174,
    "pomegranate juice, bottled": 250,
    "figs, raw": 149,
    "figs, dried, uncooked": 149,
    "dates, deglet noor": 178,
    "dates, medjool": 178,
    "raisins, seeded": 145,
    "prune puree": 260,
    "prune juice, canned": 256,

    # ============ PROTEINS - POULTRY ============
    "chicken, breast, boneless, skinless, raw": 140,
    "chicken, breast, meat and skin, raw": 140,
    "chicken, ground, with additives, raw": 225,
    "turkey, ground, raw": 225,
    "turkey, ground, 93% lean, 7% fat, pan-broiled crumbles": 198,
    "turkey, ground, 93% lean/ 7% fat, raw": 225,
    "duck, domesticated, liver, raw": 140,

    # ============ PROTEINS - BEEF ============
    "beef, ground, 80% lean meat / 20% fat, raw": 225,
    "beef, ground, 90% lean meat / 10% fat, raw": 225,
    "beef, grass-fed, ground, raw": 225,
    "beef, top sirloin steak, raw": 227,
    "beef, tenderloin steak, raw": 227,

    # ============ PROTEINS - PORK ============
    "pork, ground, raw": 225,
    "pork, loin, boneless, raw": 227,
    "pork, belly, with skin, raw": 227,
    "ham, sliced, pre-packaged, deli meat (96%fat free, water added)": 135,
    "ham, sliced, restaurant": 135,
    "ham, minced": 225,
    "bacon, meatless": 30,
    "sausage, italian, pork, mild, cooked, pan-fried": 100,
    "sausage, smoked link sausage, pork": 100,
    "sausage, turkey, breakfast links, mild, raw": 85,
    "sausage, breakfast sausage, beef, pre-cooked, unprepared": 100,

    # ============ PROTEINS - LAMB & OTHER ============
    "lamb, ground, raw": 225,
    "lamb, new zealand, imported, ground lamb, raw": 225,
    "veal, ground, raw": 225,
    "bison, ground, grass-fed, raw": 225,
    "bison, ground, grass-fed, cooked": 198,
    "bison, ground, raw": 225,

    # ============ PROTEINS - SEAFOOD ============
    "fish, salmon, atlantic, farm raised, raw": 227,
    "fish, salmon, sockeye, wild caught, raw": 227,
    "fish, tuna, light, canned in water, drained solids": 154,
    "tuna, ahi or yellowfin, frozen, wild caught": 227,
    "fish, cod, atlantic, wild caught, raw": 227,
    "cod, pacific or alaskan, frozen, wild caught": 227,
    "fish, halibut, atlantic and pacific, raw": 227,
    "fish, halibut, greenland, raw": 227,
    "halibut, frozen, wild caught": 227,
    "fish, tilapia, raw": 227,
    "fish, tilapia, farm raised, raw": 227,
    "fish, tilapia, cooked, dry heat": 227,
    "fish, trout, mixed species, raw": 227,
    "fish, trout, rainbow, farmed, raw": 227,
    "fish, mackerel, atlantic, raw": 227,
    "fish, sardine, atlantic, canned in oil, drained solids with bone": 149,
    "anchovies, canned in olive oil, with salt, drained": 45,
    "crustaceans, shrimp, farm raised, raw": 227,
    "crustaceans, crab, blue, canned": 135,
    "crustaceans, crab, blue swimming, lump, pasteurized, refrigerated": 135,
    "crustaceans, lobster, northern, raw": 145,
    "crustaceans, lobster, northern, cooked, moist heat": 145,
    "lobster, tail only, frozen, wild caught": 145,
    "mollusks, scallop, mixed species, raw": 150,
    "scallops, bay, patagonian, frozen, wild caught": 150,
    "scallops, sea, frozen, wild caught": 150,
    "mollusks, mussel, blue, raw": 150,
    "mollusks, mussel, blue, cooked, moist heat": 150,
    "mollusks, clam, mixed species, raw": 150,

    # ============ PROTEINS - PLANT BASED ============
    "tempeh": 166,
    "tempeh, cooked": 166,
    "tofu, fried": 126,

    # ============ BAKING INGREDIENTS ============
    "cocoa, dry powder, unsweetened": 86,
    "baking chocolate, unsweetened, liquid": 170,
    "baking chocolate, mexican, squares": 170,
    "leavening agents, baking powder, double-acting, straight phosphate": 230,
    "leavening agents, baking powder, low-sodium": 230,
    "leavening agents, baking soda": 220,
    "leavening agents, cream of tartar": 150,
    "salt, table, iodized": 288,

    # ============ HERBS & SPICES ============
    "basil, fresh": 24,
    "spices, basil, dried": 12,
    "thyme, fresh": 18,
    "spices, thyme, dried": 8,
    "rosemary, fresh": 30,
    "spices, rosemary, dried": 8,
    "spices, sage, ground": 10,
    "spices, oregano, dried": 9,
    "parsley, fresh": 60,
    "parsley, freeze-dried": 5,
    "coriander (cilantro) leaves, raw": 16,
    "spices, coriander leaf, dried": 5,
    "dill weed, fresh": 10,
    "spices, bay leaf": 2,
    "ginger root, raw": 96,
    "spices, ginger, ground": 64,
    "spices, cumin seed": 100,
    "spices, paprika": 68,
    "spices, turmeric, ground": 100,
    "spices, nutmeg, ground": 75,
    "spices, pepper, black": 102,
    "spices, pepper, red or cayenne": 80,
    "spices, chili powder": 128,
    "spices, curry powder": 100,

    # ============ CONDIMENTS & SAUCES ============
    "soy sauce made from soy (tamari)": 255,
    "sauce, worcestershire": 272,
    "sauce, teriyaki, ready-to-serve": 288,
    "sauce, teriyaki, ready-to-serve, reduced sodium": 288,
    "sauce, ready-to-serve, pepper or hot": 273,
    "sauce, hot chile, sriracha": 267,
    "sauce, salsa, ready-to-serve": 259,
    "sauce, pasta, spaghetti/marinara, ready-to-serve": 250,
    "sauce, pesto, buitoni, pesto with basil, ready-to-serve, refrigerated": 260,
    "sauce, pesto, classico, basil pesto, ready-to-serve": 260,
    "sauce, tartar, ready-to-serve": 232,
    "ketchup, restaurant": 240,
    "mustard, prepared, yellow": 249,
    "vinegar, balsamic": 255,
    "vinegar, cider": 239,
    "hummus, commercial": 246,
    "hummus, home prepared": 246,
    "pickles, cucumber, dill or kosher dill": 143,
    "salad dressing, italian dressing, commercial, regular": 250,
    "salad dressing, italian dressing, fat-free": 260,
    "salad dressing, ranch dressing, regular": 244,
    "salad dressing, ranch dressing, fat-free": 260,
    "salad dressing, blue or roquefort cheese dressing, light": 245,

    # ============ MISCELLANEOUS ============
    "bread, white, commercially prepared": 45,  # per slice
    "bread, whole-wheat, commercially prepared": 43,
    "bread, oatmeal": 27,
    "water": 240,

    # ============ MORE VEGETABLES ============
    "brussels sprouts, raw": 88,
    "collards, raw": 36,
    "chard, swiss, raw": 36,
    "turnip greens, raw": 55,
    "mustard greens, raw": 56,
    "dandelion greens, raw": 55,
    "endive, raw": 50,
    "radicchio, raw": 40,
    "fennel, bulb, raw": 87,
    "kohlrabi, raw": 135,
    "rutabagas, raw": 140,
    "yambean (jicama), raw": 120,
    "taro, raw": 104,
    "cassava, raw": 206,
    "plantains, green, raw": 148,
    "plantains, yellow, raw": 154,
    "hearts of palm, canned": 146,
    "bamboo shoots, raw": 151,
    "mung beans, mature seeds, sprouted, raw": 104,
    "alfalfa seeds, sprouted, raw": 33,
    "okra, raw": 100,
    "jerusalem-artichokes, raw": 150,
    "tomatoes, sun-dried": 54,
    "peppers, sweet, red, canned, solids and liquids": 140,
    "pimento, canned": 127,

    # ============ MORE FRUITS ============
    "persimmons, japanese, raw": 168,
    "persimmons, native, raw": 168,
    "guavas, common, raw": 165,
    "guavas, strawberry, raw": 165,
    "carambola, (starfruit), raw": 132,
    "passion-fruit, (granadilla), purple, raw": 236,
    "litchis, raw": 190,
    "litchis, dried": 100,
    "longans, raw": 150,
    "longans, dried": 96,
    "jackfruit, raw": 165,
    "durian, raw or frozen": 243,
    "breadfruit, raw": 220,
    "soursop, raw": 225,
    "cherimoya, raw": 160,
    "tamarinds, raw": 120,
    "mulberries, raw": 140,
    "gooseberries, raw": 150,
    "currants, european black, raw": 112,
    "currants, red and white, raw": 112,
    "currants, zante, dried": 144,
    "elderberries, raw": 145,
    "goji berries, dried": 113,
    "mango, dried, sweetened": 160,
    "bananas, dehydrated, or banana powder": 100,
    "snacks, banana chips": 72,
    "nuts, coconut meat, raw": 80,
    "nuts, coconut meat, dried (desiccated), not sweetened": 93,
    "nuts, coconut meat, dried (desiccated), sweetened, shredded": 93,
    "nuts, coconut water (liquid from coconuts)": 240,

    # ============ MORE GRAINS ============
    "millet, raw": 200,
    "millet, cooked": 174,
    "teff, uncooked": 193,
    "teff, cooked": 252,
    "spelt, uncooked": 174,
    "spelt, cooked": 194,
    "amaranth grain, cooked": 246,
    "sorghum grain": 192,
    "triticale": 192,
    "rye grain": 169,
    "cereals, quaker, corn grits, instant, plain, dry": 156,
    "semolina, enriched": 167,
    "cereals, farina, unenriched, dry": 157,
    "cereals, cream of wheat, instant, dry": 142,
    "cereals ready-to-eat, granola, homemade": 122,
    "cereals ready-to-eat, post bran flakes": 40,
    "cereals ready-to-eat, ralston corn flakes": 28,
    "cereals ready-to-eat, rice, puffed, fortified": 14,
    "cereals ready-to-eat, quaker, quaker puffed rice": 14,
    "wheat germ, crude": 115,
    "oat bran, raw": 94,
    "wheat bran, crude": 58,
    "rice bran, crude": 118,

    # ============ MORE LEGUMES ============
    "mung beans, mature seeds, raw": 207,
    "beans, adzuki, mature seeds, raw": 197,
    "beans, fava, in pod, raw": 126,
    "soybeans, mature seeds, raw": 186,
    "pigeon peas (red gram), mature seeds, raw": 205,

    # ============ MORE NUTS & SEEDS ============
    "nuts, brazilnuts, dried, unblanched": 133,
    "nuts, chestnuts, european, raw, peeled": 145,
    "nuts, chestnuts, chinese, raw": 157,
    "nuts, chestnuts, japanese, raw": 162,
    "seeds, flaxseed": 168,
    "spices, poppy seed": 141,
    "spices, caraway seed": 100,
    "spices, fennel seed": 87,
    "spices, mustard seed, ground": 120,
    "spices, coriander seed": 87,
    "spices, celery seed": 101,
    "spices, dill seed": 96,
    "spices, anise seed": 96,

    # ============ MORE DAIRY ============
    "cheese, gruyere": 132,
    "cheese, fontina": 132,
    "cheese, muenster": 132,
    "cheese, colby": 132,
    "cheese, monterey": 132,
    "cheese, camembert": 130,
    "cheese, edam": 132,
    "cheese, goat, soft type": 144,
    "cheese, goat, semisoft type": 132,
    "cheese, goat, hard type": 110,
    "cheese, limburger": 135,
    "cheese, port de salut": 132,
    "cheese, roquefort": 135,
    "cheese, romano": 100,
    "cheese, tilsit": 132,
    "cheese, cream": 232,
    "cheese, neufchatel": 232,
    "cheese, cottage, creamed, large or small curd": 225,
    "cheese, cottage, lowfat, 1% milkfat": 226,
    "cheese, fresh, queso fresco": 132,
    "cheese, white, queso blanco": 132,
    "cheese, mexican, queso anejo": 132,
    "cheese, mexican, queso cotija": 132,
    "butter, clarified butter (ghee)": 205,
    "milk, buttermilk, dried": 120,
    "milk, dry, nonfat, regular, with added vitamin a and vitamin d": 120,
    "cream, sour, cultured": 230,
    "sour cream, light": 230,
    "sour cream, reduced fat": 230,
    "kefir, lowfat, plain, lifeway": 245,

    # ============ MORE PROTEINS - GAME & ORGAN MEATS ============
    "duck, domesticated, meat and skin, raw": 140,
    "goose, domesticated, meat and skin, raw": 140,
    "quail, meat and skin, raw": 140,
    "game meat, rabbit, wild, raw": 140,
    "deer (venison), sitka, raw (alaska native)": 140,
    "game meat, elk, raw": 140,
    "game meat, boar, wild, raw": 140,
    "ostrich, fan, raw": 140,
    "game meat, buffalo, water, raw": 140,
    "game meat, goat, raw": 140,
    "beef, variety meats and by-products, liver, raw": 226,
    "beef, variety meats and by-products, kidneys, raw": 140,
    "beef, variety meats and by-products, tongue, raw": 140,
    "beef, variety meats and by-products, heart, raw": 145,
    "beef, variety meats and by-products, tripe, raw": 140,
    "beef, new zealand, imported, sweetbread, raw": 140,
    "chicken, liver, all classes, raw": 140,
    "soup, stock, beef, home-prepared": 240,
    "soup, stock, chicken, home-prepared": 240,

    # ============ MORE SEAFOOD ============
    "fish, swordfish, raw": 170,
    "mahi mahi, frozen, wild caught": 170,
    "fish, snapper, mixed species, raw": 170,
    "fish, grouper, mixed species, raw": 170,
    "fish, sea bass, mixed species, raw": 170,
    "fish, flatfish (flounder and sole species), raw": 170,
    "fish, catfish, channel, farmed, raw": 170,
    "fish, carp, raw": 170,
    "fish, ocean perch, atlantic, raw": 170,
    "fish, pike, northern, raw": 170,
    "fish, pike, walleye, raw": 170,
    "crustaceans, crayfish, mixed species, wild, raw": 145,
    "crustaceans, crayfish, mixed species, farmed, raw": 145,
    "crustaceans, shrimp, raw": 145,
    "crustaceans, shrimp, mixed species, raw (may contain additives to retain moisture)": 145,
    "mollusks, squid, mixed species, raw": 150,
    "mollusks, cuttlefish, mixed species, raw": 150,
    "mollusks, abalone, mixed species, raw": 150,
    "mollusks, conch, baked or broiled": 150,
    "mollusks, oyster, pacific, raw": 248,
    "mollusks, oyster, eastern, farmed, raw": 248,
    "mollusks, oyster, eastern, wild, raw": 248,
    "fish, caviar, black and red, granular": 238,
    "fish, roe, mixed species, raw": 227,
    "fish, salmon, chinook, smoked": 145,
    "fish, salmon, chinook, smoked, (lox), regular": 145,
    "crustaceans, crab, alaska king, imitation, made from surimi": 145,
    "fish, haddock, raw": 170,
    "fish, pollock, alaska, raw": 170,
    "fish, pollock, atlantic, raw": 170,
    "fish, herring, atlantic, raw": 170,
    "fish, herring, pacific, raw": 170,
    "fish, anchovy, european, canned in oil, drained solids": 45,

    # ============ MORE CONDIMENTS ============
    "sauce, fish, ready-to-serve": 260,
    "sauce, oyster, ready-to-serve": 260,
    "sauce, hoisin, ready-to-serve": 282,
    "miso": 275,
    "salad dressing, thousand island dressing, fat-free": 260,
    "salad dressing, caesar dressing, regular": 244,
    "dressing, honey mustard, fat-free": 268,
    "sauce, barbecue": 280,
    "sauce, steak, tomato based": 260,
    "vinegar, red wine": 239,
    "pickle relish, hamburger": 245,
    "capers, canned": 137,
    "olives, pickled, canned or bottled, green": 134,
    "tomato products, canned, paste, without salt added (includes foods for usda's food distribution program)": 262,
    "sauce, alfredo mix, dry": 100,
    "sauce, enchilada, red, mild, ready to serve": 250,
    "sauce, salsa, verde, ready-to-serve": 259,

    # ============ MORE BAKING ============
    "leavening agents, yeast, baker's, active dry": 136,
    "leavening agents, yeast, baker's, compressed": 194,
    "gelatins, dry powder, unsweetened": 165,
    "arrowroot flour": 128,
    "vanilla extract": 208,
    "candies, semisweet chocolate": 168,
    "cocoa, dry powder, unsweetened, processed with alkali": 86,
    "carob flour": 103,

    # ============ MORE HERBS & SPICES ============
    "spearmint, fresh": 11,
    "peppermint, fresh": 11,
    "spearmint, dried": 3,
    "spices, tarragon, dried": 5,
    "spices, marjoram, dried": 6,
    "spices, savory, ground": 5,
    "spices, cardamom": 100,
    "spices, cloves, ground": 78,
    "spices, allspice, ground": 99,
    "spices, mace, ground": 93,
    "spices, cinnamon, ground": 125,
    "spices, saffron": 69,

    # ============ PREPARED FOODS ============
    "rice, white, long-grain, regular, enriched, cooked": 158,
    "rice, white, medium-grain, enriched, cooked": 186,
    "rice, brown, long-grain, cooked (includes foods for usda's food distribution program)": 195,
    "pasta, cooked, unenriched, with added salt": 140,
    "beans, black, mature seeds, cooked, boiled, with salt": 172,
    "lentils, mature seeds, cooked, boiled, with salt": 198,
    "potatoes, mashed, ready-to-eat": 210,
    "fast foods, potato, mashed": 210,
    "potatoes, frozen, french fried, par fried, extruded, unprepared": 82,
    "snack, potato chips, made from dried potatoes, plain": 28,
    "snacks, potato chips, plain, salted": 28,
    "snacks, tortilla chips, nacho cheese": 32,
    "tortilla chips, yellow, plain, salted": 32,
    "crackers, saltines (includes oyster, soda, soup)": 30,
    "snacks, pretzels, hard, plain, salted": 60,
    "snacks, popcorn, air-popped": 8,
    "snacks, popcorn, air-popped (unsalted)": 8,
    "snacks, trail mix, regular": 150,
    "snacks, granola bars, hard, almond": 28,
    "snacks, granola bars, hard, plain": 28,

    # ============ MORE TOFU & PLANT PROTEINS ============
    "tofu, raw, firm, prepared with calcium sulfate": 252,
    "tofu, raw, regular, prepared with calcium sulfate": 248,

    # ============ MORE JUICES ============
    "passion-fruit juice, purple, raw": 247,
    "passion-fruit juice, yellow, raw": 247,
    "guava nectar, with sucralose, canned": 250,
    "tamarind nectar, canned": 250,

    # ============ CANNED FRUITS ============
    "beverages, pineapple and grapefruit juice drink, canned": 250,
    "figs, canned, water pack, solids and liquids": 248,
    "fruit cocktail, canned, heavy syrup, drained": 214,
    "peach nectar, canned, with added ascorbic acid": 220,
    "peaches, canned, heavy syrup, drained": 222,
    "pear nectar, canned, with added ascorbic acid": 250,
    "pears, canned, heavy syrup, drained": 201,
    "pineapple, canned, juice pack, drained": 162,
    "tangerines, (mandarin oranges), canned, juice pack": 249,
    "tangerines, (mandarin oranges), canned, juice pack, drained": 189,

    # ============ CANNED VEGETABLES ============
    "asparagus, canned, drained solids": 242,
    "bamboo shoots, canned, drained solids": 131,
    "beef stew, canned entree": 196,
    "beef, corned beef hash, with potato, canned": 236,
    "beets, canned, drained solids": 170,
    "beets, harvard, canned, solids and liquids": 246,
    "butterbur, canned": 124,
    "carrot juice, canned": 236,
    "carrots, canned, no salt added, drained solids": 228,
    "cherries, sour, canned, water pack, drained": 168,
    "gravy, mushroom, canned": 238,
    "mushrooms, canned, drained solids": 156,
    "nuts, coconut cream, canned, sweetened": 296,
    "peas and onions, canned, solids and liquids": 120,
    "potatoes, canned, drained solids": 180,
    "potatoes, canned, solids and liquids": 300,
    "succotash, (corn and limas), canned, with cream style corn": 266,
    "tomatoes, red, ripe, canned, packed in tomato juice": 240,

    # ============ FROZEN VEGETABLES ============
    "beans, snap, green, frozen, all styles, microwaved": 111,
    "beans, snap, green, frozen, cooked, boiled, drained, with salt": 135,
    "broccoli, frozen, chopped, cooked, boiled, drained, with salt": 184,
    "broccoli, frozen, chopped, unprepared": 156,
    "corn, yellow, whole kernel, frozen, microwaved": 141,
    "peas and carrots, frozen, unprepared": 140,
    "peas and onions, frozen, unprepared": 138,
    "spinach, frozen, chopped or leaf, cooked, boiled, drained, with salt": 190,
    "spinach, frozen, chopped or leaf, cooked, boiled, drained, without salt": 190,
    "succotash, (corn and limas), frozen, unprepared": 156,
    "vegetables, mixed, frozen, cooked, boiled, drained, with salt": 182,
    "vegetables, mixed, frozen, cooked, boiled, drained, without salt": 182,

    # ============ FROZEN FRUITS ============
    "blueberries, frozen, sweetened": 230,
    "blueberries, frozen, unsweetened (includes foods for usda's food distribution program)": 155,
    "loganberries, frozen": 147,
    "peaches, frozen, sliced, sweetened": 250,
    "raspberries, frozen, red, sweetened": 250,
    "raspberries, frozen, red, unsweetened": 140,
    "strawberries, frozen, sweetened, sliced": 255,
    "strawberries, frozen, unsweetened (includes foods for usda's food distribution program)": 149,

    # ============ ASIAN INGREDIENTS ============
    "cabbage, chinese (pak-choi), cooked, boiled, drained, with salt": 170,
    "cabbage, chinese (pak-choi), raw": 70,
    "cabbage, chinese (pe-tsai), raw": 76,
    "cabbage, kimchi": 150,
    "cabbage, napa, cooked": 109,
    "fungi, cloud ears, dried": 28,
    "mushrooms, enoki, raw": 65,
    "mushrooms, shiitake, cooked, with salt": 145,
    "mushrooms, shiitake, stir-fried": 97,
    "noodles, chinese, cellophane or long rice (mung beans), dehydrated": 140,
    "noodles, chinese, chow mein": 56,
    "noodles, japanese, soba, cooked": 114,
    "puddings, coconut cream, dry mix, instant": 25,
    "restaurant, chinese, vegetable chow mein, without meat or noodles": 195,
    "rice and vermicelli mix, beef flavor, unprepared": 185,
    "rice and vermicelli mix, rice pilaf flavor, prepared with 80% margarine": 238,
    "rice and vermicelli mix, rice pilaf flavor, unprepared": 206,
    "seaweed, agar, raw": 5,
    "seaweed, irishmoss, raw": 5,
    "seaweed, wakame, raw": 5,
    "soy sauce made from soy and wheat (shoyu)": 255,
    "soy sauce made from soy and wheat (shoyu), low sodium": 255,
    "vermicelli, made from soy": 140,
    "wasabi, root, raw": 130,

    # ============ BEAN SPROUTS ============
    "beans, kidney, mature seeds, sprouted, raw": 184,
    "beans, mung, mature seeds, sprouted, canned, drained solids": 125,
    "beans, navy, mature seeds, sprouted, raw": 104,
    "soybeans, mature seeds, sprouted, cooked, steamed": 94,
    "soybeans, mature seeds, sprouted, raw": 70,

    # ============ LATIN INGREDIENTS ============
    "cheese, mexican blend": 112,
    "corn flour, masa, enriched, white": 114,
    "corn flour, masa, unenriched, white": 114,
    "dip, salsa con queso, cheese and salsa- medium": 250,
    "on the border, mexican rice": 114,
    "on the border, refried beans": 135,
    "refried beans, canned, vegetarian": 242,
    "restaurant, latino, arroz con leche (rice pudding)": 253,
    "restaurant, latino, black bean soup": 246,

    # ============ MORE EUROPEAN CHEESES ============
    "cheese spread, cream cheese base": 240,
    "cheese, brick": 113,
    "cracker barrel, macaroni n' cheese": 149,
    "macaroni and cheese, frozen entree": 137,
    "sauce, cheese, ready-to-serve": 252,

    # ============ MORE CONDIMENTS & SAUCES ============
    "fish, sardine, pacific, canned in tomato sauce, drained solids with bone": 89,
    "pickles, cucumber, sweet (includes bread and butter pickles)": 153,
    "sauce, cocktail, ready-to-serve": 240,

    # ============ SPREADS & BUTTERS ============
    "biscuits, plain or buttermilk, dry mix": 128,
    "butter, salted": 227,
    "butter, whipped, with salt": 151,
    "butter, without salt": 227,
    "candies, confectioner's coating, peanut butter": 168,
    "fruit butters, apple": 282,
    "jams and preserves, no sugar (with sodium saccharin), any flavor": 224,
    "margarine-like, margarine-butter blend, soybean oil and butter": 227,
    "marmalade, orange": 320,
    "peanut butter, chunky, vitamin and mineral fortified": 258,
    "peanut butter, smooth style, without salt": 258,
    "peanut butter, smooth, vitamin and mineral fortified": 258,

    # ============ CANNED PROTEINS ============
    "chicken, canned, no broth": 205,
    "fish, tuna, light, canned in oil, drained solids": 146,

    # ============ CANNED BEANS ============
    "beans, baked, canned, with beef": 266,
    "beans, baked, canned, with franks": 259,
    "beans, baked, canned, with pork": 253,
    "beans, black turtle, mature seeds, canned": 240,
    "beans, kidney, all types, mature seeds, canned": 256,
    "beans, kidney, red, mature seeds, canned, solids and liquids": 256,
    "beans, navy, mature seeds, canned": 262,
    "beans, pinto, mature seeds, canned, solids and liquids": 240,
    "beans, pinto, mature seeds, canned, solids and liquids, low sodium": 240,
    "beans, snap, green, canned, no salt added, drained solids": 153,
    "beans, snap, green, canned, no salt added, solids and liquids": 240,
    "chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained, rinsed in tap water": 152,
    "chickpeas (garbanzo beans, bengal gram), mature seeds, canned, solids and liquids": 240,
    "chili with beans, canned": 256,
    "chili, no beans, canned entree": 240,

    # ============ SOUPS & BROTHS ============
    "campbell's, chicken noodle soup, condensed": 246,
    "campbell's, tomato soup, condensed": 248,
    "fish broth": 244,
    "soup, beef broth bouillon and consomme, canned, condensed": 248,
    "soup, beef broth or bouillon canned, ready-to-serve": 240,
    "soup, black bean, canned, condensed": 257,
    "soup, chicken broth, canned, condensed": 252,
    "soup, chicken noodle, canned, condensed": 248,
    "soup, cream of asparagus, canned, condensed": 252,
    "soup, healthy choice garden vegetable soup, canned": 246,
    "soup, lentil with ham, canned, ready-to-serve": 248,
    "soup, pea, green, canned, condensed": 256,
    "soup, pea, split with ham, canned, condensed": 270,
    "soup, swanson, vegetable broth": 220,
    "soup, tomato, canned, condensed": 148,

    # ============ MORE BEVERAGES ============
    "beverages, coffee, brewed, breakfast blend": 248,
    "beverages, coffee, brewed, prepared with tap water": 237,
    "beverages, cranberry juice cocktail": 271,
    "beverages, cranberry-grape juice drink, bottled": 245,
    "beverages, lemonade, powder": 218,
    "beverages, tea, green, brewed, regular": 245,
    "beverages, tea, herb, brewed, chamomile": 237,
    "lemonade, powder, prepared with water": 264,
    "milk, chocolate beverage, hot cocoa, homemade": 250,
    "potatoes, mashed, dehydrated, flakes without milk, dry form": 60,
    "tomato and vegetable juice, low sodium": 242,
    "vegetable juice cocktail, canned": 253,
    "vegetable juice cocktail, low sodium, canned": 254,
    "vegetable juice, bolthouse farms, daily greens": 269,

    # ============ BREAD CRUMBS & STUFFING ============
    "bread, crumbs, dry, grated, plain": 108,
    "bread, crumbs, dry, grated, seasoned": 120,
    "bread, stuffing, cornbread, dry mix, prepared": 200,
    "bread, stuffing, dry mix, prepared": 200,
    "croutons, plain": 30,
    "croutons, seasoned": 40,

    # ============ GRAVIES ============
    "gravy, campbell's, chicken": 226,
    "gravy, onion, dry, mix": 24,

    # ============ MORE DAIRY ============
    "yogurt, greek, strawberry, lowfat": 245,
    "yogurt, plain, low fat": 245,
    "yogurt, plain, skim milk": 245,

    # ============ DESSERTS ============
    "cake, snack cakes, creme-filled, chocolate with frosting": 50,
    "gelatin desserts, dry mix": 21,
    "gelatin desserts, dry mix, prepared with water": 270,
    "ice creams, vanilla": 66,
    "ice creams, vanilla, light": 76,
    "puddings, chocolate, dry mix, instant": 25,
    "puddings, chocolate, dry mix, regular": 25,
    "sherbet, orange": 148,

    # ============ MORE CEREALS & GRAINS ============
    "cereals ready-to-eat, post, waffle crisp": 30,
    "oats (includes foods for usda's food distribution program)": 156,
    "pancakes, buckwheat, dry mix, incomplete": 122,

    # ============ MORE OILS ============
    "oil, mustard": 218,
    "oil, sesame, salad or cooking": 218,

    # ============ MORE BAKING ============
    "syrups, table blends, pancake": 314,
    "wheat flour, white, tortilla mix, enriched": 111,

    # ============ MORE SNACKS ============
    "snacks, tortilla chips, unsalted, white corn": 26,
    "snacks, trail mix, regular, unsalted": 150,

    # ============ MISCELLANEOUS VEGETABLES & FOODS ============
    "abiyuch, raw": 228,
    "beans, black, mature seeds, raw": 194,
    "burdock root, raw": 118,
    "cabbage, mustard, salted": 128,
    "grape leaves, raw": 14,
    "jew's ear, (pepeao), raw": 99,
    "mangos, raw": 165,
    "mushrooms, chanterelle, raw": 54,
    "peppers, hot chile, sun-dried": 37,
    "restaurant, chinese, vegetable lo mein, without meat": 136,

    # ============ MORE FLOURS (USDA SR Legacy / Foundation) ============
    "flour, buckwheat": 120,
    "buckwheat flour, whole-groat": 120,
    "flour, chickpea (besan)": 92,
    "chickpea flour (besan)": 92,
    "flour, garbanzo bean": 92,
    "flour, rye, dark": 128,
    "flour, rye, light": 102,
    "flour, rye, medium": 102,
    "flour, millet": 119,
    "flour, sorghum": 121,
    "flour, tapioca": 120,
    "tapioca flour": 120,
    "flour, cassava": 150,
    "cassava flour": 150,
    "flour, chestnut": 100,
    "chestnut flour": 100,
    "flour, hazelnut": 112,
    "hazelnut flour": 112,
    "flour, walnut": 80,
    "walnut flour": 80,
    "flour, lupin": 132,
    "lupin flour": 132,
    "flour, teff": 140,
    "teff flour": 140,
    "flour, spelt": 99,
    "spelt flour": 99,
    "flour, kamut": 120,
    "flour, einkorn": 100,
    "flour, emmer": 120,
    "flour, mesquite": 108,
    "flour, tigernut": 120,

    # ============ MORE PASTA TYPES (dry, per cup) ============
    "pasta, angel hair, dry": 85,
    "pasta, linguine, dry": 100,
    "pasta, fettuccine, dry": 100,
    "pasta, penne, dry": 105,
    "pasta, rigatoni, dry": 105,
    "pasta, fusilli, dry": 105,
    "pasta, orzo, dry": 170,
    "orzo, dry": 170,
    "pasta, macaroni, elbow, dry, enriched": 105,
    "macaroni, elbow, dry": 105,
    "pasta, shells, small, dry": 105,
    "pasta, shells, medium, dry": 95,
    "pasta, shells, large, dry": 85,
    "pasta, farfalle (bow ties), dry": 85,
    "farfalle, dry": 85,
    "pasta, rotini, dry": 105,
    "rotini, dry": 105,
    "pasta, lasagna, dry, sheets": 57,
    "lasagna, dry": 57,
    "pasta, ravioli, cheese, frozen": 108,
    "ravioli, cheese": 108,
    "pasta, tortellini, cheese, frozen": 108,
    "tortellini, cheese": 108,
    "gnocchi, potato": 170,
    "gnocchi": 170,
    "couscous, israeli (pearl), dry": 157,
    "israeli couscous, dry": 157,
    "pearl couscous, dry": 157,
    "pasta, ditalini, dry": 105,
    "pasta, orecchiette, dry": 85,
    "pasta, cavatappi, dry": 100,
    "pasta, gemelli, dry": 105,
    "pasta, campanelle, dry": 85,
    "pasta, radiatore, dry": 85,
    "pasta, ziti, dry": 105,

    # ============ MORE RICE TYPES ============
    "rice, jasmine, white, raw": 185,
    "jasmine rice, white, raw": 185,
    "rice, jasmine, brown, raw": 190,
    "rice, arborio, raw": 185,
    "arborio rice, raw": 185,
    "rice, basmati, white, raw": 180,
    "basmati rice, white, raw": 180,
    "rice, basmati, brown, raw": 190,
    "rice, sushi (calrose), raw": 195,
    "sushi rice, raw": 195,
    "rice, sticky (glutinous), raw": 185,
    "sticky rice, raw": 185,
    "rice, forbidden (black), raw": 185,
    "forbidden rice, raw": 185,
    "black rice, raw": 185,
    "rice, red, raw": 190,
    "red rice, raw": 190,
    "rice, parboiled, dry": 185,
    "parboiled rice, dry": 185,
    "rice, instant, white, dry": 160,
    "instant rice, dry": 160,
    "rice, jasmine, white, cooked": 175,
    "rice, basmati, white, cooked": 165,
    "rice, arborio, cooked (risotto)": 175,
    "rice, carnaroli, raw": 185,
    "rice, bomba, raw": 185,
    "rice, valencian, raw": 185,

    # ============ MORE ASIAN VEGETABLES ============
    "bok choy, raw": 70,
    "bok choy, cooked, boiled, drained": 170,
    "cabbage, napa, raw": 76,
    "napa cabbage, raw": 76,
    "cabbage, chinese (pe-tsai), cooked, boiled, drained": 119,
    "broccoli, chinese, raw": 88,
    "gai lan, raw": 88,
    "chinese broccoli, raw": 88,
    "yu choy, raw": 85,
    "choy sum, raw": 85,
    "mustard cabbage, raw": 56,
    "spinach, water, raw": 30,
    "water spinach, raw": 30,
    "kangkong, raw": 30,
    "amaranth leaves, raw": 28,
    "moringa leaves, raw": 21,
    "moringa, leaves, cooked, boiled, drained": 140,
    "purslane, raw": 43,
    "malabar spinach, raw": 44,
    "bitter melon (balsam pear), raw": 93,
    "balsam-pear (bitter gourd), leafy tips, raw": 58,
    "balsam-pear (bitter gourd), pods, raw": 93,
    "winter melon (wax gourd), raw": 152,
    "wax gourd, raw": 152,
    "luffa (chinese okra), raw": 89,
    "dishcloth gourd (luffa), raw": 89,
    "chayote, fruit, raw": 132,
    "chayote, cooked, boiled, drained": 160,
    "daikon, raw": 116,
    "radishes, oriental, raw": 116,
    "white radish, raw": 116,
    "lotus root, raw": 120,
    "lotus root, cooked, boiled, drained": 89,
    "taro root, raw": 104,
    "taro, cooked, without salt": 135,
    "malanga, raw": 228,
    "yautia (tannier), raw": 135,
    "name yam, raw": 150,
    "dasheen, raw": 104,
    "chrysanthemum, garland, raw": 36,
    "chrysanthemum leaves, raw": 36,

    # ============ MORE MUSHROOMS ============
    "mushrooms, portabella, raw": 86,
    "portobello mushroom, raw": 86,
    "mushrooms, portabella, grilled": 121,
    "mushrooms, cremini (brown italian), raw": 72,
    "cremini mushrooms, raw": 72,
    "mushrooms, white, raw": 70,
    "button mushrooms, raw": 70,
    "mushrooms, shiitake, raw": 145,
    "shiitake mushrooms, raw": 145,
    "mushrooms, shiitake, dried": 15,
    "shiitake mushrooms, dried": 15,
    "mushrooms, shiitake, cooked, without salt": 145,
    "mushrooms, maitake, raw": 70,
    "maitake mushrooms, raw": 70,
    "lion's mane mushroom, raw": 55,
    "mushrooms, morel, raw": 66,
    "morel mushrooms, raw": 66,
    "mushrooms, porcini, raw": 70,
    "porcini mushrooms, raw": 70,
    "porcini mushrooms, dried": 30,
    "mushrooms, black trumpet, raw": 60,
    "black trumpet mushrooms, raw": 60,
    "mushrooms, hedgehog, raw": 70,
    "mushrooms, matsutake, raw": 80,

    # ============ MORE DRIED FRUITS ============
    "cranberries, dried, sweetened": 120,
    "dried cranberries (craisins)": 120,
    "cherries, sweet, dried": 140,
    "dried cherries": 140,
    "blueberries, dried, sweetened": 140,
    "dried blueberries": 140,
    "apricots, dried, sulfured, stewed": 250,
    "apricots, dehydrated (low-moisture), sulfured, uncooked": 119,
    "dried figs": 149,
    "prunes, dehydrated (low-moisture), uncooked": 132,
    "prunes, dried, uncooked": 174,
    "dried prunes": 174,
    "plums, dried (prunes)": 174,
    "apples, dried, sulfured, uncooked": 86,
    "dried apples": 86,
    "pears, dried, sulfured, uncooked": 180,
    "dried pears": 180,
    "peaches, dried, sulfured, uncooked": 130,
    "dried peaches": 130,
    "dried mango": 160,
    "papaya, dried": 140,
    "dried papaya": 140,
    "pineapple, dried": 175,
    "dried pineapple": 175,
    "coconut, dried (desiccated), sweetened, flaked, packaged": 74,
    "coconut, dried (desiccated), toasted": 60,

    # ============ MORE NUT BUTTERS ============
    "pistachio butter": 250,
    "macadamia nut butter": 240,
    "hazelnut butter": 256,
    "hazelnut spread, chocolate-hazelnut": 288,
    "walnut butter": 240,
    "pecan butter": 256,
    "coconut butter (coconut manna)": 224,

    # ============ MORE SEED BUTTERS ============
    "tahini (sesame butter)": 240,
    "sunflower seed butter, without salt": 256,
    "sunflower seed butter, with salt added": 256,
    "pumpkin seed butter": 256,

    # ============ ALTERNATIVE PROTEINS ============
    "seitan, cooked": 144,
    "wheat gluten, vital": 120,
    "jackfruit, canned, in brine": 165,
    "textured vegetable protein (tvp), dry": 88,
    "tvp, dry": 88,
    "soy curls, dry": 60,
    "tofu, extra firm, raw": 252,
    "tofu, silken, soft": 255,
    "tofu, silken, firm": 253,
    "tofu, smoked": 248,

    # ============ MORE DAIRY ALTERNATIVES ============
    "oat milk, unsweetened": 240,
    "oat milk, sweetened": 244,
    "rice milk, unsweetened": 245,
    "rice milk": 245,
    "hemp milk, unsweetened": 240,
    "hemp milk": 240,
    "cashew milk, unsweetened": 240,
    "cashew milk": 240,
    "macadamia milk, unsweetened": 240,
    "macadamia milk": 240,
    "pea milk, unsweetened": 240,
    "pea milk": 240,
    "flax milk, unsweetened": 240,
    "flax milk": 240,
    "coconut cream, raw (liquid expressed from grated meat)": 240,
    "coconut cream, canned, sweetened": 296,
    "coconut cream, canned": 240,
    "coconut yogurt, unsweetened": 224,
    "almond yogurt, unsweetened": 227,
    "soy yogurt, plain": 245,
    "cashew cheese": 113,
    "nutritional yeast": 60,
    "yeast, nutritional, fortified": 60,

    # ============ FERMENTED FOODS ============
    "sauerkraut, canned, solids and liquids": 142,
    "sauerkraut, canned, drained": 142,
    "kimchi, napa cabbage": 150,
    "miso, red": 275,
    "miso, white": 275,
    "natto": 175,
    "kombucha": 240,
    "kefir, plain, whole milk": 245,
    "kefir, lowfat, plain": 245,
    "kefir, nonfat, plain": 246,
    "pickled ginger": 100,
    "ginger, pickled": 100,
    "pickled vegetables, mixed": 130,

    # ============ SWEETENERS ============
    "stevia, powder": 0.5,
    "monk fruit sweetener, powder": 0.5,
    "erythritol": 180,
    "xylitol": 192,
    "maltitol": 180,
    "date syrup": 320,
    "sugar, date": 160,
    "coconut sugar": 144,
    "sugar, coconut": 144,
    "palm sugar": 200,
    "jaggery (gur)": 220,
    "jaggery": 220,
    "turbinado sugar": 200,
    "sugar, turbinado": 200,
    "muscovado sugar": 220,
    "sugar, muscovado": 220,
    "demerara sugar": 220,
    "sugar, demerara": 220,
    "date sugar": 160,
    "maple sugar": 172,

    # ============ COOKING WINES & LIQUIDS ============
    "sherry, cooking": 240,
    "cooking sherry": 240,
    "wine, marsala": 240,
    "marsala wine": 240,
    "sake (rice wine)": 240,
    "rice wine, sake": 240,
    "mirin (sweet rice wine)": 240,
    "rice wine, mirin": 240,
    "wine, table, white": 240,
    "white wine": 240,
    "wine, table, red": 240,
    "red wine": 240,
    "beer, regular": 356,
    "beer, light": 354,
    "chicken stock, home-prepared": 240,
    "chicken stock, canned": 240,
    "beef stock, home-prepared": 240,
    "beef stock, canned": 240,
    "vegetable stock, home-prepared": 240,
    "vegetable stock, canned": 240,
    "fish stock, home-prepared": 244,
    "dashi (japanese fish stock)": 240,
    "dashi": 240,
    "bone broth, beef": 240,
    "bone broth, chicken": 240,

    # ============ THICKENERS ============
    "xanthan gum": 150,
    "guar gum": 144,
    "locust bean gum (carob bean gum)": 144,
    "agar, dried": 8,
    "agar agar, powder": 115,
    "agar agar, flakes": 28,
    "carrageenan": 144,
    "psyllium husk, whole": 80,
    "psyllium husk, powder": 130,
    "glucomannan (konjac powder)": 100,
    "pectin, dry mix": 152,
    "pectin, liquid": 300,
    "gelatin, unflavored, powder": 165,
    "kuzu (kudzu starch)": 128,
    "potato starch": 160,
    "tapioca starch": 120,
    "modified food starch": 128,

    # ============ ADDITIONAL SEAWEEDS ============
    "seaweed, kelp (kombu), raw": 80,
    "kombu, dried": 8,
    "seaweed, nori, dried": 2.6,
    "nori, sheets, dried": 2.6,
    "seaweed, dulse, dried": 28,
    "seaweed, spirulina, dried": 112,
    "seaweed, chlorella, dried": 112,
    "seaweed, hijiki, dried": 43,
    "seaweed, arame, dried": 28,

    # ============ ADDITIONAL GRAINS ============
    "freekeh, dry": 170,
    "freekeh, cooked": 200,
    "fonio, dry": 180,
    "kaniwa, dry": 170,
    "job's tears (hato mugi), dry": 190,
    "wheat berries, hard red, dry": 180,
    "wheat berries, soft white, dry": 170,
    "rye berries, dry": 180,
    "oat groats, dry": 160,

    # ============ ADDITIONAL LEGUMES ============
    "lupini beans, canned, drained": 177,
    "butter beans (lima), canned, drained": 170,
    "cannellini beans, canned, drained": 179,
    "gigante beans, canned, drained": 180,
    "cranberry beans, canned, drained": 177,
    "mung beans, dry": 207,
    "urad dal (black gram), dry": 200,
    "toor dal (pigeon pea), dry": 205,
    "chana dal, dry": 200,
    "masoor dal (red lentils), dry": 190,

    # ============ ADDITIONAL ITEMS ============
    "aquafaba (chickpea liquid)": 240,
    "flax egg (1 tbsp flax + 3 tbsp water)": 45,
    "chia egg (1 tbsp chia + 3 tbsp water)": 45,
    "cacao nibs": 120,
    "cacao powder, raw": 86,
    "maca powder": 100,
    "lucuma powder": 100,
    "matcha powder": 64,
    "acai powder, freeze-dried": 75,
    "spirulina powder": 112,
    "wheatgrass powder": 60,
    "barley grass powder": 60,
    "collagen powder": 73,
    "protein powder, whey": 29,
    "protein powder, pea": 60,
    "protein powder, rice": 60,
    "protein powder, hemp": 60,
    "protein powder, soy": 75,
}


class USDAService:
    """
    Any operations that interact with the USDA API
    """

    def __init__(self):
        """
        Initialize
        """
        self.api_key = json.load(open("api_keys.json", 'r'))["usda"]
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.food_search_endpoint = "/foods/search"
        self.food_details_endpoint = "/food"

    def get_food_portions(self, fdc_id: int) -> dict:
        """
        Get portion data for a food by its FDC ID using the food details endpoint.

        :param fdc_id: the USDA FoodData Central ID
        :return: dict of portion descriptions to gram weights
        """
        url = f"{self.base_url}{self.food_details_endpoint}/{fdc_id}?api_key={self.api_key}"
        r = requests.get(url)
        if r.status_code != 200:
            return {}
        food_info = r.json()

        portions = {}
        if "foodPortions" in food_info:
            for portion in food_info["foodPortions"]:
                gram_weight = portion.get("gramWeight")
                if not gram_weight:
                    continue

                # Try multiple fields to build portion description
                desc = portion.get("portionDescription", "").lower()

                # SR Legacy uses "modifier" (e.g., "cup", "tbsp")
                if not desc and "modifier" in portion:
                    amount = portion.get("amount", 1)
                    modifier = portion.get("modifier", "").lower()
                    desc = f"{amount} {modifier}".strip()

                # Foundation/other formats use measureUnit object
                if not desc and "measureUnit" in portion:
                    amount = portion.get("amount", 1)
                    measure_unit = portion.get("measureUnit", {})
                    unit_name = measure_unit.get("name", "").lower()
                    if unit_name:
                        desc = f"{amount} {unit_name}"

                if desc and gram_weight:
                    portions[desc] = gram_weight
        return portions

    def search_food(self, food_keywords: str, food_type: str="foundation"):
        """
        Search for food nutrient information and portion data by keyword(s).
        :param food_keywords: the keywords to search for food in USDA database
        :param food_type: foundation, sr_legacy, or branded
        :return: dict with 'nutrients' and 'portions' keys
        """
        food_keywords = food_keywords.replace(' ', "%20")
        if food_type == "branded":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&api_key={self.api_key}"
        elif food_type == "foundation":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=Foundation&api_key={self.api_key}"
        elif food_type == "sr_legacy":
            url = f"{self.base_url}{self.food_search_endpoint}?query={food_keywords}&dataType=SR%20Legacy&api_key={self.api_key}"
        else:
            raise Exception(f"Invalid food type: {food_type} not in [branded, foundation, sr_legacy]")
        print("USDA URL:", url)
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Couldn't get food search response for \"{food_keywords}\"")
        r = r.json()
        food_info = r["foods"][0]
        # Extract nutrients
        nutrients = food_info["foodNutrients"]
        keys_to_remove = ["nutrientId", "nutrientNumber", "derivationCode", "derivationDescription", "derivationId",
                          "foodNutrientSourceId", "foodNutrientSourceCode", "foodNutrientSourceDescription", "rank",
                          "indentLevel", "foodNutrientId", "dataPoints", "min", "max", "median"]
        for nut in nutrients:
            for key in keys_to_remove:
                nut.pop(key, None)
        # Extract portion data (unit to gram conversions)
        portions = {}
        if "foodMeasures" in food_info:
            for measure in food_info["foodMeasures"]:
                unit = measure.get("disseminationText", "").lower()
                gram_weight = measure.get("gramWeight")
                if unit and gram_weight:
                    portions[unit] = gram_weight
        if "foodPortions" in food_info:
            for portion in food_info["foodPortions"]:
                desc = portion.get("portionDescription", "").lower()
                gram_weight = portion.get("gramWeight")
                if desc and gram_weight:
                    portions[desc] = gram_weight
        # For branded foods, also grab servingSize
        if "servingSize" in food_info and "servingSizeUnit" in food_info:
            unit = food_info["servingSizeUnit"].lower()
            portions[f"1 {unit}"] = food_info["servingSize"]

        # If no portions found, fetch from food details endpoint
        if not portions and "fdcId" in food_info:
            portions = self.get_food_portions(food_info["fdcId"])

        return {
            "name": food_info["description"],
            "fdcId": food_info.get("fdcId"),
            "nutrients": nutrients,
            "portions": portions
        }

    def convert_amount_to_grams(self, amount: float, unit: str, portions: dict, ingredient_name: str = None) -> float:
        """
        Convert an ingredient amount to grams using USDA portion data,
        with fallback to ingredient-specific or standard volume/weight conversions.

        :param amount: the numeric amount (e.g., 2 for "2 cups")
        :param unit: the unit to convert from (e.g., "cup", "tbsp")
        :param portions: dict of portion descriptions to gram weights from search_food
        :param ingredient_name: optional ingredient name for ingredient-specific conversions
        :return: amount in grams
        :raises ValueError: if no conversion found for the unit
        """
        unit_lower = unit.lower().strip()

        # If already in grams, return as-is
        if unit_lower in ("g", "gram", "grams"):
            return amount

        # If already a weight unit, convert directly
        if unit_lower in FALLBACK_VOLUME_TO_GRAMS and unit_lower in ("ounce", "ounces", "oz", "pound", "pounds", "lb", "lbs", "kg", "kilogram", "kilograms"):
            return amount * FALLBACK_VOLUME_TO_GRAMS[unit_lower]

        # Try USDA portions first (ingredient-specific, most accurate)
        for portion_desc, gram_weight in portions.items():
            if unit_lower in portion_desc or portion_desc in unit_lower:
                return amount * gram_weight

        # Try matching with "1 unit" pattern
        search_patterns = [
            f"1 {unit_lower}",
            unit_lower,
            f"{unit_lower}s",  # plural
            unit_lower.rstrip('s'),  # singular
        ]
        for pattern in search_patterns:
            for portion_desc, gram_weight in portions.items():
                if pattern in portion_desc:
                    return amount * gram_weight

        # Try ingredient-specific cup conversions
        if ingredient_name and unit_lower in ("cup", "cups", "c"):
            ing_lower = ingredient_name.lower()
            # Try exact match first
            if ing_lower in INGREDIENT_GRAMS_PER_CUP:
                return amount * INGREDIENT_GRAMS_PER_CUP[ing_lower]
            # Try partial matches
            for ing_key, grams in INGREDIENT_GRAMS_PER_CUP.items():
                if ing_key in ing_lower or ing_lower in ing_key:
                    return amount * grams

        # Try ingredient-specific conversions for tbsp/tsp (scale from cup)
        if ingredient_name and unit_lower in ("tablespoon", "tablespoons", "tbsp", "tbs"):
            ing_lower = ingredient_name.lower()
            for ing_key, grams_per_cup in INGREDIENT_GRAMS_PER_CUP.items():
                if ing_key in ing_lower or ing_lower in ing_key:
                    return amount * (grams_per_cup / 16)  # 16 tbsp per cup

        if ingredient_name and unit_lower in ("teaspoon", "teaspoons", "tsp"):
            ing_lower = ingredient_name.lower()
            for ing_key, grams_per_cup in INGREDIENT_GRAMS_PER_CUP.items():
                if ing_key in ing_lower or ing_lower in ing_key:
                    return amount * (grams_per_cup / 48)  # 48 tsp per cup

        # Fallback to standard conversions (water-based, approximate)
        if unit_lower in FALLBACK_VOLUME_TO_GRAMS:
            return amount * FALLBACK_VOLUME_TO_GRAMS[unit_lower]

        raise ValueError(f"No gram conversion found for unit '{unit}'. Available portions: {list(portions.keys())}")

    def convert_nutrient_unit(self, value, from_unit, to_unit, nutrient_name=None):
        """
        Convert a nutrient value from one unit to another.
        :param value: the numeric value to convert
        :param from_unit: the source unit (e.g., 'G', 'MG', 'UG', 'IU')
        :param to_unit: the target unit
        :param nutrient_name: nutrient name (required for IU conversions)
        :return: converted value
        """
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        if from_unit == to_unit:
            return value
        # Standard unit conversions
        key = (from_unit, to_unit)
        if key in UNIT_CONVERSIONS:
            return value * UNIT_CONVERSIONS[key]
        # IU conversions require knowing the nutrient
        if from_unit == "IU" and nutrient_name:
            nutrient_lower = nutrient_name.lower()
            for nutrient_key, multiplier in IU_CONVERSIONS.items():
                if nutrient_key in nutrient_lower:
                    # IU converts to the base unit (UG for vitamins A/D, MG for vitamin E)
                    iu_value = value * multiplier
                    # If target unit differs from IU's natural target, chain convert
                    if nutrient_key in ["vitamin a", "vitamin d"] and to_unit == "MG":
                        return iu_value * 0.001  # UG -> MG
                    elif nutrient_key == "vitamin e" and to_unit == "UG":
                        return iu_value * 1000  # MG -> UG
                    return iu_value
        raise ValueError(f"No conversion available from {from_unit} to {to_unit} for {nutrient_name}")

    def parse_nutrients_to_ingredient_fields(self, nutrients, nutrient_map=None):
        """
        Parse USDA nutrients into Ingredient-compatible field values with unit conversion.
        :param nutrients: list of nutrient dicts from USDA API
        :param nutrient_map: dict mapping nutrient names to {field, expected_unit}
        :return: dict of {field_name: converted_value}
        """
        if nutrient_map is None:
            with open("nutrient_map.json", "r") as f:
                nutrient_map = json.load(f)
        result = {}
        for nutrient in nutrients:
            nutrient_name = nutrient.get("nutrientName")
            if nutrient_name not in nutrient_map:
                continue
            mapping = nutrient_map[nutrient_name]
            field_name = mapping["field"]
            expected_unit = mapping["expected_unit"]
            # Skip if we already have a value for this field (e.g., Energy from multiple sources)
            if field_name in result:
                continue
            usda_unit = nutrient.get("unitName", "").upper()
            value = nutrient.get("value")
            if value is None:
                continue
            # Convert if units don't match
            if usda_unit != expected_unit:
                try:
                    value = self.convert_nutrient_unit(value, usda_unit, expected_unit, nutrient_name)
                except ValueError as e:
                    print(f"Warning: {e}")
                    continue
            result[field_name] = value
        return result


if __name__ == "__main__":
    usda_service = USDAService()
    result = usda_service.search_food("kraft shredded cheese", "branded")
    print("Name:", result["name"])
    print("Portions:", result["portions"])
    print("Nutrients:", result["nutrients"])