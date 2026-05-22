import random
from collections import defaultdict

import pandas as pd


# =========================
# LOAD DATA
# =========================

food_df = pd.read_csv("food_selected2.csv")

if "desc_lower" not in food_df.columns:
    food_df["desc_lower"] = food_df["Description"].astype(str).str.lower()


# =========================
# BASIC HELPERS
# =========================

def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    return round(bmi, 2)


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obese"


def build_long_term_state(user_profile):
    weight = user_profile["weight"]
    height = user_profile["height"]

    bmi = calculate_bmi(weight, height)

    raw_conditions = user_profile.get("health_condition", [])
    if isinstance(raw_conditions, str):
        raw_conditions = [raw_conditions]

    health_conditions = [str(c).lower().strip() for c in raw_conditions]

    return {
        "age": user_profile["age"],
        "pcos": user_profile.get("pcos", False),
        "pregnant": user_profile.get("pregnant", False),
        "cycle_phase": user_profile.get("cycle_phase"),
        "health_condition": raw_conditions,
        "health_conditions": health_conditions,
        "bmi": bmi,
        "bmi_status": classify_bmi(bmi),
    }


# =========================
# RULES / MAPS
# =========================

NUTRITION_RULES = {
    "bmi": {
        "Overweight": {
            "increase": ["Fiber", "Protein"],
            "reduce": ["Sugar", "Refined carbs", "Trans Fat"],
        },
        "Obese": {
            "increase": ["Fiber", "Protein"],
            "reduce": ["Sugar", "Refined carbs", "Trans Fat"],
        },
        "Underweight": {
            "increase": ["Protein", "Healthy Fats", "Complex carbs"],
            "reduce": [],
        },
    },
    "pcos": {
        "increase": ["Magnesium", "Fiber", "Omega-3", "Vitamin D", "Protein"],
        "reduce": ["Sugar", "Refined carbs"],
    },
    "diabetes": {
        "increase": ["Fiber", "Magnesium", "Protein", "Omega-3"],
        "reduce": ["Sugar", "Refined carbs"],
    },
    "hypertension": {
        "increase": ["Potassium", "Magnesium", "Calcium", "Fiber"],
        "reduce": ["Sodium", "Saturated Fat", "Trans Fat"],
    },
}

nutrient_food_sources = {
    "Omega-3": ["salmon", "tuna", "walnuts", "flax seeds"],
    "Vitamin D": ["milk", "egg", "salmon", "yogurt"],
    "Vitamin B12": ["egg", "milk", "yogurt", "tuna", "chicken"],
}

nutrient_map = {
    "Protein": "Data.Protein",
    "Iron": "Data.Major Minerals.Iron",
    "Magnesium": "Data.Major Minerals.Magnesium",
    "Zinc": "Data.Major Minerals.Zinc",
    "Calcium": "Data.Major Minerals.Calcium",
    "Vitamin B6": "Data.Vitamins.Vitamin B6",
}

food_group_map = {
    "plant_protein": "protein",
    "animal_protein": "protein",
    "vegetable": "vegetable",
    "fruit": "fruit",
    "carb": "carb",
    "grain": "carb",
    "oil": "fat",
    "nut": "fat",
    "seed": "fat",
    "fat": "fat",
    "diary": "dairy",
    "dairy": "dairy",
}

category_limits = {
    "protein": 4,
    "vegetable": 5,
    "fruit": 4,
    "carb": 4,
    "fat": 3,
    "dairy": 2,
}

food_df["food_group_ai"] = food_df["food_group"].map(food_group_map)

nutrient_max = {}
for col in nutrient_map.values():
    if col in food_df.columns:
        nutrient_max[col] = food_df[col].max()


# =========================
# FOOD DISPLAY
# =========================

def clean_display(name):
    name = str(name).lower()

    if "goat" in name and "milk" in name:
        return "Goat milk (whole)" if "whole" in name else "Goat milk"

    if "almond" in name and "milk" in name:
        return "Almond milk"

    if name.startswith("egg"):
        if "white" in name:
            return "Egg white"
        if "yolk" in name:
            return "Egg yolk"
        return "Egg (whole)"

    if "yogurt" in name:
        if "nonfat" in name or "fat free" in name:
            return "Yogurt (nonfat)"
        if "low fat" in name or "1%" in name:
            return "Yogurt (low fat)"
        if "greek" in name:
            return "Greek yogurt"
        return "Yogurt"

    if "milk" in name:
        if "fat free" in name or "skim" in name or "nonfat" in name:
            return "Milk (skim - fat free)"
        if "low fat" in name or "1%" in name:
            return "Milk (1% - low fat)"
        if "reduced fat" in name or "2%" in name:
            return "Milk (2% - reduced fat)"
        if "whole" in name:
            return "Milk (whole)"
        return "Milk"

    if "cheese" in name:
        return "Cheese"

    return name.split(",")[0].strip().capitalize()


# =========================
# LIMITATIONS / EXPLANATION
# =========================

def generate_limitations(state, daily_state):
    limitations = {"reduce": [], "moderate": []}

    conditions = state.get("health_conditions", [])
    phase = (state.get("cycle_phase") or "").lower()
    activity = daily_state.get("activity_level")
    stress = daily_state.get("stress_score", 0)

    if "diabetes" in conditions:
        limitations["reduce"] += ["refined carbs", "sweets", "sugar"]

    if state.get("pcos"):
        limitations["reduce"] += ["sugar", "refined carbs"]

    if state.get("bmi_status") in ["Overweight", "Obese"]:
        limitations["reduce"] += ["sugar", "refined carbs"]

    if phase == "luteal":
        limitations["moderate"] += ["caffeine"]
        limitations["reduce"] += ["high sugar foods"]

    if phase == "menstrual":
        limitations["reduce"] += ["high sugar foods"]

    if activity == "low":
        limitations["reduce"] += ["refined carbs"]
        limitations["moderate"] += ["red meat", "cheese"]

    if stress >= 7:
        limitations["moderate"] += ["caffeine", "red meat"]

    if state.get("pregnant"):
        limitations["moderate"] += ["caffeine", "cheese"]
        limitations["reduce"] += ["energy drinks"]

    if not limitations["reduce"]:
        limitations["reduce"] = ["ultra-processed foods"]

    if not limitations["moderate"]:
        limitations["moderate"] = ["excess sugar", "fried foods"]

    limitations["reduce"] = list(dict.fromkeys([x.lower() for x in limitations["reduce"]]))
    limitations["moderate"] = list(dict.fromkeys([x.lower() for x in limitations["moderate"]]))

    return limitations


def generate_explanation(state, daily_state):
    explanation = []

    phase = (state.get("cycle_phase") or "").lower()
    conditions = state.get("health_conditions", [])

    if state.get("pregnant"):
        explanation.append("Pregnancy → increased need for protein, iron, calcium, and essential nutrients")

    if state.get("pcos"):
        explanation.append("PCOS → prioritize fiber and omega-3 foods like vegetables, nuts, and fish")

    if "diabetes" in conditions:
        explanation.append("Diabetes → reduce sugar and refined carbs while focusing on fiber and protein")

    if "hypertension" in conditions:
        explanation.append("Hypertension → reduce sodium and choose heart-friendly foods")

    if daily_state.get("stress_score", 0) >= 7:
        explanation.append("High stress → focus on magnesium-rich foods like walnuts, seeds, and leafy greens")

    if daily_state.get("hydration") == "low":
        explanation.append("Low hydration → add water-rich foods")

    if daily_state.get("sleep_hours", 8) <= 3:
        explanation.append("Very low sleep → reduce caffeine and add calming herbal teas")

    if daily_state.get("activity_level") == "low":
        explanation.append("Low activity → reduce refined carbs to avoid excess energy storage")

    if phase == "menstrual":
        explanation.append("Menstrual phase → increase iron-rich foods like spinach and legumes")
    elif phase == "follicular":
        explanation.append("Follicular phase → supports energy, iron, and B vitamins")
    elif phase == "luteal":
        explanation.append("Luteal phase → support magnesium, calcium, and reduce high sugar foods")

    if state.get("bmi_status") == "Underweight":
        explanation.append("Underweight → increase calorie-dense and nutrient-rich foods")
    elif state.get("bmi_status") == "Overweight":
        explanation.append("Overweight BMI → prioritize fiber, lean protein, and low-fat dairy for fullness")
    elif state.get("bmi_status") == "Obese":
        explanation.append("Obese BMI → prioritize low-impact nutrition choices with fiber and lean protein")

    if not explanation:
        explanation.append("This plan supports a balanced daily nutrition routine")

    return explanation


# =========================
# SCORING
# =========================

def calculate_priority_nutrients(state, daily_state):
    increase = defaultdict(int)
    reduce = defaultdict(int)

    bmi_status = state.get("bmi_status")

    if bmi_status in NUTRITION_RULES["bmi"]:
        for nutrient in NUTRITION_RULES["bmi"][bmi_status]["increase"]:
            increase[nutrient] += 1
        for nutrient in NUTRITION_RULES["bmi"][bmi_status]["reduce"]:
            reduce[nutrient] += 1

    if state.get("pcos"):
        increase["Fiber"] += 3
        increase["Magnesium"] += 3
        increase["Omega-3"] += 2
        increase["Vitamin D"] += 2
        increase["Protein"] += 2
        reduce["Sugar"] += 3
        reduce["Refined carbs"] += 3

    for condition in state.get("health_conditions", []):
        if condition in NUTRITION_RULES:
            for nutrient in NUTRITION_RULES[condition]["increase"]:
                increase[nutrient] += 2
            for nutrient in NUTRITION_RULES[condition]["reduce"]:
                reduce[nutrient] += 2

    age = state.get("age", 0)

    if age <= 40:
        increase["Calcium"] += 1
        increase["Vitamin D"] += 1
    elif age <= 50:
        increase["Vitamin B12"] += 1
    else:
        increase["Calcium"] += 2
        increase["Vitamin D"] += 2
        increase["Vitamin B12"] += 2

    stress = daily_state.get("stress_score", 0)
    sleep = daily_state.get("sleep_hours", 8)
    mood = daily_state.get("mood", "good")
    activity = daily_state.get("activity_level", "moderate")
    hydration = daily_state.get("hydration", "good")

    if stress >= 8:
        increase["Magnesium"] += 3
        increase["Vitamin B6"] += 2
        increase["Zinc"] += 2
    elif stress >= 5:
        increase["Magnesium"] += 2
        increase["Vitamin B6"] += 1

    if sleep <= 5:
        increase["Magnesium"] += 2
        increase["Vitamin B6"] += 1

    if mood == "low":
        increase["Magnesium"] += 1
        increase["Omega-3"] += 1
        increase["Vitamin B6"] += 1

    if activity == "high":
        increase["Protein"] += 2
        increase["Iron"] += 1
    elif activity == "moderate":
        increase["Protein"] += 1

    if hydration == "low":
        increase["Potassium"] += 1

    phase = (state.get("cycle_phase") or "").lower()

    if state.get("pregnant"):
        increase["Iron"] += 3
        increase["Calcium"] += 3
        increase["Protein"] += 2
        increase["Folate"] += 4
        increase["Vitamin B6"] += 2
        increase["Vitamin B12"] += 2
        increase["Vitamin D"] += 2
        increase["Omega-3"] += 2
        reduce["Sugar"] += 1
        reduce["Caffeine"] += 1

    elif phase == "menstrual":
        increase["Iron"] += 3
        increase["Magnesium"] += 2
        increase["Potassium"] += 1
        increase["Omega-3"] += 1

    elif phase == "luteal":
        increase["Magnesium"] += 2
        increase["Calcium"] += 2
        increase["Vitamin B6"] += 2
        increase["Potassium"] += 1
        increase["Omega-3"] += 1
        reduce["Sugar"] += 1
        reduce["Caffeine"] += 1

    return dict(increase), dict(reduce)


def categorize_scores(scores):
    categories = {
        "high_priority": [],
        "focus_area": [],
        "support_level": [],
    }

    for nutrient, score in scores.items():
        if score >= 4:
            categories["high_priority"].append(nutrient)
        elif score >= 2:
            categories["focus_area"].append(nutrient)
        else:
            categories["support_level"].append(nutrient)

    return categories


def get_nutrient_weight(nutrient, categories):
    if nutrient in categories["high_priority"]:
        return 3.0
    if nutrient in categories["focus_area"]:
        return 2.0
    return 1.2


def calculate_food_score(row, increase_list, reduce_list, categories, state):
    score = 0
    name = str(row.get("desc_lower", "")).lower()

    for nutrient in increase_list:
        col = nutrient_map.get(nutrient)

        if col and col in row and nutrient_max.get(col, 0):
            score += (row[col] / nutrient_max[col]) * get_nutrient_weight(nutrient, categories)

        if nutrient in nutrient_food_sources:
            if any(keyword in name for keyword in nutrient_food_sources[nutrient]):
                score += get_nutrient_weight(nutrient, categories)

    if "Data.Sugar Total" in row:
        score -= (row["Data.Sugar Total"] / 100) * 3

    if state.get("bmi_status") == "Underweight":
        if any(x in name for x in ["avocado", "olive oil", "walnuts", "almonds", "pumpkin seeds", "flax seeds"]):
            score += 3

    if state.get("pregnant"):
        if "egg" in name:
            score += 2
        if "salmon" in name:
            score += 1.5
        if "milk" in name and "almond" not in name:
            score += 1.2

    if any(x in name for x in ["cake", "soda", "candy", "syrup"]):
        score -= 3

    if any(x in name for x in ["cheese", "processed"]):
        score -= 1.5

    return score


# =========================
# RECOMMENDATION BUILDERS
# =========================

def filter_foods(df, limitations):
    filtered = df.copy()
    reduce_list = limitations.get("reduce", [])

    if any("sugar" in x for x in reduce_list):
        filtered = filtered[~filtered["desc_lower"].str.contains("cake|sweet|syrup|candy|soda", na=False)]

    if any("refined carbs" in x for x in reduce_list):
        filtered = filtered[~filtered["desc_lower"].str.contains("white bread|cake|cookie", na=False)]

    return filtered


def get_top_foods(df, limitations, top_n=5):
    selected = []
    used = set()

    ranked = df.sort_values("score", ascending=False)

    for _, row in ranked.iterrows():
        name = str(row["desc_lower"])
        display = clean_display(row["Description"])
        base = display.lower()

        if base in used:
            continue

        if any(blocked in name for blocked in limitations.get("reduce", [])):
            continue

        selected.append(display)
        used.add(base)

        if len(selected) >= top_n:
            break

    return selected


def recommend_foods_by_category(df, limitations, state, daily_state):
    ranked = df.sort_values("score", ascending=False)
    recommendations = {}

    for category, limit in category_limits.items():
        foods = ranked[ranked["food_group_ai"] == category].copy()

        if category == "dairy":
            if state.get("bmi_status") in ["Overweight", "Obese"] or daily_state.get("activity_level") == "low":
                foods = foods[foods["desc_lower"].str.contains("low fat|skim|nonfat|fat free|yogurt|milk", na=False)]

        selected = []
        used = set()

        for _, row in foods.iterrows():
            raw = str(row["desc_lower"])
            name = clean_display(row["Description"])
            base = name.lower()

            if base in used:
                continue

            if "red meat" in limitations.get("moderate", []) and any(x in raw for x in ["beef", "lamb", "veal"]):
                continue

            if category == "carb" and any(x in raw for x in ["white bread", "cake", "cookie"]):
                continue

            selected.append(name)
            used.add(base)

            if len(selected) >= limit:
                break

        if category == "fruit":
            special = []

            if daily_state.get("hydration") == "low":
                special += ["Watermelon", "Strawberry", "Grapefruit"]

            if daily_state.get("mood") == "low":
                special += ["Strawberry", "Banana"]

            special = list(dict.fromkeys(special))

            for fruit in reversed(special):
                if fruit not in selected:
                    selected.insert(0, fruit)

            selected = selected[:limit]

        recommendations[category] = selected

    return recommendations


def recommend_herbal_tea(state, daily_state, limitations):
    teas = []

    if daily_state.get("stress_score", 0) >= 7:
        teas += ["Chamomile", "Lavender"]

    teas += ["Spearmint"]

    if daily_state.get("activity_level") == "low" and "caffeine" not in limitations.get("moderate", []):
        teas += ["Green tea"]

    return list(dict.fromkeys(teas))[:3]


def build_recommendation(state, daily_state, df):
    increase_scores, reduce_scores = calculate_priority_nutrients(state, daily_state)
    categories = categorize_scores(increase_scores)

    increase_list = (
        categories["high_priority"]
        + categories["focus_area"]
        + categories["support_level"]
    )

    reduce_list = list(reduce_scores.keys())

    limitations = generate_limitations(state, daily_state)

    filtered_df = filter_foods(df, limitations).copy()

    filtered_df["score"] = filtered_df.apply(
        lambda row: calculate_food_score(
            row,
            increase_list,
            reduce_list,
            categories,
            state,
        ),
        axis=1,
    )

    top_foods = get_top_foods(filtered_df, limitations)
    foods = recommend_foods_by_category(filtered_df, limitations, state, daily_state)
    teas = recommend_herbal_tea(state, daily_state, limitations)
    why = generate_explanation(state, daily_state)

    return {
        "top_foods": top_foods,
        "foods": foods,
        "herbal_teas": teas,
        "limitations": limitations,
        "why": why,
    }


# =========================
# MEALS LOGIC
# =========================

def prioritize_items(items, preferred):
    preferred_items = [x for x in items if x in preferred]
    other_items = [x for x in items if x not in preferred]
    return preferred_items + other_items


def apply_limitations(recommended, result, state=None):
    adjusted = {k: list(v) for k, v in recommended.items()}

    reduce_list = [str(x).lower().strip() for x in result.get("limitations", {}).get("reduce", [])]
    moderate_list = [str(x).lower().strip() for x in result.get("limitations", {}).get("moderate", [])]

    limitations = reduce_list + moderate_list

    def remove_items(category, blocked):
        adjusted[category] = [
            f for f in adjusted.get(category, [])
            if str(f).lower().strip() not in blocked
        ]

    if "refined carbs" in limitations:
        remove_items("carb", ["white bread", "cake", "cookies", "sweet cereal"])

    if "red meat" in limitations:
        remove_items("protein", ["beef", "lamb"])

    if "caffeine" in limitations:
        for category in adjusted:
            remove_items(category, ["coffee", "black tea", "green tea", "energy drinks"])

    if "cheese" in limitations:
        for category in adjusted:
            remove_items(category, ["cheese"])

    return adjusted


def adjust_recommended_foods(recommended, state):
    adjusted = {k: list(v) for k, v in recommended.items()}

    adjusted.setdefault("protein", [])
    adjusted.setdefault("fat", [])
    adjusted.setdefault("carb", [])
    adjusted.setdefault("dairy", [])
    adjusted.setdefault("vegetable", [])
    adjusted.setdefault("fruit", [])

    if "Egg (whole)" not in adjusted["protein"]:
        adjusted["protein"].append("Egg (whole)")

    if "Olive oil" not in adjusted["fat"]:
        adjusted["fat"].insert(0, "Olive oil")

    bmi_status = state.get("bmi_status", "").lower()

    if bmi_status in ["overweight", "obese"]:
        adjusted["protein"] = prioritize_items(
            adjusted["protein"],
            ["Egg (whole)", "Chicken breast", "Tuna", "Black beans", "Kidney beans", "Pinto beans", "White beans"],
        )
        adjusted["carb"] = prioritize_items(
            adjusted["carb"],
            ["Oatmeal", "Quinoa", "Barley"],
        )

    return adjusted


def safe_choice(options, used_foods=None):
    if not options:
        return None

    if used_foods is None:
        used_foods = set()

    available = [f for f in options if f not in used_foods]
    if not available:
        available = options

    selected = random.choice(available)
    used_foods.add(selected)
    return selected


def split_foods_by_meal(recommended, state):
    breakfast = {
        "protein": [f for f in recommended.get("protein", []) if "egg" in f.lower()],
        "dairy": recommended.get("dairy", []),
        "carb": [f for f in recommended.get("carb", []) if "quinoa" not in f.lower()],
        "fruit": recommended.get("fruit", []),
        "vegetable": recommended.get("vegetable", []),
        "fat": [],
    }

    lunch = {
        "protein": [f for f in recommended.get("protein", []) if "egg" not in f.lower()],
        "carb": [f for f in recommended.get("carb", []) if "oat" not in f.lower()],
        "vegetable": recommended.get("vegetable", []),
        "fat": [f for f in recommended.get("fat", []) if "oil" in f.lower() or "avocado" in f.lower()],
    }

    snack = {
        "fruit": recommended.get("fruit", []),
        "dairy": recommended.get("dairy", []),
        "fat": [
            f for f in recommended.get("fat", [])
            if "seed" in f.lower() or "walnut" in f.lower() or "almond" in f.lower() or "nut" in f.lower()
        ],
    }

    dinner = {
        "protein": [f for f in recommended.get("protein", []) if "egg" not in f.lower()],
        "vegetable": recommended.get("vegetable", []),
        "carb": [f for f in recommended.get("carb", []) if "oat" not in f.lower()],
        "fat": [f for f in recommended.get("fat", []) if "oil" in f.lower() or "avocado" in f.lower()],
    }

    return {
        "breakfast": breakfast,
        "lunch": lunch,
        "snack": snack,
        "dinner": dinner,
    }

def build_day_plan(meals, state=None, daily_state=None):
    used_foods = set()
    day_plan = {}

    activity_level = ""
    if daily_state:
        activity_level = daily_state.get("activity_level", "").lower()

    allow_carb = activity_level in ["moderate", "high"]

    # -------- BREAKFAST: lighter breakfast --------
    day_plan["breakfast"] = [
        safe_choice(meals["breakfast"]["dairy"], used_foods),
        safe_choice(meals["breakfast"]["fruit"], used_foods),
    ]

    if allow_carb:
        day_plan["breakfast"].append(
            safe_choice(meals["breakfast"]["carb"], used_foods)
        )

    if not any(day_plan["breakfast"]):
        day_plan["breakfast"] = [
            safe_choice(meals["breakfast"]["protein"], used_foods),
            safe_choice(meals["breakfast"]["vegetable"], used_foods),
        ]

    # -------- LUNCH: main balanced meal --------
    day_plan["lunch"] = [
        safe_choice(meals["lunch"]["protein"], used_foods),
        safe_choice(meals["lunch"]["carb"], used_foods),
        safe_choice(meals["lunch"]["vegetable"], used_foods),
    ]

    if meals["lunch"]["fat"]:
        day_plan["lunch"].append(
            safe_choice(meals["lunch"]["fat"], used_foods)
        )

    # -------- SNACK --------
    day_plan["snack"] = [
        safe_choice(meals["snack"]["dairy"], used_foods),
        safe_choice(meals["snack"]["fruit"], used_foods),
    ]

    if not any(day_plan["snack"]):
        day_plan["snack"] = [
            safe_choice(meals["snack"]["fruit"], used_foods),
            safe_choice(meals["snack"]["fat"], used_foods),
        ]

    # -------- DINNER: lighter dinner --------
    day_plan["dinner"] = [
        safe_choice(meals["dinner"]["protein"], used_foods),
        safe_choice(meals["dinner"]["vegetable"], used_foods),
    ]

    if allow_carb:
        day_plan["dinner"].append(
            safe_choice(meals["dinner"]["carb"], used_foods)
        )

    if meals["dinner"]["fat"]:
        day_plan["dinner"].append(
            safe_choice(meals["dinner"]["fat"], used_foods)
        )

    # remove None values
    for meal in day_plan:
        day_plan[meal] = [
            food for food in day_plan[meal]
            if food is not None
        ]

    return day_plan

def name_meal(meal_name, foods):
    if not foods:
        return "Healthy Meal"

    text = " ".join(foods).lower()

    has_protein = any(k in text for k in ["chicken", "tuna", "salmon", "beans", "egg"])
    has_carb = any(k in text for k in ["oat", "quinoa", "barley", "potato"])
    has_fruit = any(k in text for k in ["banana", "orange", "apple", "berries", "strawberry"])
    has_dairy = any(k in text for k in ["yogurt", "milk"])
    has_fat = any(k in text for k in ["seeds", "walnuts", "almonds", "avocado", "olive oil"])

    if meal_name == "breakfast":
        if has_dairy and has_carb and has_fruit:
            return "Creamy Fruit Breakfast Bowl"
        return "Balanced Morning Plate"

    if meal_name == "lunch":
        if has_protein and has_carb:
            return "Protein & Grain Power Bowl"
        return "Balanced Lunch Plate"

    if meal_name == "snack":
        if has_fruit and has_dairy:
            return "Fruit Yogurt Snack"
        if has_fruit and has_fat:
            return "Fresh Crunch Snack"
        return "Light Smart Snack"

    if meal_name == "dinner":
        if has_protein and has_carb:
            return "Wholesome Dinner Plate"
        return "Light Healthy Dinner"

    return "Healthy Meal"


# =========================
# PUBLIC FUNCTIONS FOR FLASK
# =========================

def get_recommendation(user_profile, daily_state):
    state = build_long_term_state(user_profile)
    return build_recommendation(state, daily_state, food_df)

category_portion = {
    "protein": 1.2,
    "carb": 1.0,
    "vegetable": 1.0,
    "fruit": 0.8,
    "fat": 0.1,
    "dairy": 1.0,
}


def get_food_category(food_name, recommended):
    food_name = str(food_name).lower().strip()

    for category, foods in recommended.items():
        for food in foods:
            if food_name == str(food).lower().strip():
                return category

    return None


def get_food_calories(food_name, df):
    food_key = str(food_name).lower().strip()

    alias_map = {
        "egg (whole)": "egg",
        "yogurt (nonfat)": "yogurt",
        "yogurt (low fat)": "yogurt",
        "milk (2% - reduced fat)": "milk",
        "milk (1% - low fat)": "milk",
        "milk (skim - fat free)": "milk",
        "almond milk": "almond milk",
        "oat bran cereal": "oat bran",
        "chicken breast": "chicken breast",
    }

    search_key = alias_map.get(food_key, food_key)

    row = df[df["desc_lower"] == search_key]

    if row.empty:
        row = df[df["desc_lower"].str.contains(search_key, na=False, regex=False)]

    if row.empty:
        return None

    row = row.iloc[0]

    protein = row.get("Data.Protein", 0)
    carbs = row.get("Data.Carbohydrate", 0)
    fat = row.get("Data.Fat.Total Lipid", 0)

    calories = (protein * 4) + (carbs * 4) + (fat * 9)

    return round(calories, 1)


def calculate_meal_calories(day_plan, df, recommended):
    total_day = 0
    meals_calories = {}

    for meal_name, foods in day_plan.items():
        meal_total = 0

        for food in foods:
            base_calories = get_food_calories(food, df)

            if base_calories is None:
                continue

            category = get_food_category(food, recommended)
            factor = category_portion.get(category, 1.0)

            final_calories = base_calories * factor
            meal_total += final_calories

        meals_calories[meal_name] = round(meal_total, 1)
        total_day += meal_total

    total_day = round(total_day, 1)

    if total_day < 1200:
        note = "Total calories are too low. Consider increasing portions or adding an extra snack."
    elif total_day < 1500:
        note = "Calories are on the low side. Consider increasing protein or carb portions."
    else:
        note = "Calories look reasonable."

    return {
        "meals": meals_calories,
        "total_day_calories": total_day,
        "note": note,
    }
def get_recommendation_response(user_profile, daily_state):
    state = build_long_term_state(user_profile)

    result = build_recommendation(state, daily_state, food_df)

    recommended = result.get("foods", {})
    recommended = apply_limitations(recommended, result, state)
    recommended = adjust_recommended_foods(recommended, state)

    meals = split_foods_by_meal(recommended, state)
    day_plan = build_day_plan(meals, state, daily_state)

    meal_calories = calculate_meal_calories(day_plan, food_df, recommended)

    return {
        "daily_meal_plan": {
            "breakfast": {
                "title": name_meal("breakfast", day_plan.get("breakfast", [])),
                "foods": day_plan.get("breakfast", []),
                "calories": meal_calories["meals"].get("breakfast", 0),
            },
            "lunch": {
                "title": name_meal("lunch", day_plan.get("lunch", [])),
                "foods": day_plan.get("lunch", []),
                "calories": meal_calories["meals"].get("lunch", 0),
            },
            "snack": {
                "title": name_meal("snack", day_plan.get("snack", [])),
                "foods": day_plan.get("snack", []),
                "calories": meal_calories["meals"].get("snack", 0),
            },
            "dinner": {
                "title": name_meal("dinner", day_plan.get("dinner", [])),
                "foods": day_plan.get("dinner", []),
                "calories": meal_calories["meals"].get("dinner", 0),
            },
        },
        "daily_calories": {
            "total_day_calories": meal_calories["total_day_calories"],
            "note": meal_calories["note"],
        },
    }