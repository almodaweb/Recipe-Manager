import streamlit as st
import random
import datetime
import pandas as pd
import re
from collections import defaultdict
from recipes import (
    add_recipe,
    store_recipes,
    update_cooking_history,
    search_ingredient,
    random_suggestion,
    scale_ingredients
)

st.title("Digital Recipe Manager")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Add a New Recipe",
    "Search by Ingredient",
    "View All Recipes",
    "Random Recipe Suggestion",
    "Generate Shopping List"
])

# Load recipes 
recipes = store_recipes()
existing_names = [r["Recipe Name"].strip().lower() for r in recipes]
      
import re
import fractions

import re
import fractions
import streamlit as st

## Add a new recipe        
with tab1:
    st.header("Add a New Recipe")

    recipe_name = st.text_input("Recipe name:")
    category = st.selectbox("Category:", ["Breakfast", "Lunch", "Dinner", "Dessert"])
    servings = st.number_input("Servings:", min_value=1, value=1)
    ingredients = st.text_area("Ingredients (comma-separated):")
    prep_time = st.number_input("Preparation time (mins):", min_value=1)
    instructions = st.text_area("Instructions:")
    level = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
    rating = st.slider("Rating:", 0, 5, 1)
    
    if st.button("Add Recipe"):
        # Basic validation
        if not recipe_name or not ingredients or not instructions:
            st.warning("Please fill in all fields.")
        elif recipe_name.strip().lower() in existing_names:
            st.error(f"'{recipe_name}' already exists in your recipe book. Please enter a unique recipe name.")
        elif recipe_name.strip().isdigit():
            st.warning("Recipe name cannot be a number.")
        else:
            ingredient_list = [ing.strip() for ing in ingredients.split(",") if ing.strip()]
            has_negative = False
            cleaned_ingredients = []

            for ing in ingredient_list:
                # Handle formats like 4-eggs
                ing = re.sub(r"^(-?\d+(?:/\d+)?(?:\.\d+)?)-", r"\1 ", ing)

                # Extract numeric part at start of string
                match = re.match(r"^\s*(-?\d+(?:/\d+)?(?:\.\d+)?)", ing)
                if match:
                    try:
                        qty = float(fractions.Fraction(match.group(1)))
                        if qty < 0:
                            has_negative = True
                    except:
                        st.warning(f"Could not parse quantity for ingredient: {ing}")
                
                cleaned_ingredients.append(ing.capitalize())

            if has_negative:
                st.warning("Ingredients cannot contain negative quantities. Please correct your input.")
            else:
                final_ingredients = ", ".join(cleaned_ingredients)
                add_recipe(
                    recipe_name.strip(),
                    category,
                    final_ingredients,
                    prep_time,
                    instructions.strip(),
                    level,
                    servings,
                    rating
                )
                st.success(f"{recipe_name} was added successfully!")


## Search by ingredient
with tab2:
    st.header("Search Recipes by Ingredient")
    ing = st.text_input("Enter an ingredient:")
    
    if st.button("Search"):
        if ing.strip():
            found = search_ingredient(ing, recipes)
            if found:
                st.success(f"Found {len(found)} recipe(s) containing '{ing}'.")
                st.dataframe(pd.DataFrame(found))
            else:
                st.warning(f"No recipes found containing '{ing}'.")
        else:
            st.error("Please enter an ingredient before searching.")


## View all recipes           
with tab3:
    st.header("All Recipes")

    if recipes:
        df = pd.DataFrame(recipes)[["Recipe Name", "Category", "Prep Time (mins)", "Difficulty", "Rating"]]
        st.dataframe(df)

        recipe_names = df["Recipe Name"].tolist()
        selected = st.selectbox("Select recipe:", [""] + recipe_names)

        if selected:
            recipe = next(r for r in recipes if r["Recipe Name"] == selected)
            st.write(f"**Category:** {recipe['Category']}")
            st.write(f"**Difficulty:** {recipe['Difficulty']}")
            st.write(f"**Prep Time:** {recipe['Prep Time (mins)']} mins")
            st.write(f"**Servings:** {recipe['Servings']}")
            st.write(f"**Rating:** {recipe['Rating']}")

            st.write("**Ingredients:**")
            st.text(recipe["Ingredients"])

            st.write("**Instructions:**")
            st.text(recipe["Instructions"])

            # Restrict to current date or past dates 
            today = datetime.date.today()
            cooked_date = st.date_input("Date cooked:", max_value=today)

            if st.button("Add to Cooking History"):
                if cooked_date > today:
                    st.error("You cannot log a future date.")
                else:
                    date_str = cooked_date.strftime("%Y-%m-%d")
                    update_cooking_history(selected, date_str)
                    st.success(f"Added {date_str} to cooking history!")

            st.subheader("Cooking History")

            # Reload recipe
            recipe = next(r for r in store_recipes() if r["Recipe Name"] == selected)

            # Sort cooking history
            history_raw = recipe.get("Cooking History", [])
            try:
                history = json.loads(history_raw) if isinstance(history_raw, str) else history_raw
            except json.JSONDecodeError:
                history = []

            history = sorted(history, key=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"))

            if history:
                st.table(pd.DataFrame({"Cooked On": history}))
            else:
                st.info("No cooking history yet.")


## Random recipe suggestion 
with tab4:
    st.header("Random Recipe Suggestion")
    recipes = store_recipes()

    if recipes:
        # Initialize current recipe only once
        if "current_recipe" not in st.session_state:
            st.session_state.current_recipe = random_suggestion(recipes)
            st.session_state.desired_servings = st.session_state.current_recipe["Servings"]

        # Button to get a new recipe
        if st.button("Get New Suggestion"):
            st.session_state.current_recipe = random_suggestion(recipes)
            st.session_state.desired_servings = st.session_state.current_recipe["Servings"]

            # Reset checkboxes for new recipe
            for idx in range(50): 
                st.session_state.pop(f"{st.session_state.current_recipe['Recipe Name']}_{idx}", None)

        recipe = st.session_state.current_recipe

        # Display recipe info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(recipe["Recipe Name"])
            st.write(f"Category: {recipe['Category']}")
            st.write(f"Difficulty: {recipe['Difficulty']}")
            st.write(f"Preparation Time: {recipe['Prep Time (mins)']} mins")

            # Display instructions directly
            st.subheader("Instructions")
            st.write(recipe["Instructions"])

        with col2:
            # Number input for servings — stays persistent
            desired_servings = st.number_input(
                "How many servings?",
                min_value=1,
                value=st.session_state.desired_servings,
                step=1
            )

            # Update session state when user changes servings
            if desired_servings != st.session_state.desired_servings:
                st.session_state.desired_servings = desired_servings

            # Scale ingredients
            scaled_ingredients = scale_ingredients(
                recipe["Ingredients"],
                recipe["Servings"],
                desired_servings
            )

            st.subheader("Ingredients")
            ingredients_list = [ing.strip() for ing in scaled_ingredients.split(",") if ing.strip()]
            for idx, ingredient in enumerate(ingredients_list):
                st.checkbox(ingredient, key=f"{recipe['Recipe Name']}_{idx}")

    else:
        st.info("No recipes in the collection yet!")

## Generate shopping list 
with tab5:
    st.header("Generate Shopping List")

    recipes = store_recipes()
    recipe_names = [r["Recipe Name"] for r in recipes]

    selected_names = st.multiselect("Select recipes to include:", recipe_names)

    if selected_names:
        selected_recipes = [r for r in recipes if r["Recipe Name"] in selected_names]

        all_ingredients = []

        for idx, recipe in enumerate(selected_recipes):
            st.markdown(f"### {recipe['Recipe Name']}")
            st.write(f"Ingredients per serving (default: {recipe['Servings']} servings):")

            ingredients_list = [i.strip() for i in recipe["Ingredients"].split(",") if i.strip()]
            st.text_area(
                "Ingredients",
                "\n".join(ingredients_list),
                height=100,
                key=f"ingredients_{idx}"  
            )

            all_ingredients.extend(ingredients_list)

        # Combined shopping list
        if st.button("Generate Combined Shopping List"):
            combined_dict = defaultdict(float)

            for ing in all_ingredients:
                # Separate quantity from ingredient name
                ing_clean = ing.replace("-", " ")  # handle cases like "4-eggs"
                match = re.match(r"^\s*(\d+(?:/\d+)?(?:\.\d+)?)\s+(.*)$", ing_clean)
                if match:
                    qty_str, name = match.groups()
                    try:
                        qty = float(fractions.Fraction(qty_str))
                    except:
                        qty = 0
                    # Normalize name (keep original)
                    name = name.lower().strip()
                    combined_dict[name] += qty
                else:
                    # No numeric quantity, just add as 1
                    combined_dict[ing.lower().strip()] += 1

            # Build final list with pluralization
            final_list = []
            for name, qty in combined_dict.items():
                display_name = name
                if qty != 1 and not name.endswith("s"):
                    display_name += "s"
                final_list.append(f"{round(qty, 2)} {display_name}")

            st.subheader("Combined Shopping List")
            st.text_area(
                "Ingredients Needed:",
                "\n".join(final_list),
                height=200,
                key="combined_list"
            )

    else:
        st.warning("Please select at least one recipe to generate a shopping list.")
