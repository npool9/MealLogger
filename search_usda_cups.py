#!/usr/bin/env python3
"""
USDA FoodData Central - Complete Food Database Portion Extractor

This script iterates through ALL foods in the USDA FoodData Central API
and extracts all portion-to-gram mappings (cups, cloves, slices, pieces, etc.).

The USDA database contains ~400,000+ foods across multiple data types:
- Foundation: ~2,000 foods (high-quality, detailed nutrient data)
- SR Legacy: ~8,000 foods (Standard Reference, comprehensive)
- FNDDS: ~9,000 foods (survey data with portions)
- Branded: ~380,000+ foods (commercial products)

Usage:
    python search_usda_cups.py [--data-type TYPE] [--start PAGE] [--limit PAGES]

    Options:
        --data-type    Foundation, SR Legacy, FNDDS, or Branded (default: all)
        --start        Starting page number (default: 1)
        --limit        Max pages to process, 0 for unlimited (default: 0)
        --output       Output file name (default: usda_cups_complete.json)

Requirements:
    - requests library
    - api_keys.json file with "usda" key containing your API key

Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html
"""

import json
import requests
import time
import argparse
import re
from typing import Optional
from datetime import datetime

# Volume unit conversion to cups (1 cup = 240ml baseline)
# Maps unit names to their equivalent in cups
VOLUME_TO_CUPS = {
    # Cups
    "cup": 1.0,
    "cups": 1.0,
    "c": 1.0,
    # Tablespoons (16 tbsp = 1 cup)
    "tablespoon": 1/16,
    "tablespoons": 1/16,
    "tbsp": 1/16,
    "tbs": 1/16,
    # Teaspoons (48 tsp = 1 cup)
    "teaspoon": 1/48,
    "teaspoons": 1/48,
    "tsp": 1/48,
    # Fluid ounces (8 fl oz = 1 cup)
    "fluid ounce": 1/8,
    "fluid ounces": 1/8,
    "fl oz": 1/8,
    # Milliliters (240ml = 1 cup)
    "milliliter": 1/240,
    "milliliters": 1/240,
    "ml": 1/240,
    # Liters (1L = ~4.227 cups)
    "liter": 4.227,
    "liters": 4.227,
    "l": 4.227,
    # Pints (1 pint = 2 cups)
    "pt": 2.0,
    "pint": 2.0,
    "pints": 2.0,
    # Quarts (1 quart = 4 cups)
    "qt": 4.0,
    "qts": 4.0,
    "quart": 4.0,
    "quarts": 4.0,
    # Gallons (1 gallon = 16 cups)
    "gallon": 16.0,
    "gallons": 16.0,
    "gal": 16.0,
    "gals": 16.0,
}

# Build regex pattern for all volume units (sorted by length desc to match longer units first)
VOLUME_UNITS = sorted(VOLUME_TO_CUPS.keys(), key=len, reverse=True)
VOLUME_PATTERN = r'(\d+(?:/\d+)?(?:\.\d+)?)\s*(' + '|'.join(re.escape(u) for u in VOLUME_UNITS) + r')\b'

# Load API key
with open("api_keys.json", "r") as f:
    API_KEY = json.load(f)["usda"]

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
PAGE_SIZE = 200  # Max allowed by API

# =============================================================================
# FNDDS PORTION CODES: Maps numeric modifier codes to portion descriptions
# Source: USDA FNDDS Portions and Weights dataset
# =============================================================================
FNDDS_PORTION_CODES = {
    # Volume measurements
    "10205": "1 cup",
    "10206": "0.5 cup",
    "10207": "0.25 cup",
    "10208": "0.33 cup",
    "10209": "0.75 cup",
    "10210": "2 cups",
    "21000": "1 tablespoon",
    "21001": "0.5 tablespoon",
    "21002": "2 tablespoons",
    "21003": "3 tablespoons",
    "22000": "1 teaspoon",
    "22001": "0.5 teaspoon",
    "22002": "0.25 teaspoon",
    "22003": "2 teaspoons",
    "30000": "1 fl oz",
    "30001": "2 fl oz",
    "30002": "4 fl oz",
    "30003": "6 fl oz",
    "30004": "8 fl oz",
    "30005": "12 fl oz",
    "30006": "16 fl oz",
    # Common container sizes
    "60424": "1 can or bottle (16 fl oz)",
    "60533": "1 can or bottle (12 fl oz)",
    "60699": "1 drink",
    "63480": "guideline amount per fl oz",
    "64216": "1 bottle (40 fl oz)",
    # Special codes
    "90000": "quantity not specified",
}

def get_foods_list(data_type: Optional[str] = None, page: int = 1) -> dict:
    """
    Get a page of foods from the USDA database.

    :param data_type: Optional filter by data type
    :param page: Page number (1-indexed)
    :return: API response dict with 'foods' list and metadata
    """
    url = f"{BASE_URL}/foods/list"
    params = {
        "api_key": API_KEY,
        "pageSize": PAGE_SIZE,
        "pageNumber": page
    }
    if data_type:
        params["dataType"] = [data_type]

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return {"foods": response.json(), "status": "ok"}
        elif response.status_code == 429:
            print(f"  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return get_foods_list(data_type, page)
        else:
            print(f"  Error {response.status_code}: {response.text[:200]}")
            return {"foods": [], "status": "error"}
    except Exception as e:
        print(f"  Exception: {e}")
        return {"foods": [], "status": "error"}


def get_food_details(fdc_id: int) -> dict:
    """
    Get detailed food information including portions.

    :param fdc_id: USDA FoodData Central ID
    :return: Food details dict
    """
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"    Rate limited on details, waiting 60 seconds...")
            time.sleep(60)
            return get_food_details(fdc_id)
        return {}
    except Exception as e:
        print(f"    Exception getting details: {e}")
        return {}


def get_foods_batch(fdc_ids: list) -> dict:
    """
    Get detailed food information for multiple foods in one request.
    Uses POST /foods endpoint which accepts up to 20 fdcIds.

    :param fdc_ids: List of USDA FoodData Central IDs (max 20)
    :return: Dict mapping fdcId to food details
    """
    if not fdc_ids:
        return {}

    url = f"{BASE_URL}/foods"
    params = {"api_key": API_KEY}

    try:
        response = requests.post(url, params=params, json={"fdcIds": fdc_ids})
        if response.status_code == 200:
            foods = response.json()
            return {food["fdcId"]: food for food in foods}
        elif response.status_code == 429:
            print(f"    Rate limited on batch, waiting 60 seconds...")
            time.sleep(60)
            return get_foods_batch(fdc_ids)
        else:
            print(f"    Batch error {response.status_code}: {response.text[:100]}")
            return {}
    except Exception as e:
        print(f"    Exception in batch: {e}")
        return {}


def parse_amount(amount_str: str) -> float:
    """Parse an amount string, handling fractions like '1/4'."""
    if '/' in amount_str:
        num, denom = amount_str.split('/')
        return float(num) / float(denom)
    return float(amount_str)


def normalize_unit(unit: str) -> str:
    """
    Normalize a unit name to a standard singular form.
    E.g., 'cups' -> 'cup', 'cloves' -> 'clove', 'slices' -> 'slice'
    """
    unit = unit.lower().strip()
    # Common plural -> singular mappings
    if unit.endswith('ves'):  # loaves -> loaf
        return unit[:-3] + 'f'
    if unit.endswith('ies'):  # berries -> berry
        return unit[:-3] + 'y'
    if unit.endswith('es') and len(unit) > 3:  # slices -> slice, but not 'es' alone
        if unit[:-2].endswith(('c', 's', 'x', 'z', 'ch', 'sh')):
            return unit[:-2]
        return unit[:-1]  # removes just 'e' for cases like 'pieces' -> 'piec' -> keep 'piece'
    if unit.endswith('s') and len(unit) > 2:
        return unit[:-1]
    return unit


# Pattern to extract amount and unit from portion descriptions
# Matches: "1 cup", "1/4 cup", "0.5 clove", "3 large slices", "1 medium (2-3/4\" dia)"
PORTION_PATTERN = re.compile(
    r'^(\d+(?:/\d+)?(?:\.\d+)?)\s+'  # amount (required)
    r'(?:small|medium|large|extra large|extra-large)?\s*'  # optional size modifier
    r'([a-zA-Z][a-zA-Z\s]*?)(?:\s|$|,|\()',  # unit name (letters, capture until space/comma/paren)
    re.IGNORECASE
)


def add_portion(portions: dict, unit: str, modifier: str, grams_per_unit: float):
    """
    Add a portion to the nested portions dict.
    Structure: {unit: {modifier: grams_per_unit}}

    :param portions: The portions dict to modify
    :param unit: The unit name (e.g., "cup", "tablespoon")
    :param modifier: The modifier (e.g., "sifted", "cooked") or "" if none
    :param grams_per_unit: Grams per one unit
    """
    if unit not in portions:
        portions[unit] = {}
    # Only add if this modifier doesn't exist yet
    if modifier not in portions[unit]:
        portions[unit][modifier] = grams_per_unit


def extract_all_portions(food: dict) -> dict:
    """
    Extract all portion-to-gram mappings from food data.
    Returns a nested dict of unit -> modifier -> grams_per_unit.

    :param food: Food dict from list or details endpoint
    :return: Dict like {"cup": {"sifted": 85.0, "": 130.0}, "tablespoon": {"": 5.0}}
    """
    portions = {}

    # Check foodPortions (Foundation, SR Legacy, FNDDS details)
    if "foodPortions" in food:
        for portion in food["foodPortions"]:
            gram_weight = portion.get("gramWeight")
            if not gram_weight:
                continue

            amount = portion.get("amount", 1)
            if not amount or amount <= 0:
                continue

            unit = None
            modifier = ""

            # Get unit from measureUnit (preferred source)
            if portion.get("measureUnit"):
                unit_name = portion["measureUnit"].get("name", "")
                if unit_name and unit_name.lower() != "undetermined":
                    unit = normalize_unit(unit_name)

            # Get modifier from modifier field
            if portion.get("modifier"):
                mod_value = str(portion["modifier"])
                # Check if it's an FNDDS numeric code
                if mod_value.isdigit() and mod_value in FNDDS_PORTION_CODES:
                    # Parse the FNDDS code description for unit if we don't have one
                    desc = FNDDS_PORTION_CODES[mod_value].lower()
                    match = PORTION_PATTERN.match(desc)
                    if match:
                        if not unit:
                            unit = normalize_unit(match.group(2))
                        try:
                            amount = parse_amount(match.group(1))
                        except:
                            pass
                else:
                    # String modifier (e.g., "sifted", "cooked")
                    modifier = mod_value.lower().strip()
                    # If no measureUnit, modifier might be the unit itself (SR Legacy)
                    if not unit:
                        unit = normalize_unit(mod_value)
                        modifier = ""

            # Try portionDescription if still no unit
            if not unit and portion.get("portionDescription"):
                desc = portion["portionDescription"].lower()
                match = PORTION_PATTERN.match(desc)
                if match:
                    unit = normalize_unit(match.group(2))
                    try:
                        amount = parse_amount(match.group(1))
                    except:
                        pass

            if unit and unit != "undetermined":
                grams_per_unit = round(gram_weight / amount, 2)
                add_portion(portions, unit, modifier, grams_per_unit)

    # Check foodMeasures (from search/list results) -- Survey (FNDDS)
    if "foodMeasures" in food:
        for measure in food["foodMeasures"]:
            text = measure.get("disseminationText", "").lower()
            gram_weight = measure.get("gramWeight")

            if gram_weight and text:
                match = PORTION_PATTERN.match(text)
                if match:
                    try:
                        amount = parse_amount(match.group(1))
                        unit = normalize_unit(match.group(2))
                        if unit and amount > 0:
                            grams_per_unit = round(gram_weight / amount, 2)
                            # For foodMeasures, use empty modifier (no modifier info available)
                            add_portion(portions, unit, "", grams_per_unit)
                    except:
                        pass

    # Check householdServingFullText (Branded foods)
    if "householdServingFullText" in food:
        text = food["householdServingFullText"].lower()
        mass_serving_size = food.get("servingSize")
        mass_unit = food.get("servingSizeUnit", "").upper()

        if mass_serving_size and mass_unit in ["G", "GRAM", "GRAMS", "GRM", "GRMS", "GR", "GRS", "GS"]:
            match = PORTION_PATTERN.match(text)
            if match:
                try:
                    amount = parse_amount(match.group(1))
                    unit = normalize_unit(match.group(2))
                    if unit and amount > 0:
                        grams_per_unit = round(mass_serving_size / amount, 2)
                        # For householdServingFullText, use empty modifier
                        add_portion(portions, unit, "", grams_per_unit)
                except:
                    pass

    return portions


def save_progress(output_file: str, all_results: dict, current_data_type: str,
                  current_page: int, completed_types: list):
    """
    Save current progress to a file so processing can be resumed.
    Stores results for all data types.

    :param output_file: Base output file name
    :param all_results: Results dict for all data types
    :param current_data_type: Current data type being processed
    :param current_page: Current page number
    :param completed_types: List of completed data types
    """
    progress_file = output_file.replace(".json", "_progress.json")
    progress = {
        "current_data_type": current_data_type,
        "current_page": current_page,
        "completed": completed_types,
        "results": all_results,
        "saved_at": datetime.now().isoformat()
    }
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)

    total_results = sum(len(d.get("results", [])) for d in all_results.values())
    print(f"  [Progress saved: {current_data_type} page {current_page}, {total_results} total results]")


def load_progress(output_file: str) -> Optional[dict]:
    """
    Load progress from a previous run.

    :param output_file: Base output file name
    :return: Progress dict or None if no progress file exists
    """
    progress_file = output_file.replace(".json", "_progress.json")
    try:
        with open(progress_file, "r") as f:
            progress = json.load(f)
            completed = progress.get('completed', [])
            current = progress.get('current_data_type', 'unknown')
            current_page = progress.get('current_page', 0)
            total_results = sum(len(d.get("results", [])) for d in progress.get('results', {}).values())
            print(f"Found progress file from {progress['saved_at']}")
            print(f"  Completed: {completed if completed else 'none'}")
            print(f"  In progress: {current} (page {current_page})")
            print(f"  Total results so far: {total_results}")
            return progress
    except FileNotFoundError:
        return None


def process_all_foods(data_types: list, start_page: int = 1, max_pages: int = 0,
                      output_file: str = "usda_cups_complete.json", resume: bool = True) -> dict:
    """
    Process all foods in the USDA database.

    :param data_types: List of data types to process
    :param start_page: Starting page number
    :param max_pages: Maximum pages to process (0 = unlimited)
    :param output_file: Output file name (used for progress file)
    :param resume: Whether to resume from previous progress
    :return: Dict of results by data type
    """
    all_results = {}
    completed_types = []

    # Try to load previous progress
    progress = None
    if resume:
        progress = load_progress(output_file)
        if progress:
            all_results = progress.get("results", {})
            completed_types = progress.get("completed", [])

    for data_type in data_types:
        # Skip already completed data types
        if data_type in completed_types:
            print(f"\n{'='*60}")
            print(f"Skipping {data_type} (already completed)")
            print(f"{'='*60}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {data_type or 'All Types'}")
        print(f"{'='*60}")

        results = {}  # Dict of food_name -> {fdcId, portions}
        page = start_page
        total_foods = 0
        foods_with_portions = 0

        # Resume in-progress data type
        if progress and progress.get("current_data_type") == data_type:
            prev_data = all_results.get(data_type, {})
            results = prev_data.get("results", {})
            page = progress.get("current_page", start_page) + 1
            total_foods = prev_data.get("total_foods_processed", 0)
            foods_with_portions = len(results)
            print(f"Resuming from page {page} ({foods_with_portions} foods so far)...")

        while True:
            print(f"\nPage {page}...", end=" ", flush=True)
            response = get_foods_list(data_type, page)
            foods = response.get("foods", [])

            if not foods:
                print("No more foods.")
                break

            print(f"Got {len(foods)} foods")
            total_foods += len(foods)

            for food in foods:
                fdc_id = food.get("fdcId")
                print(f"  {fdc_id}")
                name = food.get("description", "").lower()

                # First try to get portions from list data
                portions = extract_all_portions(food)

                # If not found, fetch details from USDA
                if not portions and fdc_id:
                    details = get_food_details(fdc_id)
                    if details:
                        portions = extract_all_portions(details)
                    time.sleep(0.1)  # Rate limiting for details calls

                if portions:
                    foods_with_portions += 1
                    results[name] = {
                        "fdcId": fdc_id,
                        "data_type": data_type or food.get("dataType", "Unknown"),
                        "portions": portions
                    }
                    portions_list = []
                    for unit, modifiers in portions.items():
                        for mod, grams in modifiers.items():
                            if mod:
                                portions_list.append(f"{unit}({mod}): {grams}g")
                            else:
                                portions_list.append(f"{unit}: {grams}g")
                    print(f"    + {name}: {', '.join(portions_list)}")

            # Update all_results and save progress after each page
            all_results[data_type] = {
                "total_foods_processed": total_foods,
                "foods_with_portions": foods_with_portions,
                "results": results
            }
            save_progress(output_file, all_results, data_type, page, completed_types)

            # Check if we should continue
            if max_pages > 0 and page >= start_page + max_pages - 1:
                print(f"\nReached page limit ({max_pages} pages)")
                break

            if len(foods) < PAGE_SIZE:
                print("\nReached end of database.")
                break

            page += 1
            time.sleep(0.5)  # Rate limiting between pages

        # Mark this data type as completed
        completed_types.append(data_type)
        all_results[data_type] = {
            "total_foods_processed": total_foods,
            "foods_with_portions": foods_with_portions,
            "results": results
        }

        # Save progress and output file after completing each data type
        save_progress(output_file, all_results, data_type, page, completed_types)
        output_python_dict(all_results, output_file)
        print(f"\n{data_type}: Found {foods_with_portions} foods with portion data out of {total_foods}")
        print(f"Results saved to {output_file}")

    return all_results


def output_python_dict(results: dict, output_file: str):
    """
    Output results in Python dict format.
    New structure: {food_name: {fdcId, data_type, portions: {unit: grams}}}

    :param results: Results dict from process_all_foods
    :param output_file: Output file path
    """
    print("\n" + "=" * 80)
    print("PORTION DATA - All unit-to-gram mappings:")
    print("=" * 80 + "\n")

    # Merge all foods from all data types
    all_foods = {}
    for data_type, data in results.items():
        for name, food_data in data.get("results", {}).items():
            if name not in all_foods:
                all_foods[name] = food_data
            else:
                # Merge portions from different sources (nested structure)
                existing_portions = all_foods[name].get("portions", {})
                new_portions = food_data.get("portions", {})
                for unit, modifiers in new_portions.items():
                    if unit not in existing_portions:
                        existing_portions[unit] = modifiers
                    else:
                        # Merge modifiers for this unit
                        for mod, grams in modifiers.items():
                            if mod not in existing_portions[unit]:
                                existing_portions[unit][mod] = grams
                all_foods[name]["portions"] = existing_portions

    # Sort by name
    sorted_names = sorted(all_foods.keys())

    # Group by first letter for readability
    current_letter = ""
    for name in sorted_names:
        first_letter = name[0].upper() if name else "?"
        if first_letter != current_letter:
            current_letter = first_letter
            print(f"\n# === {current_letter} ===")

        food_data = all_foods[name]
        portions = food_data.get("portions", {})
        # Format: unit(modifier): grams or unit: grams if no modifier
        portions_list = []
        for unit in sorted(portions.keys()):
            modifiers = portions[unit]
            for mod in sorted(modifiers.keys()):
                grams = modifiers[mod]
                if mod:
                    portions_list.append(f"{unit}({mod}): {grams}g")
                else:
                    portions_list.append(f"{unit}: {grams}g")
        print(f'"{name}": {{{", ".join(portions_list)}}}')

    print(f"\n\nTotal unique foods with portion data: {len(all_foods)}")

    # Count unique units across all foods
    all_units = set()
    for food_data in all_foods.values():
        all_units.update(food_data.get("portions", {}).keys())
    print(f"Unique units found: {len(all_units)}")
    print(f"Units: {sorted(all_units)}")

    # Save to file
    with open(output_file, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_unique_foods": len(all_foods),
            "unique_units": sorted(all_units),
            "by_data_type": results,
            "all_foods": all_foods
        }, f, indent=2)
    print(f"Full results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract all portion-to-gram mappings from USDA FoodData Central database"
    )
    parser.add_argument(
        "--data-type",
        choices=["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded", "all"],
        default="all",
        help="Data type to process (default: all)"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting page number (default: 1)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max pages to process, 0 for unlimited (default: 0)"
    )
    parser.add_argument(
        "--output",
        default="usda_cups_complete.json",
        help="Output file name (default: usda_cups_complete.json)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh instead of resuming from previous progress"
    )

    args = parser.parse_args()

    # Determine data types to process
    if args.data_type == "all":
        # Process all data types including Branded
        # Note: Branded has 380k+ foods and will take many hours
        data_types = ["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded"]
    else:
        data_types = [args.data_type]

    resume = not args.no_resume

    print("=" * 80)
    print("USDA FoodData Central - Complete Portion Extractor")
    print("=" * 80)
    print(f"Data types: {data_types}")
    print(f"Starting page: {args.start}")
    print(f"Page limit: {args.limit if args.limit > 0 else 'unlimited'}")
    print(f"Output file: {args.output}")
    print(f"Resume from progress: {resume}")

    # Process foods
    results = process_all_foods(data_types, args.start, args.limit, args.output, resume)

    # Output results
    output_python_dict(results, args.output)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_processed = sum(d.get("total_foods_processed", 0) for d in results.values())
    total_with_portions = sum(d.get("foods_with_portions", 0) for d in results.values())

    print(f"Total foods processed: {total_processed}")
    print(f"Foods with portion data: {total_with_portions}")
    print(f"Percentage: {100 * total_with_portions / total_processed:.1f}%" if total_processed > 0 else "N/A")


if __name__ == "__main__":
    main()
