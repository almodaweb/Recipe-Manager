import datetime
import random
import csv
import json
import re
import fractions

def add_recipe(recipe_name, category, ingredients, prep_time, instructions, level, servings=1, rating=0, cooking_history=None):
    """
    Adds a new recipe to recipes.csv.

    Parameters:
    - recipe_name (str): name of recipe
    - category (str): breakfast, lunch, dinner, or dessert
    - ingredients (str): list of ingredients separated by commas
    - prep_time (int): preparation time in minutes
    - instructions (str): step-by-step cooking instructions
    - level (str): difficulty level (easy, medium, hard)
    - servings (int): number of servings
    - rating (float): rating on 0–5 scale
    - cooking_history (list): list of cooking dates
    """
    file_path = "recipes.csv"

    cooking_history = cooking_history or []

    # Check if file exists
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            file_empty = not first_line  # True if file is empty
    except FileNotFoundError:
        file_empty = True  # File doesn't exist yet

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if file_empty:
            writer.writerow(headers)
        writer.writerow([
            recipe_name, category, servings, ingredients, prep_time,
            instructions, level, rating, json.dumps(cooking_history)
        ])
 

def search_ingredient(ingredient, recipes):
    '''
    Returns a list of recipes that contain a given ingredient.

    Parameters:
    - ingredient (str): ingredient to search for
    - recipes (list): list of recipe dictionaries
    '''
    return [r for r in recipes if ingredient.lower() in r["Ingredients"].lower()]


def random_suggestion(recipes, recent_cutoff=7):
    """
    Suggests a random recipe that hasn't been cooked recently (within recent_cutoff days)
    based on the 'Cooking History' column in the CSV file.

    Parameters:
    - recipes (list): List of recipe dictionaries
    - recent_cutoff (int): number of days to exclude recently cooked recipes (set to 7)
    """
    today = datetime.date.today()
    candidates = [] # Empty list to store recipes that are eligible for suggestion

    for r in recipes:
        history_raw = r.get("Cooking History", "[]")
        try:
            history = json.loads(history_raw) if isinstance(history_raw, str) else history_raw
        except json.JSONDecodeError:
            history = []

        if not history: # never cooked before = add to candidates list
            candidates.append(r)
        else: # among cooked, what hasn't been cooked recently = add to candidates list
            try:
                last_date = datetime.datetime.strptime(history[-1], "%Y-%m-%d").date()
                if (today - last_date).days > recent_cutoff:
                    candidates.append(r)
            except ValueError:
                candidates.append(r)

    # return a random recipe
    return random.choice(candidates or recipes)


def shopping_list(selected_recipes):
    '''
    Generates a combined shopping list from selected recipe dictionaries.

    Parameter:
    - selected_recipes (list): list of recipe dictionaries selected by the user
    '''
    ingredients = []
    for recipe in selected_recipes:
        if "Ingredients" in recipe and recipe["Ingredients"]:
            items = [i.strip() for i in recipe["Ingredients"].split(",") if i.strip()]
            ingredients.extend(items)
    return sorted(set(ingredients))


def store_recipes():
    """
    Loads all recipes from recipe.txt and returns them as a list of dictionaries, parsing JSON Cooking History.
    """
    recipes = []
    try:
        with open("recipes.csv", "r") as f:
            reader = csv.reader(f)
            next(reader, None)  
            for row in reader:
                if len(row) < 9:
                    continue
                try:
                    recipes.append({
                        "Recipe Name": row[0],
                        "Category": row[1],
                        "Servings": int(row[2]),
                        "Ingredients": row[3],
                        "Prep Time (mins)": int(row[4]),
                        "Instructions": row[5],
                        "Difficulty": row[6],
                        "Rating": float(row[7]),
                        "Cooking History": json.loads(row[8]) if row[8] else []
                    })
                except ValueError:
                    continue  
    except FileNotFoundError:
        # Create empty CSV with headers if not found
        with open("recipes.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Recipe Name", "Category", "Servings", "Ingredients",
                "Prep Time (mins)", "Instructions", "Difficulty",
                "Rating", "Cooking History"
            ])
    return recipes


def scale_ingredients(ingredients, original_servings, desired_servings):
    '''
    Scales ingredient quantities based on desired servings.

    Note:
    Only scales numeric quantities at the start of ingredient strings.

    Parameters:
    - ingredients (str): list of ingredients
    - original_servings (int): original serving size
    - desired_servings (int): the user’s desired serving size
    '''
    scale_factor = desired_servings / original_servings
    scaled = []

    for ingredient in ingredients.split(","):
        ingredient = ingredient.strip()
        # Match a number at the start (integer, decimal, or fraction) possibly followed by '-'
        match = re.match(r"^(\d+(?:/\d+)?(?:\.\d+)?)(?:-|\s+)?(.*)", ingredient)
        if match:
            qty_str = match.group(1)
            rest = match.group(2).strip()
            try:
                qty = float(fractions.Fraction(qty_str))
                qty_scaled = round(qty * scale_factor, 2)
                scaled.append(f"{qty_scaled} {rest}".strip())
            except ValueError:
                # If parsing fails, leave as is
                scaled.append(ingredient)
        else:
            scaled.append(ingredient)

    return ", ".join(scaled)


def update_cooking_history(recipe_name, date_str):
    """
    Updates an existing recipe by appending a new cooking date.

    Parameters:
    - recipe_name (str): name of the recipe to update
    - date_str (str): date string to add to cooking history
    """
    recipes = store_recipes()
    for r in recipes:
        if r["Recipe Name"] == recipe_name:
            if "Cooking History" not in r:
                r["Cooking History"] = []
            r["Cooking History"].append(date_str)
            break
    with open("recipes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Recipe Name", "Category", "Servings", "Ingredients",
            "Prep Time (mins)", "Instructions", "Difficulty",
            "Rating", "Cooking History"
        ])
        for r in recipes:
            writer.writerow([
                r["Recipe Name"],
                r["Category"],
                r["Servings"],
                r["Ingredients"],
                r["Prep Time (mins)"],
                r["Instructions"],
                r["Difficulty"],
                r["Rating"],
                json.dumps(r.get("Cooking History", []))
            ])