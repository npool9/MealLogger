#!/usr/bin/env python3
"""
USDA FoodData Central - Complete Food Database Cup Measurement Extractor

This script iterates through ALL foods in the USDA FoodData Central API
and extracts grams-per-cup measurements when available.

The USDA database contains ~400,000+ foods across multiple data types:
- Foundation: ~2,000 foods (high-quality, detailed nutrient data)
- SR Legacy: ~8,000 foods (Standard Reference, comprehensive)
- FNDDS: ~9,000 foods (survey data with portions)
- Branded: ~380,000+ foods (commercial products)

Usage:
    python search_usda_cups.py [--data-type TYPE] [--start PAGE] [--limit PAGES]

    Options:
        --data-type   Foundation, SR Legacy, FNDDS, or Branded (default: all)
        --start       Starting page number (default: 1)
        --limit       Max pages to process, 0 for unlimited (default: 0)
        --output      Output file name (default: usda_cups_complete.json)

Requirements:
    - requests library
    - api_keys.json file with "usda" key containing your API key

Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html
"""

import json
import requests
import time
import argparse
from typing import Optional
from datetime import datetime

# Load API key
with open("api_keys.json", "r") as f:
    API_KEY = json.load(f)["usda"]

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
PAGE_SIZE = 200  # Max allowed by API


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


def extract_cup_measurement(food: dict) -> Optional[tuple]:
    """
    Extract grams-per-cup measurement from food data.

    :param food: Food dict from list or details endpoint
    :return: Tuple of (grams_per_cup, portion_description) or None
    """
    cup_keywords = ["cup", "cups", "c "]

    # Check foodPortions
    if "foodPortions" in food:
        for portion in food["foodPortions"]:
            gram_weight = portion.get("gramWeight")
            if not gram_weight:
                continue

            # Build description from various fields
            desc = ""
            amount = portion.get("amount", 1)

            # Try portionDescription first
            if portion.get("portionDescription"):
                desc = portion["portionDescription"].lower()

            # Try modifier (SR Legacy format)
            elif portion.get("modifier"):
                desc = f"{amount} {portion['modifier']}".lower()

            # Try measureUnit
            elif portion.get("measureUnit"):
                unit_name = portion["measureUnit"].get("name", "")
                desc = f"{amount} {unit_name}".lower()

            # Check if it's a cup measurement
            if any(kw in desc for kw in cup_keywords):
                # Normalize to 1 cup
                grams_per_cup = gram_weight / amount if amount else gram_weight
                return (round(grams_per_cup, 1), desc)

    # Check foodMeasures (from search/list results)
    if "foodMeasures" in food:
        for measure in food["foodMeasures"]:
            text = measure.get("disseminationText", "").lower()
            gram_weight = measure.get("gramWeight")

            if gram_weight and any(kw in text for kw in cup_keywords):
                # Try to extract amount from text like "1 cup" or "0.5 cup"
                if "1 cup" in text or text.strip() == "cup":
                    return (round(gram_weight, 1), text)
                # For other amounts, we'd need to parse - skip for now
                return (round(gram_weight, 1), text)

    return None


def process_all_foods(data_types: list, start_page: int = 1, max_pages: int = 0) -> dict:
    """
    Process all foods in the USDA database.

    :param data_types: List of data types to process
    :param start_page: Starting page number
    :param max_pages: Maximum pages to process (0 = unlimited)
    :return: Dict of results by data type
    """
    all_results = {}

    for data_type in data_types:
        print(f"\n{'='*60}")
        print(f"Processing: {data_type or 'All Types'}")
        print(f"{'='*60}")

        results = []
        page = start_page
        total_foods = 0
        foods_with_cups = 0

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
                name = food.get("description", "").lower()

                # First try to get cup measurement from list data
                cup_data = extract_cup_measurement(food)

                # If not found, fetch details
                if cup_data is None and fdc_id:
                    details = get_food_details(fdc_id)
                    if details:
                        cup_data = extract_cup_measurement(details)
                    time.sleep(0.1)  # Rate limiting for details calls

                if cup_data:
                    grams, portion_desc = cup_data
                    foods_with_cups += 1
                    results.append({
                        "fdcId": fdc_id,
                        "name": name,
                        "grams_per_cup": grams,
                        "portion_description": portion_desc,
                        "data_type": data_type or food.get("dataType", "Unknown")
                    })
                    print(f"  + {name}: {grams}g/cup")

            # Check if we should continue
            if max_pages > 0 and page >= start_page + max_pages - 1:
                print(f"\nReached page limit ({max_pages} pages)")
                break

            if len(foods) < PAGE_SIZE:
                print("\nReached end of database.")
                break

            page += 1
            time.sleep(0.5)  # Rate limiting between pages

        all_results[data_type or "All"] = {
            "total_foods_processed": total_foods,
            "foods_with_cup_measurements": foods_with_cups,
            "results": results
        }

        print(f"\n{data_type or 'All'}: Found {foods_with_cups} foods with cup measurements out of {total_foods}")

    return all_results


def output_python_dict(results: dict, output_file: str):
    """
    Output results in Python dict format.

    :param results: Results dict from process_all_foods
    :param output_file: Output file path
    """
    print("\n" + "=" * 80)
    print("PYTHON DICT FORMAT - Add to INGREDIENT_GRAMS_PER_CUP:")
    print("=" * 80 + "\n")

    all_foods = []
    for data_type, data in results.items():
        all_foods.extend(data["results"])

    # Sort by name and remove duplicates (keep first occurrence)
    seen = set()
    unique_foods = []
    for food in sorted(all_foods, key=lambda x: x["name"]):
        if food["name"] not in seen:
            seen.add(food["name"])
            unique_foods.append(food)

    # Group by first letter for readability
    current_letter = ""
    for food in unique_foods:
        first_letter = food["name"][0].upper() if food["name"] else "?"
        if first_letter != current_letter:
            current_letter = first_letter
            print(f"\n    # === {current_letter} ===")

        # Convert to int if it's a whole number
        grams = int(food["grams_per_cup"]) if food["grams_per_cup"] == int(food["grams_per_cup"]) else food["grams_per_cup"]
        print(f'    "{food["name"]}": {grams},')

    print(f"\n\nTotal unique foods with cup measurements: {len(unique_foods)}")

    # Save to file
    with open(output_file, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_unique_foods": len(unique_foods),
            "by_data_type": results,
            "unique_foods": unique_foods
        }, f, indent=2)
    print(f"Full results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract cup measurements from entire USDA FoodData Central database"
    )
    parser.add_argument(
        "--data-type",
        choices=["Foundation", "SR Legacy", "FNDDS", "Branded", "all"],
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

    args = parser.parse_args()

    # Determine data types to process
    if args.data_type == "all":
        # Process all data types including Branded
        # Note: Branded has 380k+ foods and will take many hours
        data_types = ["Foundation", "SR Legacy", "FNDDS", "Branded"]
    else:
        data_types = [args.data_type]

    print("=" * 80)
    print("USDA FoodData Central - Complete Cup Measurement Extractor")
    print("=" * 80)
    print(f"Data types: {data_types}")
    print(f"Starting page: {args.start}")
    print(f"Page limit: {args.limit if args.limit > 0 else 'unlimited'}")
    print(f"Output file: {args.output}")

    # Process foods
    results = process_all_foods(data_types, args.start, args.limit)

    # Output results
    output_python_dict(results, args.output)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_processed = sum(d["total_foods_processed"] for d in results.values())
    total_with_cups = sum(d["foods_with_cup_measurements"] for d in results.values())
    print(f"Total foods processed: {total_processed}")
    print(f"Foods with cup measurements: {total_with_cups}")
    print(f"Percentage: {100 * total_with_cups / total_processed:.1f}%" if total_processed > 0 else "N/A")


if __name__ == "__main__":
    main()
