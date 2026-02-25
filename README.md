# Meal Logger

A Python application that automatically scrapes recipes from cooking websites, parses ingredients, fetches nutritional data from the USDA FoodData Central API, and stores everything in a PostgreSQL database for tracking meals and macros.

## Features

- **Recipe Scraping**: Automatically search and scrape recipes from FitMenCook, supporting both V1 and V2 site templates with JSON-LD and HTML fallback parsing
- **Intelligent Ingredient Parsing**: Parse complex ingredient strings including fractions, ranges, unicode characters, and various unit formats using the `ingredient-parser-nlp` library
- **USDA Nutrition Lookup**: Fetch comprehensive nutritional data from the USDA FoodData Central API (supports Foundation, SR Legacy, and Branded food types)
- **Macro Logging**: Calculate per-serving nutrient totals from ingredient data and log meals with date tracking
- **Interactive Ingredient Editor**: PyQt6-based GUI for reviewing and editing parsed ingredients before saving
- **PostgreSQL Storage**: Persistent storage with automated schema migrations via Flyway-style scripts
- **MVC Architecture**: Clean separation of concerns with Model-View-Controller pattern

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3 |
| GUI | PyQt6 |
| Database | PostgreSQL |
| Web Scraping | BeautifulSoup4, Requests |
| Ingredient Parsing | ingredient-parser-nlp |
| DB Driver | psycopg2 |
| Nutrition API | USDA FoodData Central |
| AI Estimation | Anthropic Claude API (optional, for unit conversion fallback) |

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

> **Note:** All `_per_gram` nutrient columns store values in grams, regardless of the nutrient's conventional unit (mg, mcg, etc.).

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | TEXT | Ingredient name |
| calories_per_gram | NUMERIC | Calories |
| protein_per_gram | NUMERIC | Protein |
| carbs_per_gram | NUMERIC | Carbohydrates |
| fat_per_gram | NUMERIC | Fat |
| fiber_per_gram | NUMERIC | Fiber |
| sugar_per_gram | NUMERIC | Sugar |
| saturated_fat_per_gram | NUMERIC | Saturated fat |
| trans_fat_per_gram | NUMERIC | Trans fat |
| cholesterol_per_gram | NUMERIC | Cholesterol |
| sodium_per_gram | NUMERIC | Sodium |
| potassium_per_gram | NUMERIC | Potassium |
| calcium_per_gram | NUMERIC | Calcium |
| iron_per_gram | NUMERIC | Iron |
| vitamin_a_per_gram | NUMERIC | Vitamin A |
| vitamin_c_per_gram | NUMERIC | Vitamin C |
| vitamin_d_per_gram | NUMERIC | Vitamin D |

**meal_ingredient_bridge**
| Column | Type | Description |
|--------|------|-------------|
| meal_id | INT | Foreign key to meals (composite PK) |
| ingredient_id | INT | Foreign key to ingredients (composite PK) |
| quantity | DECIMAL | Amount used in recipe units |
| unit | TEXT | Unit of measurement |
| quantity_grams | DECIMAL | Amount converted to grams |

**meal_log**
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| meal_id | INT | Foreign key to meals |
| date_eaten | DATE | Date the meal was consumed |
| servings_consumed | DECIMAL | Number of servings eaten (default 1) |
| calories | DECIMAL | Calories for servings consumed |
| protein | DECIMAL | Protein (g) |
| carbs | DECIMAL | Carbohydrates (g) |
| fat | DECIMAL | Fat (g) |
| fiber | DECIMAL | Fiber (g) |
| sugar | DECIMAL | Sugar (g) |
| saturated_fat | DECIMAL | Saturated fat (g) |
| trans_fat | DECIMAL | Trans fat (g) |
| cholesterol | DECIMAL | Cholesterol (g) |
| sodium | DECIMAL | Sodium (g) |
| potassium | DECIMAL | Potassium (g) |
| calcium | DECIMAL | Calcium (g) |
| iron | DECIMAL | Iron (g) |
| vitamin_a | DECIMAL | Vitamin A (g) |
| vitamin_c | DECIMAL | Vitamin C (g) |
| vitamin_d | DECIMAL | Vitamin D (g) |
| created_at | TIMESTAMP | Creation timestamp |

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+

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

5. **Configure API keys**

   Create `api_keys.json` in the project root:
   ```json
   {
     "usda": "YOUR_USDA_API_KEY",
     "anthropic": "YOUR_ANTHROPIC_API_KEY"
   }
   ```

   - Get a free USDA key from [USDA FoodData Central](https://fdc.nal.usda.gov/api-key-signup.html)
   - The Anthropic key is optional and used as a fallback for estimating grams-per-cup when USDA portion data is unavailable

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
4. Ingredients are looked up via the USDA API for nutritional data
5. **Meal and ingredients are saved** to the database
6. **Macros are calculated** per serving and logged to the `meal_log` table

### Ingredient Types

- **Foundation**: Generic/unbranded foods (e.g., "cheddar cheese", "chicken breast")
- **Branded**: Specific branded products (e.g., "Kraft Singles", "Tyson chicken strips")

## Project Structure

```
MealLogger/
├── main.py                       # Application entry point (Controller)
├── model.py                      # Business logic layer (Model)
├── view.py                       # User interface layer (View)
├── meal.py                       # Meal data object
├── meal_log.py                   # Meal log data object
├── ingredient.py                 # Ingredient data object
├── meal_repository.py            # Meal database operations
├── meal_log_repository.py        # Meal log database operations
├── ingredient_repository.py      # Ingredient database operations
├── meal_ingredient_repository.py # Meal-ingredient bridge operations
├── ingredient_editor.py          # PyQt6 ingredient editing GUI
├── recipe_parser.py              # Recipe/ingredient parser (JSON-LD + HTML)
├── recipe_search.py              # Base class for recipe scrapers
├── fitmencook_search.py          # FitMenCook scraper implementation
├── usda_service.py               # USDA FoodData Central API client
├── database_utility.py           # Database connection utilities
├── flyway.py                     # Database migration runner
├── nutrient_map.json             # Maps USDA nutrient names to DB fields
├── grams_per_cup_cache.json      # Cached grams-per-cup estimates
├── api_keys.json                 # API keys (gitignored)
├── requirements.txt              # Python dependencies
├── database/
│   ├── database.ini              # Database configuration (gitignored)
│   └── flyway/
│       └── postgresql/
│           ├── create_table_meals.sql
│           ├── create_table_ingredients.sql
│           ├── create_table_meal_ingredient_bridge.sql
│           └── create_table_meal_log.sql
└── units/
    ├── units.json                # Measurement unit aliases
    └── descriptor_units.json     # Descriptor units (e.g., "to taste")
```

## Nutrient Calculation Pipeline

The pipeline that converts raw USDA data into per-serving meal log values involves several steps. Below is a summary of each stage and how the math works.

### Pipeline Steps

1. **USDA API** returns nutrient values **per 100g** of food (e.g., Protein: 20g per 100g)
2. **`parse_nutrients_to_ingredient_fields()`** converts units if needed (MG→G, IU→UG, KJ→KCAL). Values are still per 100g at this point.
3. **`fetch_ingredients()`** divides by 100, converting to **per 1g** (e.g., 20 / 100 = 0.2g protein per gram). Stored on the `Ingredient` object.
4. **`convert_amount_to_grams()`** converts recipe amounts to grams (e.g., 2 cups flour → 260g) using USDA portion data, volume-to-cup derivation, or Claude AI estimation as a last resort.
5. **`log_macros()`** calculates the final values:
   - For each ingredient: `per_gram × amount_grams`
   - Sum across all ingredients to get the **total for the entire recipe**
   - Divide by `meal.servings` to get **per serving**
   - Multiply by `servings_consumed` to get the **final logged value**

### Worked Example

**Recipe:** 2 cups oatmeal, 4 servings, user eats 1 serving

| Step | Operation | Protein Value |
|------|-----------|---------------|
| USDA API | Raw value per 100g | 17g |
| ÷ 100 | Per gram | 0.17g |
| × 300g (2 cups) | Whole recipe total | 51g |
| ÷ 4 servings | Per serving | 12.75g |
| × 1 consumed | Logged value | **12.75g** |

### Formula

```
logged_nutrient = (sum(per_gram_i × amount_grams_i) / recipe_servings) × servings_consumed
```

### Known Limitations

- **Portion modifiers** (e.g., "sifted" vs "packed" cups) are not yet supported; the default modifier is used
- **Zero-value nutrients** are treated the same as missing nutrients (no impact on totals since 0 × grams = 0)

## Roadmap

- [ ] Support for additional recipe websites
- [ ] Nutritional goal tracking
- [ ] Export to CSV/JSON
- [ ] Meal planning and scheduling
- [ ] Shopping list generation