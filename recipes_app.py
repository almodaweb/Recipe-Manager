import streamlit as st
import random
import datetime
import pandas as pd
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
        # Validation
        if not recipe_name or not ingredients or not instructions:
            st.warning("Please fill in all fields.")
        elif recipe_name.strip().lower() in existing_names:
            st.error(f"'{recipe_name}' already exists in your recipe book. Please enter a unique recipe name.")
        elif recipe_name.strip().isdigit():
            st.warning("Recipe name cannot be a number.")
        else:
            import re
            numbers = re.findall(r"\b\d*\.?\d+\b", ingredients) # to extract only numeric quantities
            has_negative = any(float(num) < 0 for num in numbers)

            if has_negative:
                st.error("Ingredients cannot contain negative quantities. Please check your input.")
            else:
                cleaned_ingredients = ", ".join(
                    ing.strip().capitalize() for ing in ingredients.split(",") if ing.strip()
                )

                add_recipe(recipe_name.strip(), category, cleaned_ingredients, prep_time, instructions.strip(), level, servings, rating)
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
            # Number input for servings
            desired_servings = st.number_input(
                "How many servings?",
                min_value=1,
                value=st.session_state.desired_servings,
                step=1
            )

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

            # Split ingredients 
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
            st.subheader("Combined Shopping List")
            st.text_area(
                "Ingredients Needed:",
                "\n".join(sorted(set(all_ingredients))),
                height=200,
                key="combined_list"  
            )
    else:
        st.warning("Please select at least one recipe to generate a shopping list.")