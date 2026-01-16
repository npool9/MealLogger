# Meal Logger

A Python application that automatically scrapes recipes from cooking websites, parses ingredients, fetches nutritional data from the USDA FoodData Central API, and stores everything in a PostgreSQL database for tracking meals and macros.

## Features

- **Recipe Scraping**: Automatically search and scrape recipes from FitMenCook (with extensible architecture for additional sites)
- **Intelligent Ingredient Parsing**: Parse complex ingredient strings including fractions, ranges, unicode characters, and various unit formats
- **USDA Nutrition Lookup**: Fetch comprehensive nutritional data from the USDA FoodData Central API (supports both Foundation and Branded food types)
- **Interactive Ingredient Editor**: PyQt6-based GUI for reviewing and editing parsed ingredients before saving
- **PostgreSQL Storage**: Persistent storage with automated schema migrations via Flyway-style scripts
- **MVC Architecture**: Clean separation of concerns with Model-View-Controller pattern

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3 |
| GUI | PyQt6 |
| Database | PostgreSQL |
| Web Scraping | BeautifulSoup4, Requests, Selenium |
| DB Driver | psycopg2 |
| Nutrition API | USDA FoodData Central |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                 │
│                      (Controller)                               │
├─────────────────────────────────────────────────────────────────┤
│                              │                                  │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│         ┌─────────┐                    ┌─────────┐              │
│         │  View   │                    │  Model  │              │
│         │(view.py)│                    │(model.py)│             │
│         └────┬────┘                    └────┬────┘              │
│              │                              │                   │
│              ▼                              ▼                   │
│   ┌──────────────────┐          ┌─────────────────────┐         │
│   │IngredientEditor  │          │  Recipe Scrapers    │         │
│   │    (PyQt6)       │          │  (FitMenCook, etc.) │         │
│   └──────────────────┘          └─────────────────────┘         │
│                                          │                      │
│                                          ▼                      │
│                                 ┌─────────────────────┐         │
│                                 │   RecipeParser      │         │
│                                 │   USDAService       │         │
│                                 │   DatabaseUtility   │         │
│                                 └─────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Tables

**meals**
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | TEXT | Meal name |
| description | TEXT | Recipe steps/instructions |
| servings | TEXT | Number of servings |
| serving_size | BIGINT | Size per serving |
| serving_unit | VARCHAR | Unit for serving size |
| recipe_url | TEXT | Source URL |
| created_at | TIMESTAMP | Creation timestamp |

**ingredients**
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | TEXT | Ingredient name |
| calories_per_unit | NUMERIC | Calories |
| protein_per_unit | NUMERIC | Protein (g) |
| carbs_per_unit | NUMERIC | Carbohydrates (g) |
| fat_per_unit | NUMERIC | Fat (g) |
| fiber_per_unit | NUMERIC | Fiber (g) |
| sugar_per_unit | NUMERIC | Sugar (g) |
| saturated_fat_per_unit | NUMERIC | Saturated fat (g) |
| trans_fat_per_unit | NUMERIC | Trans fat (g) |
| cholesterol_mg_per_unit | NUMERIC | Cholesterol (mg) |
| sodium_mg_per_unit | NUMERIC | Sodium (mg) |
| potassium_mg_per_unit | NUMERIC | Potassium (mg) |
| calcium_mg_per_unit | NUMERIC | Calcium (mg) |
| iron_mg_per_unit | NUMERIC | Iron (mg) |
| vitamin_a_ug_per_unit | NUMERIC | Vitamin A (mcg) |
| vitamin_c_mg_per_unit | NUMERIC | Vitamin C (mg) |
| vitamin_d_ug_per_unit | NUMERIC | Vitamin D (mcg) |
| default_unit | TEXT | Default measurement unit |

**meal_ingredient_bridge**
| Column | Type | Description |
|--------|------|-------------|
| meal_id | INT | Foreign key to meals |
| ingredient_id | INT | Foreign key to ingredients |
| quantity | DECIMAL | Amount used |
| unit | TEXT | Unit of measurement |

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Chrome browser (for Selenium-based scraping)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MealLogger
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**

   Create `database/database.ini` with your PostgreSQL credentials:
   ```ini
   [credentials]
   host = localhost
   port = 5432
   user = your_username
   init_db = postgres
   app_db = meal_logger
   ```

5. **Configure the USDA API**

   Create `api_keys.json` in the project root:
   ```json
   {
     "usda": "YOUR_USDA_API_KEY"
   }
   ```

   Get a free API key from [USDA FoodData Central](https://fdc.nal.usda.gov/api-key-signup.html).

## Usage

Run the application:

```bash
python main.py
```

### Workflow

1. **Enter a meal name** when prompted (e.g., "chicken stir fry")
2. The app searches FitMenCook for matching recipes
3. **Review ingredients** in the PyQt6 editor:
   - Edit amounts, units, or names
   - Add or remove ingredients
   - Select ingredient type (Foundation vs Branded) for USDA lookups
4. **Save** to store the meal and ingredients in the database

### Ingredient Types

- **Foundation**: Generic/unbranded foods (e.g., "cheddar cheese", "chicken breast")
- **Branded**: Specific branded products (e.g., "Kraft Singles", "Tyson chicken strips")

## Project Structure

```
MealLogger/
├── main.py                 # Application entry point (Controller)
├── model.py                # Business logic layer (Model)
├── view.py                 # User interface layer (View)
├── meal.py                 # Meal data object
├── meal_repository.py      # Meal database operations
├── ingredient.py           # Ingredient data object
├── ingredient_editor.py    # PyQt6 ingredient editing GUI
├── ingredient_parser.py    # Legacy ingredient string parser
├── recipe_parser.py        # Advanced recipe/ingredient parser
├── recipe_search.py        # Base class for recipe scrapers
├── fitmencook_search.py    # FitMenCook scraper implementation
├── usda_service.py         # USDA FoodData Central API client
├── database_utility.py     # Database connection utilities
├── flyway.py               # Database migration runner
├── macro_calculator.py     # Macro calculation utilities (WIP)
├── requirements.txt        # Python dependencies
├── database/
│   ├── database.ini        # Database configuration (gitignored)
│   └── flyway/
│       └── postgresql/
│           ├── create_table_meals.sql
│           ├── create_table_ingredients.sql
│           └── create_table_meal_ingredient_bridge.sql
└── units/
    ├── units.json          # Measurement unit aliases
    └── descriptor_units.json # Descriptor units (e.g., "to taste")
```

## Supported Units

The parser recognizes a wide variety of measurement units and their aliases:

| Unit | Aliases |
|------|---------|
| cup | c, cp, cups, cps |
| tablespoon | tbsp, tbs, T, tbl, spoon |
| teaspoon | tsp, t |
| ounce | oz, onces |
| fluid ounce | fl oz, fl. oz |
| pound | lb, lbs |
| gram | g, gr, grams |
| kilogram | kg, kilo, kilos |
| milliliter | ml, mL |
| liter | l, L, liters |
| pinch | pinches, pch |
| slice | slices |
| sprig | sprigs |
| handful | handfuls, hdful |
| ... | and many more |

## Roadmap

- [ ] FitBit integration for automatic meal logging
- [ ] Support for additional recipe websites
- [ ] Meal planning and scheduling
- [ ] Nutritional goal tracking
- [ ] Export to CSV/JSON
- [ ] Recipe favoriting and tagging
- [ ] Shopping list generation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for personal use. See LICENSE file for details.