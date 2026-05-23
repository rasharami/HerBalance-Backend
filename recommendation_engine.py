#!/usr/bin/env python
# coding: utf-8

# In[565]:


def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    return round(bmi, 2)


# In[566]:


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# In[567]:


priority_weight = {
    "Very High": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}


# In[568]:


def build_long_term_state(user_profile):

    # ---- Calculate BMI properly ----
    weight = user_profile["weight"]
    height = user_profile["height"]

    bmi = weight / ((height / 100) ** 2)

    # ---- BMI Classification ----
    def classify_bmi(bmi):
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    # ---- Normalize health conditions ----
    raw_conditions = user_profile.get("health_condition", [])

    if isinstance(raw_conditions, str):
        raw_conditions = [raw_conditions]

    health_conditions = [c.lower() for c in raw_conditions]

    state = {
        "age": user_profile["age"],
        "pcos": user_profile.get("pcos", False), 
        "health_conditions": health_conditions,  # plural now
        "bmi": bmi,
        "bmi_status": classify_bmi(bmi)
    }

    return state


# In[569]:


NUTRITION_RULES = {

"bmi": {

    "Overweight": {
        "increase": ["Fiber", "Protein"],
        "reduce": ["Sugar", "Refined carbs", "Trans Fat"]
    },

    "Obese": {
        "increase": ["Fiber", "Protein"],
        "reduce": ["Sugar", "Refined carbs", "Trans Fat"]
    },

    "Underweight": {
        "increase": ["Protein", "Healthy Fats", "Complex carbs"],
        "reduce": []
    }
},

"pcos": {
    "increase": ["Magnesium", "Fiber", "Omega-3", "Vitamin D", "Protein"],
    "reduce": ["Sugar", "Refined carbs"]
},

"diabetes": {
    "increase": ["Fiber", "Magnesium", "Protein", "Omega-3"],
    "reduce": ["Sugar", "Refined carbs"]
},

"hypertension": {
    "increase": ["Potassium", "Magnesium", "Calcium", "Fiber"],
    "reduce": ["Sodium", "Saturated Fat", "Trans Fat"]
}

}


# In[570]:


from collections import defaultdict

def map_long_term_state(state):

    increase = defaultdict(int)
    reduce = defaultdict(int)

    # ---------------- BMI ----------------
    bmi_status = state["bmi_status"]

    if bmi_status in NUTRITION_RULES["bmi"]:
        for nutrient in NUTRITION_RULES["bmi"][bmi_status]["increase"]:
            increase[nutrient] += 1

        for nutrient in NUTRITION_RULES["bmi"][bmi_status]["reduce"]:
            reduce[nutrient] += 1


    # ---------------- PCOS ----------------
    if state["pcos"]:

        increase["Fiber"] += 3
        increase["Magnesium"] += 3
        increase["Omega-3"] += 2
        increase["Vitamin D"] += 2

        reduce["Sugar"] += 3
        reduce["Refined Carbs"] += 3


    # ---------------- Health Conditions ----------------
    conditions = state.get("health_conditions", [])
    print("Conditions:", conditions)

    for condition in conditions:
        if condition in NUTRITION_RULES:
            for nutrient in NUTRITION_RULES[condition]["increase"]:
                increase[nutrient] += 2

            for nutrient in NUTRITION_RULES[condition]["reduce"]:
                reduce[nutrient] += 2


    # ---------------- Age ----------------
    age = state["age"]

    if age < 18:
        increase["Calcium"] += 2
        increase["Vitamin D"] += 2
        increase["Iron"] += 1

    elif age <= 40:
        increase["Calcium"] += 1
        increase["Vitamin D"] += 1

    elif age <= 50:
        increase["Vitamin B12"] += 1

    elif age <60:
        increase["Calcium"] += 2
        increase["Vitamin D"] += 2
        increase["Vitamin B12"] += 2

    else:  # age >= 60
        increase["Calcium"] += 3
        increase["Vitamin D"] += 3
        increase["Vitamin B12"] += 4

        increase["Protein"] += 1
        increase["Magnesium"] += 1


    return {
        "increase": dict(increase),
        "reduce": dict(reduce)
    }


# In[571]:


def categorize_baseline(increase_dict):

    high_priority = []
    focus_area = []
    support_level = []

    for nutrient, score in increase_dict.items():

        if score >= 4:
            high_priority.append(nutrient)

        elif score >= 3:
            focus_area.append(nutrient)

        else:
            support_level.append(nutrient)

    return {
        "high_priority": high_priority,
        "focus_area": focus_area,
        "support_level": support_level
    }


# In[572]:


def categorize_reduce(reduce_dict):

    high_restriction = []
    moderate_restriction = []

    for nutrient in reduce_dict:

        if nutrient in ["Sugar", "Refined Carbs", "Sodium"]:
            high_restriction.append(nutrient)
        else:
            moderate_restriction.append(nutrient)

    return {
        "high_restriction": high_restriction,
        "moderate_restriction": moderate_restriction
    }


# In[573]:


user_profile = {
    "age": 20,
    "weight": 40,
    "height": 160,
    "pcos": False,
    "health_condition":[]

}


# In[574]:


bastate = build_long_term_state(user_profile)

# 1️⃣ Build state
state = build_long_term_state(user_profile)

# 2️⃣ Map nutrients
baseline = map_long_term_state(state)

# 3️⃣ Categorize
increase_categories = categorize_baseline(baseline["increase"])
reduce_categories = categorize_reduce(baseline["reduce"])

# 4️⃣ Print
print("STATE:", state)
print("Increase:", increase_categories)
print("Reduce:", reduce_categories)


# In[575]:


def apply_daily_modulation_proportional(baseline_scores, daily_state):

    increase = baseline_scores["increase"].copy()
    reduce = baseline_scores["reduce"].copy()

    def boost(nutrient, value):
        if value > 0:
            increase[nutrient] = increase.get(nutrient, 0) + value

    # ---------------- STRESS ----------------
    stress_score = daily_state.get("stress_score", 0)  # 0–10
    stress_boost = min(stress_score // 4, 2)

    boost("Magnesium", stress_boost)
    boost("Vitamin B6", stress_boost)
    boost("Zinc", stress_boost)

    # ---------------- SLEEP ----------------
    sleep_hours = daily_state.get("sleep_hours", 8)
    sleep_deficit = max(0, 7 - sleep_hours)
    sleep_boost = min(sleep_deficit // 2, 2)

    boost("Magnesium", sleep_boost)
    boost("Vitamin B6", sleep_boost)

    # ---------------- STRESS + SLEEP SYNERGY ----------------
    if stress_score >= 8 and sleep_hours <= 5:
        boost("Magnesium", 1)
        boost("Vitamin B6", 1)

    # ---------------- MOOD ----------------
    mood = daily_state.get("mood")

    if mood == "low":
        boost("Magnesium", 1)
        boost("Omega-3", 1)
        boost("Vitamin B6", 1)

    elif mood == "moderate":
        boost("Magnesium", 1)

    # neutral / good → no change

    # ---------------- ACTIVITY ----------------
    activity = daily_state.get("activity_level")

    if activity == "high":
        boost("Protein", 1)
        boost("Iron", 1)

    elif activity == "moderate":
        boost("Protein", 1)

    # ---------------- HYDRATION ----------------
    hydration = daily_state.get("hydration")

    if hydration == "low":
        boost("Potassium", 1)

    # ---------------- SCORE CAP ----------------
    MAX_SCORE = 5

    for nutrient in increase:
        increase[nutrient] = min(increase[nutrient], MAX_SCORE)

    for nutrient in reduce:
        reduce[nutrient] = min(reduce[nutrient], MAX_SCORE)

    return {
        "increase": increase,
        "reduce": reduce
    }


# In[576]:


user_profile = {
    "age": 30,
    "weight": 90,
    "height": 160,
    "pcos": True,
    "health_condition": []

}
daily_state = {
 "stress_score": 1,
 "sleep_hours": 3,
 "activity_level": "low",
 "hydration": "good",
 "mood": "low"
}
state = build_long_term_state(user_profile)

baseline = map_long_term_state(state)

final_scores = apply_daily_modulation_proportional(baseline, daily_state)

increase_categories = categorize_baseline(final_scores["increase"])
reduce_categories = categorize_reduce(final_scores["reduce"])

print("Increase:", increase_categories)
print("Reduce:", reduce_categories)


# In[577]:


def apply_cycle_layer(scores, state):

    increase = scores.get("increase", {}).copy()
    reduce = scores.get("reduce", {}).copy()

    age = state.get("age", 0)
    phase = (state.get("cycle_phase") or "").lower()
    pregnant = state.get("pregnant", False)

    def boost(nutrient, value):
        increase[nutrient] = increase.get(nutrient, 0) + value

    def restrict(nutrient, value):
        reduce[nutrient] = reduce.get(nutrient, 0) + value


    # =====================================================
    # 1️⃣ PREGNANCY (Independent Condition)
    # =====================================================
    if pregnant:

        boost("Iron", 3)
        boost("Calcium", 3)
        boost("Protein", 2)
        boost("Folate", 4)

        boost("Vitamin B6", 2)
        boost("Vitamin B12", 2)
        boost("Vitamin D", 2)

        boost("Omega-3", 2)
        boost("Vitamin C", 1)
        boost("Zinc", 1)

        restrict("Sugar", 1)
        restrict("Caffeine", 1)

        return {"increase": increase, "reduce": reduce}


    # =====================================================
    # 2️⃣ MENOPAUSE
    # =====================================================
    if age >= 55:

        boost("Calcium", 3)
        boost("Vitamin D", 2)
        boost("Magnesium", 2)

        boost("Protein", 2)
        boost("Omega-3", 1)
        boost("Potassium", 1)

        restrict("Sugar", 1)
        restrict("Salt", 1)
        restrict("Caffeine", 1)

        return {"increase": increase, "reduce": reduce}


    # =====================================================
    # 3️⃣ MENSTRUAL CYCLE PHASES
    # =====================================================

    if phase == "menstrual":

        boost("Iron", 3)
        boost("Magnesium", 2)
        boost("Potassium", 1)

        boost("Vitamin C", 1)
        boost("Omega-3", 1)


    elif phase == "follicular":

        boost("Iron", 1)
        boost("Zinc", 1)

        boost("Vitamin B6", 1)
        boost("Protein", 1)


    elif phase == "ovulation":

        boost("Zinc", 2)
        boost("Vitamin C", 1)
        boost("Omega-3", 1)


    elif phase == "luteal":

        boost("Magnesium", 2)
        boost("Calcium", 2)
        boost("Vitamin B6", 2)
        boost("Potassium", 1)
        boost("Omega-3", 1)

        restrict("Sugar", 1)
        restrict("Caffeine", 1)
        restrict("Salt", 1)


    return {"increase": increase, "reduce": reduce}


# In[578]:


#user
user_profile = {
    "age": 24,
    "weight": 60,
    "height": 165,
    "pcos": False,
    "health_condition": []
}

daily_state = {
    "stress_score": 3,
    "sleep_hours": 7,
    "activity_level": "moderate",
    "hydration": "good",
    "mood": "good"
}


# ============================================
# LAYER 1 — LONG TERM
# ============================================

state = build_long_term_state(user_profile)

# ✅ keep health conditions inside state
state["health_condition"] = user_profile.get("health_condition", [])

# Example: test pregnancy
state["pregnant"] =  False

# If not pregnant, assign cycle phase
if not state.get("pregnant") and state["age"] < 55:
    state["cycle_phase"] ="follicular"
else:
    state["cycle_phase"] = None

baseline = map_long_term_state(state)


# ============================================
# LAYER 2 — DAILY MODULATION
# ============================================

daily_scores = apply_daily_modulation_proportional(
    baseline,
    daily_state
)


# ============================================
# LAYER 3 — CYCLE / PREGNANCY LAYER
# ============================================

final_scores = apply_cycle_layer(
    daily_scores,
    state
)


# ============================================
# CATEGORIZATION
# ============================================

increase_categories = categorize_baseline(final_scores["increase"])
reduce_categories = categorize_reduce(final_scores["reduce"])


# ============================================
# EXPLANATION
# ============================================



# ============================================
# OUTPUT
# ============================================

print("=================================")
print("STATE:", state)

print("\n--- DAILY STATE ---")
for k, v in daily_state.items():
    print(f"{k}: {v}")

print("\n--- FINAL PRIORITIES ---")
print("Increase:", increase_categories)
print("Reduce:", reduce_categories)



print("=================================")


# In[579]:


priority_nutrients = (
    increase_categories["high_priority"] +
    increase_categories["focus_area"] +
    increase_categories["support_level"]
)

restricted_nutrients = (
    reduce_categories["high_restriction"] +
    reduce_categories["moderate_restriction"]
)


# In[580]:


import pandas as pd 
import numpy as np


# In[581]:


food_df = pd.read_csv("food_selected2.csv")


# In[582]:


food_df.columns


# In[583]:


PRIORITY_WEIGHTS = {
    "pregnancy": 3,
    "disease": 2,
    "bmi": 1,
    "daily": 0.5
}


# In[584]:


# 🔥 SMART FOOD MAPPING (for missing nutrients)
nutrient_food_sources = {
    "Omega-3": ["salmon", "tuna", "walnuts", "flax seeds"],
    "Vitamin D": ["milk", "egg", "salmon", "yogurt"],
    "Vitamin B12": ["egg", "milk", "yogurt", "tuna", "chicken"]
}


# In[585]:


nutrient_map = {
    "Protein": "Data.Protein",
    "Iron": "Data.Major Minerals.Iron",
    "Magnesium": "Data.Major Minerals.Magnesium",
    "Zinc": "Data.Major Minerals.Zinc",
    "Calcium": "Data.Major Minerals.Calcium",
    "Vitamin B6": "Data.Vitamins.Vitamin B6"
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
    "diary": "dairy"
}

# ------------------ CATEGORY LIMITS ------------------
category_limits = {
    "protein": 4,
    "vegetable": 5,
    "fruit": 4,
    "carb": 4,
    "fat": 3,
    "dairy": 2
}

# ------------------ FILTER LISTS ------------------
INGREDIENT_FOODS = ["garlic", "ginger", "spice", "seasoning", "herb"]

POPULAR_FOODS = [
    "broccoli", "carrot", "tomato", "cucumber",
    "zucchini", "banana", "apple", "orange", "spinach"
]


# In[586]:


food_df["food_group_ai"] = food_df["food_group"].map(food_group_map)

nutrient_max = {col: food_df[col].max() for col in nutrient_map.values()}


# In[587]:


def apply_energy_logic(state, increase_categories):
    if state.get("bmi_status") == "Underweight":
        increase_categories["high_priority"].append("Energy")
        increase_categories["support_level"].append("Healthy Fats")


# In[588]:


def folate_proxy_score(name):
    name = name.lower()

    if any(x in name for x in ["spinach", "kale", "lettuce"]):
        return 2
    if any(x in name for x in ["lentil", "chickpea", "bean"]):
        return 2
    if any(x in name for x in ["orange", "avocado"]):
        return 1
    if any(x in name for x in ["broccoli", "asparagus"]):
        return 1

    return 0


# In[589]:


def clean_food_df(food_df, reduce_categories):

    df = food_df.copy()

    if "Refined carbs" in reduce_categories["high_restriction"]:
        df = df[~df["desc_lower"].str.contains("bread", na=False)]

    if "Sugar" in reduce_categories["high_restriction"]:
        df = df[~df["desc_lower"].str.contains("cake|sweet|syrup", na=False)]

    return df


# In[590]:


def get_nutrient_weight(nutrient, increase_categories):

    if nutrient in increase_categories["high_priority"]:
        return 3.0
    elif nutrient in increase_categories["focus_area"]:
        return 2.0
    elif nutrient in increase_categories["support_level"]:
        return 1.2
    else:
        return 1


# In[591]:


def food_has_nutrient(row, nutrient):
    name = row["desc_lower"]

    # ✅ If in dataset → use column
    col = nutrient_map.get(nutrient)
    if col and col in row:
        if row[col] > 0:
            return True

    # 🔥 If NOT in dataset → use name matching
    if nutrient in nutrient_food_sources:
        for keyword in nutrient_food_sources[nutrient]:
            if keyword in name:
                return True

    return False


# In[592]:


def has_condition(state, condition_names):
    conditions = [
        c.strip().lower()
        for c in state.get("health_condition", [])
    ]

    return any(c in conditions for c in condition_names)


# In[593]:


def has_condition(state, condition_names):
    conditions = [
        c.strip().lower()
        for c in state.get("health_condition", [])
    ]

    return any(c in conditions for c in condition_names)


def calculate_food_score(row, increase_nutrients, reduce_nutrients,
                         nutrient_max, increase_categories, state):

    score = 0
    name = row["desc_lower"].lower()

    pregnant = state.get("pregnant", False)
    bmi_status = state.get("bmi_status")

    # ✅ Positive nutrients
    for nutrient in increase_nutrients:
        column = nutrient_map.get(nutrient)

        if column and column in row:
            weight = get_nutrient_weight(nutrient, increase_categories)
            score += (row[column] / nutrient_max.get(column, 1)) * weight

    # 🔥 ENERGY BOOST (UNDERWEIGHT)
    if bmi_status == "Underweight":
        if "Data.Fat.Total Lipid" in row:
            score += (row["Data.Fat.Total Lipid"] /
                      nutrient_max.get("Data.Fat.Total Lipid", 1)) * 2

    # 🔻 Negative nutrients
    for nutrient in reduce_nutrients:
        column = nutrient_map.get(nutrient)

        if column and column in row:
            score -= (row[column] / nutrient_max.get(column, 1)) * 3

    # 🔥 Sugar penalty
    if "Data.Sugar Total" in row:
        score -= (row["Data.Sugar Total"] / 100) * 3

    # 🔥 High-calorie foods boost (Underweight)
    if bmi_status == "Underweight":
        if any(x in name for x in [
            "avocado", "olive oil",
            "walnuts", "almonds", "pistachio", "hazelnut",
            "pumpkin seeds", "flax seeds"
        ]):
            score += 3.0

    # 🔥 PREGNANCY BOOST
    if pregnant:

        if "egg" in name:
            score += 2.0

        if "salmon" in name:
            score += 1.5

        if "milk" in name and "almond" not in name:
            score += 1.2

        if "almond milk" in name:
            score -= 0.5

    # 🔥 Dairy boost (Underweight)
    if bmi_status == "Underweight":
        if "yogurt" in name or "milk" in name:
            score += 1.5

    # ❌ General penalties
    if any(x in name for x in ["cheese", "processed"]):
        score -= 2.0

    # ⭐ Popular foods boost
    if any(x in name for x in POPULAR_FOODS):
        score += 0.3

    # ================= 🔥 LIMITATION PENALTIES =================

    # 🟠 MODERATE (Red meat)
    if any(x in name for x in ["beef", "lamb", "goat"]):
        if any("red meat" in x.lower() for x in reduce_nutrients):
            score *= 0.6

    # 🔴 HIGH restriction example (sugar)
    if any(x in name for x in ["cake", "soda", "candy"]):
        if any("sugar" in x.lower() for x in reduce_nutrients):
            score *= 0.3

    # 🤰 Extra pregnancy safety
    if pregnant:
        if any(x in name for x in ["beef", "lamb"]):
            score *= 0.7

    # 🫒 Olive oil priority for hypertension / cholesterol
    has_hypertension = has_condition(
        state,
        ["hypertension", "high blood pressure"]
    )

    has_cholesterol = has_condition(
        state,
        ["cholesterol", "hypertension"]
    )

    if has_hypertension or has_cholesterol:
        if "olive oil" in name:
            score += 4.0

        if any(x in name for x in ["butter", "ghee", "lard"]):
            score -= 3.0

    return score


# In[594]:


nutrient_to_food_map = {
    "Sugar": ["refined carbs", "sweets", "soft drinks"],
    "Caffeine": ["coffee", "black tea", "energy drinks"],
    "Saturated Fat": ["red meat", "butter", "cheese"],
    "Trans Fat": ["fried foods", "fast food"],
}


def generate_limitations(state, daily_state, reduce_scores=None):

    limitations = {"reduce": [], "moderate": []}

    conditions = state.get("health_conditions", [])
    phase = (state.get("cycle_phase") or "").lower()
    activity = daily_state.get("activity_level")
    stress = daily_state.get("stress_score", 0)

    has_condition = bool(conditions) or state.get("pcos")

    # =========================================================
    # 🧠 1. CORE LOGIC → FROM NUTRIENTS
    # =========================================================
    if reduce_scores:
        for nutrient, score in reduce_scores.items():
            foods = nutrient_to_food_map.get(nutrient, [])

            if score >= 2:
                limitations["reduce"].extend(foods)
            elif score > 0:
                limitations["moderate"].extend(foods)

    # =========================================================
    # 🔴 2. CONDITION-BASED RULES
    # =========================================================
    if "diabetes" in conditions:
        limitations["reduce"] += ["refined carbs", "sweets"]

    if state.get("pcos"):
        limitations["reduce"] += ["sugar"]

    # =========================================================
    # 🔴 3. CYCLE-BASED RULES
    # =========================================================
    if phase == "luteal":
        limitations["moderate"] += ["caffeine"]
        limitations["reduce"] += ["high sugar foods"]

    if phase == "menstrual":
        limitations["reduce"] += ["high sugar foods"]

    # =========================================================
    # 🔴 4. ACTIVITY-BASED RULE
    # =========================================================
    if activity == "low":
        limitations["reduce"] += ["refined carbs"]
        limitations["moderate"] += ["red meat", "cheese"]

    # =========================================================
    # 🔴 5. STRESS RULE
    # =========================================================
    if stress >= 7:
        limitations["moderate"] += ["caffeine", "red meat"]

    # =========================================================
    # 🔴 6. PREGNANCY SAFETY LAYER ✅ FIXED
    # =========================================================
    if state.get("pregnant"):
        limitations["moderate"] += ["caffeine", "cheese"]
        limitations["reduce"] += ["energy drinks"]

    # =========================================================
    # 🔵 7. FALLBACK LOGIC
    # =========================================================
    if not limitations["reduce"]:
        limitations["reduce"] = ["ultra-processed foods"]

    if not limitations["moderate"]:
        limitations["moderate"] = ["excess sugar", "fried foods"]

    # =========================================================
    # 🧹 8. CLEAN + NORMALIZE
    # =========================================================
    limitations["reduce"] = list(set(x.lower() for x in limitations["reduce"]))
    limitations["moderate"] = list(set(x.lower() for x in limitations["moderate"]))

    return limitations


# In[595]:


def clean_display(name):
    name = name.lower()

    # 🐐 GOAT MILK (before normal milk)
    if "goat" in name and "milk" in name:
        if "whole" in name:
            return "Goat milk (whole)"
        elif "low fat" in name or "1%" in name:
            return "Goat milk (1% - low fat)"
        else:
            return "Goat milk"

    # 🌰 ALMOND MILK
    if "almond" in name and "milk" in name:
        return "Almond milk"

    # 🥚 EGGS
    if name.startswith("egg"):
        if "white" in name:
            return "Egg white"
        elif "yolk" in name:
            return "Egg yolk"
        else:
            return "Egg (whole)"

    # 🥛 YOGURT
    if "yogurt" in name:
        if "nonfat" in name or "fat free" in name:
            return "Yogurt (nonfat)"
        elif "low fat" in name or "1%" in name:
            return "Yogurt (low fat)"
        elif "greek" in name:
            return "Greek yogurt"
        else:
            return "Yogurt"

    # 🥛 MILK
    if "milk" in name:
        if "fat free" in name or "skim" in name or "nonfat" in name:
            return "Milk (skim - fat free)"
        elif "low fat" in name or "1%" in name:
            return "Milk (1% - low fat)"
        elif "reduced fat" in name or "2%" in name:
            return "Milk (2% - reduced fat)"
        elif "whole" in name:
            return "Milk (whole)"
        else:
            return "Milk"

    # 🧀 CHEESE
    if "cheese" in name:
        return "Cheese"

    # 🌱 DEFAULT
    return name.split(",")[0].strip().capitalize()
import re

def get_top_foods(df, limitations, top_n=5, state=None, high_priority=None):

    df = df.copy()
    top = df.sort_values("score", ascending=False)

    selected_rows = []
    used = set()

    reduce_list = [x.lower() for x in limitations.get("reduce", [])]
    moderate_list = [x.lower() for x in limitations.get("moderate", [])]

    category_used = {
        "protein": 0,
        "dairy": 0,
        "vegetable": 0,
        "fat": 0,
        "other": 0
    }

    # ================= BASIC SELECTION =================
    for _, row in top.iterrows():

        name = row["desc_lower"]
        base = name.split(",")[0]
        category = row.get("food_group_ai", "other")

        if any(x in name for x in reduce_list):
            continue

        if any(x in name for x in ["beef", "lamb", "veal"]):
            if any("red meat" in x for x in moderate_list):
                continue

        if base in used:
            continue

        if category == "fat" and category_used["fat"] >= 1:
            continue

        if category == "protein" and category_used["protein"] >= 1:
            continue

        if category == "dairy" and category_used["dairy"] >= 1:
            continue

        selected_rows.append(row)
        used.add(base)
        category_used[category] = category_used.get(category, 0) + 1

        if len(selected_rows) >= top_n:
            break

    # ================= HELPER =================
    def pick_exact_food(keyword):
        pattern = rf"^{re.escape(keyword)}\b"
        match = df[df["desc_lower"].str.contains(pattern, regex=True, na=False)]
        if not match.empty:
            return match.iloc[0]
        return None

    # ================= FORCE IMPORTANT NUTRIENTS =================
    if high_priority:

        IMPORTANT = ["Omega-3", "Vitamin D", "Vitamin B12"]

        for nutrient in high_priority:

            if nutrient not in IMPORTANT:
                continue

            best_row = None

            if nutrient in nutrient_food_sources:
                for keyword in nutrient_food_sources[nutrient]:
                    match = df[df["desc_lower"].str.contains(keyword, na=False)]
                    if not match.empty:
                        best_row = match.iloc[0]
                        break

            if best_row is None:
                col = nutrient_map.get(nutrient)
                if col and col in df.columns:
                    best_row = df.sort_values(col, ascending=False).iloc[0]

            if best_row is None:
                continue

            base = best_row["desc_lower"].split(",")[0]

            if base in used:
                continue

            if any(x in best_row["desc_lower"] for x in reduce_list):
                continue

            selected_rows.insert(0, best_row)
            used.add(base)

    # ================= CATEGORY COVERAGE =================
    def ensure_category(keyword_list):
        for kw in keyword_list:
            match = df[df["desc_lower"].str.contains(kw, na=False)]
            if not match.empty:
                return match.iloc[0]
        return None

    if not any(r.get("food_group_ai") == "protein" for r in selected_rows):
        row = ensure_category(["tuna", "chicken"])
        if row is None:
            row = pick_exact_food("egg")
        if row is not None:
            selected_rows.insert(0, row)

    if not any("milk" in r["desc_lower"] or "yogurt" in r["desc_lower"] for r in selected_rows):
        row = ensure_category(["yogurt", "milk"])
        if row is not None:
            selected_rows.insert(0, row)

    if not any(r.get("food_group_ai") == "vegetable" for r in selected_rows):
        row = ensure_category(["spinach", "broccoli"])
        if row is not None:
            selected_rows.insert(0, row)

    if not any(r["desc_lower"].startswith("egg") for r in selected_rows):
        egg_row = pick_exact_food("egg")
        if egg_row is not None:
            selected_rows.insert(0, egg_row)

    # ================= FINAL CLEAN =================
    seen = set()
    final = []

    for r in selected_rows:
        base = r["desc_lower"].split(",")[0]
        if base not in seen:
            final.append(r)
            seen.add(base)

    # ================= ENSURE OLIVE OIL IN TOP PICKS =================
    if state is not None:
        has_hypertension = has_condition(
            state,
            ["hypertension", "high blood pressure"]
        )

        has_cholesterol = has_condition(
            state,
            ["cholesterol", "high cholesterol", "hypercholesterolemia"]
        )

        if has_hypertension or has_cholesterol:
            if not any("olive oil" in r["desc_lower"] for r in final):

                olive_row = df[df["desc_lower"].str.contains("olive oil", na=False)]

                if not olive_row.empty:
                    final.insert(0, olive_row.iloc[0])

    # ================= LIMIT FAT ITEMS IN TOP PICKS =================
    fat_count = 0
    balanced_final = []

    for r in final:
        category = r.get("food_group_ai", "other")

        if category == "fat":
            fat_count += 1

            if fat_count > 1:
                continue

        balanced_final.append(r)

    # refill if less than top_n
    for _, row in top.iterrows():
        base = row["desc_lower"].split(",")[0]

        if len(balanced_final) >= top_n:
            break

        if base not in [x["desc_lower"].split(",")[0] for x in balanced_final]:
            balanced_final.append(row)

    final = balanced_final

    return [clean_display(r["Description"]) for r in final[:top_n]]


# In[596]:


def get_dairy_preference(state, daily_state):
    bmi = state.get("bmi_status")
    activity = daily_state.get("activity_level")
    pregnant = state.get("pregnant", False)

    if pregnant:
        if activity == "low":
            return "low_fat"
        else:
            return "balanced"

    if bmi in ["Overweight", "Obese"]:
        return "low_fat"

    if bmi == "Underweight":
        return "full_fat"

    return "balanced"


# In[597]:


def recommend_foods_by_category(df, category_limits, limitations, state, daily_state):
    # ⭐ ADD proxy column
    df["folate_proxy"] = df["desc_lower"].apply(folate_proxy_score)

    ranked = df.sort_values("score", ascending=False)
    recommendations = {}

    moderate = [x.lower() for x in limitations["moderate"]]
    pregnant = state.get("pregnant", False)
    dairy_pref = get_dairy_preference(state, daily_state)

    for category, n in category_limits.items():
        foods = ranked[ranked["food_group_ai"] == category].copy()

        # ================= DAIRY CONTROL =================
        if category == "dairy":
            if "cheese" in moderate:
                foods = foods[~foods["desc_lower"].str.contains("cheese", na=False)]

            if dairy_pref == "low_fat":
                foods = foods[foods["desc_lower"].str.contains("low fat|skim", na=False)]
            elif dairy_pref == "full_fat":
                foods = foods[foods["desc_lower"].str.contains("whole|full fat", na=False)]

            yogurt = foods[foods["desc_lower"].str.contains("yogurt", na=False)]
            milk = foods[foods["desc_lower"].str.contains("milk", na=False)]

            foods = pd.concat([yogurt, milk, foods]).drop_duplicates()

        selected = []
        used_sources = set()

        # ================= MAIN LOOP =================
        for _, row in foods.iterrows():
            raw_name = row["desc_lower"]
            name = clean_display(raw_name)
            base_food = raw_name.split(",")[0]

            # Skip misplaced foods
            if "egg" in raw_name and category != "protein":
                continue

            if "spinach" in raw_name and category != "vegetable":
                continue

            # ⭐ Apply folate boost if pregnant
            if pregnant:
                if "Folate" in state.get("priority_nutrients", []):
                    if row["folate_proxy"] > 0:
                        if name not in selected:
                            selected.insert(0, name)
                        continue

            # ================= PROTEIN DIVERSITY =================
            if category == "protein":
                if "chicken" in raw_name and any("chicken" in f.lower() for f in selected):
                    continue

                if any(x in raw_name for x in ["salmon", "tuna", "shrimp"]):
                    if any(
                        any(x in f.lower() for x in ["salmon", "tuna", "shrimp"])
                        for f in selected
                    ):
                        continue

                has_plant = any(
                    any(x in f.lower() for x in ["beans", "lentils", "chickpeas"])
                    for f in selected
                )

                if len(selected) >= 2 and not has_plant:
                    if not any(x in raw_name for x in ["beans", "lentils", "chickpeas"]):
                        continue

            # ================= GENERAL FILTERING =================
            if any(x in raw_name for x in INGREDIENT_FOODS):
                continue

            if "red meat" in moderate and any(x in raw_name for x in ["beef", "lamb", "veal"]):
                continue

            if any(x in raw_name for x in ["white rice", "white bread"]):
                continue

            if "rice" in raw_name and "white" in raw_name:
                continue

            if category == "carb" and "bread" in raw_name:
                continue

            if category == "vegetable" and "corn" in raw_name:
                continue

            if base_food in used_sources:
                continue

            selected.append(name)
            used_sources.add(base_food)

            if len(selected) >= n:
                break

        # ================= ENSURE EGG IN PROTEIN =================
        if category == "protein" and pregnant:
            if not any("egg" in f.lower() for f in selected):
                egg_option = foods[foods["desc_lower"].str.contains("egg", na=False)]

                if not egg_option.empty:
                    if len(selected) >= n:
                        selected[-1] = clean_display(egg_option.iloc[0]["desc_lower"])
                    else:
                        selected.append(clean_display(egg_option.iloc[0]["desc_lower"]))

        # ================= SPECIAL FRUITS =================
        if category == "fruit":
            special_fruits = []

            # 💧 Hydration low
            if daily_state.get("hydration") == "low":
                special_fruits += [
                    "Watermelon",
                    "Strawberry",
                    "Grapefruit"
                ]

            # 😊 Mood low
            if daily_state.get("mood") == "low":
                special_fruits += [
                    "Strawberry",
                    "Banana"
                ]

            # 😴 Low sleep
            if daily_state.get("sleep_hours", 8) <= 6:
                special_fruits += [
                    "Banana"
                ]

            # Remove duplicates but keep order
            special_fruits = list(dict.fromkeys(special_fruits))

            # Put special fruits at the beginning
            for fruit in reversed(special_fruits):
                if fruit not in selected:
                    selected.insert(0, fruit)

            # Keep fruit section same limit
            selected = selected[:n]

        recommendations[category] = selected

    return recommendations


# In[598]:


def recommend_herbal_tea(state, daily_state, limitations):

    teas = []
    stress = daily_state.get("stress_score", 0)
    activity = daily_state.get("activity_level")

    moderate = [x.lower() for x in limitations["moderate"]]

    # 🌿 Stress-based
    if stress >= 7:
        teas += ["Chamomile", "Lavender"]

    # 🌿 Digestion
    teas += ["Spearmint"]

    # ⚡ Energy (if low activity & caffeine allowed)
    if activity == "low" and "caffeine" not in moderate:
        teas += ["Green tea"]

    return list(dict.fromkeys(teas))[:3]


# In[599]:


def add_pregnancy_folate_foods(recommendations, state):
    if not state.get("pregnant"):
        return recommendations

    folate_foods = {
        "vegetable": ["spinach", "kale", "broccoli"],
        "protein": ["lentils", "chickpeas"],   # ✅ correct
        "fruit": ["orange"],
        "fat": ["avocado"]
    }

    for category, foods in folate_foods.items():

        if category not in recommendations:
            continue

        existing = [f.lower() for f in recommendations[category]]

        for food in foods:
            if not any(food in item for item in existing):
                recommendations[category].insert(0, food)

        recommendations[category] = recommendations[category][:5]

    return recommendations


# In[600]:


def hydration_suggestions(daily_state):

    if daily_state.get("hydration") == "low":
        return ["Drink more water", "Herbal teas", "Cucumber"]

    return []


# In[601]:


def generate_explanation(state, daily_state, recommended_fruits=None):

    explanation = []

    if recommended_fruits is None:
        recommended_fruits = []

    phase = (state.get("cycle_phase") or "").lower()
    pregnant = state.get("pregnant", False)
    bmi_status = state.get("bmi_status")

    conditions = [
        c.strip().lower()
        for c in state.get("health_condition", [])
    ]

    has_diabetes = "diabetes" in conditions

    has_hypertension = (
        "hypertension" in conditions
        or "high blood pressure" in conditions
    )

    has_cholesterol = (
        "cholesterol" in conditions
        or "cholostrol" in conditions
    )

    # 🔥 Pregnancy
    if pregnant:
        explanation.append(
            "Pregnancy → increased need for protein, iron, calcium, and essential nutrients"
        )
        explanation.append(
            "Folate-rich foods like leafy greens and legumes support fetal neural development"
        )
        explanation.append(
            "Fresh fruits and vegetables → provide fiber, vitamins, and help reduce gestational diabetes risk"
        )

    # 🩺 Hypertension
    if has_hypertension:
        explanation.append(
            "Hypertension → reduce sodium intake to support healthy blood pressure"
        )
        explanation.append(
            "Olive oil → helps replace saturated fats and supports heart health"
        )

    # 🫒 Cholesterol
    if has_cholesterol:
        explanation.append(
            "Cholesterol → olive oil may support healthier fat balance"
        )

    # 🌿 Stress
    if daily_state.get("stress_score", 0) >= 7:
        explanation.append(
            "High stress → focus on magnesium-rich foods like walnuts, seeds, and leafy greens"
        )

        if has_hypertension:
            explanation.append(
                "Chamomile tea → may support relaxation and stress control"
            )

    # 🩸 Menstrual
    if phase == "menstrual":
        explanation.append(
            "Menstrual phase → increase iron-rich foods like spinach and legumes"
        )

    # 🌼 Follicular
    if phase == "follicular":
        explanation.append(
            "Follicular phase → supports energy, iron, and B vitamins"
        )

    # 🌸 PCOS
    if state.get("pcos"):
        if pregnant:
            explanation.append(
                "PCOS with pregnancy → prioritize balanced meals with protein, fiber, and healthy fats"
            )
        else:
            explanation.append(
                "PCOS → prioritize fiber and omega-3 foods like vegetables, nuts, and fish"
            )
            explanation.append(
                "Spearmint tea → may help support hormonal balance in PCOS"
            )

    # 🏃 Activity
    if daily_state.get("activity_level") == "low":
        explanation.append(
            "Low activity → reduce refined carbs to avoid excess energy storage"
        )

    # ⚖ BMI
    if bmi_status == "Underweight":
        explanation.append(
            "Underweight → increase calorie-dense and nutrient-rich foods"
        )

    elif bmi_status == "Overweight":
        explanation.append(
            "Overweight BMI → prioritize fiber, lean protein, and low-fat dairy for fullness"
        )

    # 💧 Hydration
    if daily_state.get("hydration") == "good":
        explanation.append(
            "Hydration is good → maintain balanced fluid intake"
        )

    elif daily_state.get("hydration") == "low":
        explanation.append(
            "Low hydration → add water-rich foods"
        )

    # 😴 Sleep
    if daily_state.get("sleep_hours", 0) <= 3:
        explanation.append(
            "Very low sleep → reduce caffeine and add calming herbal teas"
        )



    return explanation


# In[602]:


def calculate_nutrient_priorities(state, daily):

    scores = {}
    reduce = {}

    # ---------------- BMI ----------------
    if state.get("bmi_status") in ["Overweight", "Obese"]:
        scores['Fiber'] = scores.get('Fiber', 0) + 2 * PRIORITY_WEIGHTS["bmi"]
        scores['Protein'] = scores.get('Protein', 0) + 1 * PRIORITY_WEIGHTS["bmi"]

        reduce['Refined carbs'] = reduce.get('Refined carbs', 0) + 2
        reduce['Sugar'] = reduce.get('Sugar', 0) + 2

    # ---------------- DAILY ----------------
    if daily.get("activity_level") == "low" and not state.get("pregnant"):
        reduce['Refined carbs'] = reduce.get('Refined carbs', 0) + 1

    # ---------------- PREGNANCY ----------------
    if state.get("pregnant"):

        scores['Iron'] = scores.get('Iron', 0) + 2
        scores['Calcium'] = scores.get('Calcium', 0) + 2
        scores['Protein'] = scores.get('Protein', 0) + 2

        # ⭐ FIXED (Folate added correctly)
        scores['Folate'] = scores.get('Folate', 0) + 5

        scores['Vitamin B6'] = scores.get('Vitamin B6', 0) + 1 * PRIORITY_WEIGHTS["pregnancy"]
        scores['Omega-3'] = scores.get('Omega-3', 0) + 2 * PRIORITY_WEIGHTS["pregnancy"]

    return scores, reduce


# In[603]:


def build_recommendation(state, daily_state, food_df):

    # ================= 1. NUTRIENT PRIORITIES =================
    scores, reduce_scores = calculate_nutrient_priorities(state, daily_state)

    # ================= 2. LIMITATIONS =================
    limitations = generate_limitations(state, daily_state, reduce_scores)

    # ================= 3. CATEGORIZATION =================
    increase_categories = {
        "high_priority": [],
        "focus_area": [],
        "support_level": []
    }

    reduce_categories = {
        "high_restriction": [],
        "moderate_restriction": []
    }

    # ------------------ INCREASE ------------------
    for nutrient, score in scores.items():
        if score >= 5:
            increase_categories["high_priority"].append(nutrient)
        elif score >= 3:
            increase_categories["focus_area"].append(nutrient)
        else:
            increase_categories["support_level"].append(nutrient)

    # ------------------ REDUCE ------------------
    for nutrient, val in reduce_scores.items():
        if val >= 2:
            reduce_categories["high_restriction"].append(nutrient)
        else:
            reduce_categories["moderate_restriction"].append(nutrient)

    # ================= 4. DYNAMIC ADJUSTMENTS =================

    # 🔥 Stress
    stress_score = daily_state.get("stress_score", 0)

    if stress_score >= 8:
        increase_categories["high_priority"].append("Magnesium")
        increase_categories["focus_area"] += ["Vitamin B6", "Zinc"]

    elif stress_score >= 5:
        increase_categories["focus_area"].append("Magnesium")
        increase_categories["support_level"].append("Vitamin B6")

    # 🔥 Activity
    if daily_state.get("activity_level") == "low":
        reduce_categories["high_restriction"].append("Refined carbs")

    # 🔥 Energy (BMI-based)
    apply_energy_logic(state, increase_categories)

    # ================= 5. FLATTEN =================
    increase_list = (
        increase_categories["high_priority"]
        + increase_categories["focus_area"]
        + increase_categories["support_level"]
    )

    reduce_list = (
        reduce_categories["high_restriction"]
        + reduce_categories["moderate_restriction"]
    )

    # ================= 6. DATA CLEANING =================
    filtered_df = clean_food_df(food_df, reduce_categories)

    # ================= 7. SCORING =================
    filtered_df["score"] = filtered_df.apply(
        lambda row: calculate_food_score(
            row,
            increase_list,
            reduce_list,
            nutrient_max,
            increase_categories,
            state
        ),
        axis=1
    )

    # ================= 8. RECOMMENDATIONS =================
    top_foods = get_top_foods(
        filtered_df,
        limitations,
        state=state,
        high_priority=increase_categories["high_priority"]
)
    # 🔥 FIX: pass daily_state
    foods = recommend_foods_by_category(
        filtered_df,
        category_limits,
        limitations,
        state,
        daily_state   # ✅ IMPORTANT FIX
    )

    # 🔥 Pregnancy folate boost
    foods = add_pregnancy_folate_foods(foods, state)

    # ================= 9. EXTRAS =================
    teas = recommend_herbal_tea(state, daily_state, limitations)
    explanation = generate_explanation(state, daily_state)

    # ================= 10. OUTPUT =================
    return {
        "top_foods": top_foods,
        "foods": foods,
        "herbal_teas": teas,
        "limitations": limitations,
        "why": explanation
    }


# In[604]:


def display_recommendations(result):

    print("\n⭐ TOP PICKS")
    for f in result["top_foods"]:
        print(" •", f)

    print("\n🍽 FOOD RECOMMENDATIONS")
    for cat, foods in result["foods"].items():
        print("\n", cat.upper())
        for f in foods:
            print(" •", f)

    print("\n🍵 HERBAL TEAS")
    for t in result["herbal_teas"]:
        print(" •", t)

    print("\n⚠ LIMITATIONS")
    print("Reduce:", result["limitations"]["reduce"])
    print("Moderate:", result["limitations"]["moderate"])

    print("\n💡 WHY THIS PLAN")
    for w in result["why"]:
        print(" •", w)


# In[605]:


result = build_recommendation(state, daily_state, food_df)
display_recommendations(result)


# In[606]:


build_recommendation(state, daily_state, food_df)


# In[607]:


result = build_recommendation(state, daily_state, food_df)

recommended = result["foods"]

print(recommended.keys())

for category, foods in recommended.items():
    print("\n", category)
    print(foods)


# In[608]:


import random

def prioritize_items(items, preferred):
    preferred_items = [x for x in items if x in preferred]
    other_items = [x for x in items if x not in preferred]
    return preferred_items + other_items


# In[609]:


def apply_limitations(recommended, result, state=None):
    adjusted = {k: v.copy() for k, v in recommended.items()}

    reduce_list = [
        str(x).lower().strip()
        for x in result.get("limitations", {}).get("reduce", [])
    ]

    moderate_list = [
        str(x).lower().strip()
        for x in result.get("limitations", {}).get("moderate", [])
    ]

    limitations = reduce_list + moderate_list

    conditions = [
        str(c).lower().strip()
        for c in state.get("health_conditions", [])
    ] if state else []

    has_diabetes_or_pcos = (
        "diabetes" in conditions
        or state.get("pcos", False)
    ) if state else False

    bmi_status = state.get("bmi_status", "").lower() if state else ""

    def normalize_list(items):
        return [str(x).lower().strip() for x in items]

    high_sugar_foods = normalize_list(["Pineapple", "Mango", "Grapes"])
    refined_carb_foods = normalize_list(["White bread", "Cake", "Cookies", "Sweet cereal"])
    red_meat_foods = normalize_list(["Beef", "Lamb"])
    caffeine_foods = normalize_list(["Coffee", "Black tea", "Green tea", "Energy drinks"])
    high_sodium_foods = normalize_list(["Cheese", "Processed meat", "Sausage"])
    fried_foods = normalize_list(["French fries", "Fried chicken"])

    def remove_items(category, blocked):
        adjusted[category] = [
            f for f in adjusted.get(category, [])
            if str(f).lower().strip() not in blocked
        ]

    # Diabetes / PCOS: remove high-sugar fruits
    if has_diabetes_or_pcos and (
        "sweets" in limitations
        or "sugar" in limitations
        or "high sugar foods" in limitations
        or "excess sugar" in limitations
    ):
        remove_items("fruit", high_sugar_foods)

    # Overweight / Obese: reduce high-sugar fruits
    if bmi_status in ["overweight", "obese"]:
        remove_items("fruit", normalize_list(["Pineapple", "Mango"]))

    if "refined carbs" in limitations:
        remove_items("carb", refined_carb_foods)

    if "red meat" in limitations:
        remove_items("protein", red_meat_foods)

    if "caffeine" in limitations:
        for category in adjusted:
            remove_items(category, caffeine_foods)

    if "cheese" in limitations or "salt" in limitations or "sodium" in limitations:
        for category in adjusted:
            remove_items(category, high_sodium_foods)

    if "fried foods" in limitations or "ultra-processed foods" in limitations:
        for category in adjusted:
            remove_items(category, fried_foods)

    if "energy drinks" in limitations:
        for category in adjusted:
            remove_items(category, normalize_list(["Energy drinks"]))

    return adjusted


# In[610]:


def adjust_recommended_foods(recommended, state):
    adjusted = {k: v.copy() for k, v in recommended.items()}

    conditions = [c.lower() for c in state.get("conditions", [])]
    bmi_status = state.get("bmi_status", "").lower()
    is_pregnant = state.get("pregnant", False)
    is_menopause = state.get("menopause", False)

    if "protein" not in adjusted:
        adjusted["protein"] = []

    egg_option = "Egg (whole)"
    if egg_option not in adjusted["protein"]:
        adjusted["protein"].append(egg_option)

    if bmi_status == "underweight":
        adjusted["fat"] = prioritize_items(
            adjusted.get("fat", []),
            ["Avocado", "Walnuts", "Pumpkin seeds", "Flax seeds"]
        )

        adjusted["carb"] = prioritize_items(
            adjusted.get("carb", []),
            ["Oatmeal", "Oat bran cereal", "Quinoa", "Barley", "Sweet potato"]
        )

        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Beef", "Egg (whole)", "Chicken breast", "Kidney beans", "Black beans"]
        )

        adjusted["dairy"] = prioritize_items(
            adjusted.get("dairy", []),
            ["Milk (2% - reduced fat)", "Yogurt (low fat)", "Almond milk"]
        )

    if bmi_status in ["overweight", "obese"]:
        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Egg (whole)", "Chicken breast", "Tuna", "Black beans", "Kidney beans", "Pinto beans", "White beans"]
        )

        adjusted["carb"] = prioritize_items(
            adjusted.get("carb", []),
            ["Oat bran cereal", "Oatmeal", "Quinoa", "Barley"]
        )

        adjusted["fat"] = prioritize_items(
            adjusted.get("fat", []),
            ["Avocado", "Pumpkin seeds"]
        )

    if "diabetes" in conditions:
        adjusted["carb"] = prioritize_items(
            adjusted.get("carb", []),
            ["Oat bran cereal", "Oatmeal", "Quinoa", "Barley"]
        )

        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Egg (whole)", "Chicken breast", "Tuna", "Black beans", "Kidney beans", "Pinto beans", "White beans"]
        )

    if "pcos" in conditions:
        adjusted["carb"] = prioritize_items(
            adjusted.get("carb", []),
            ["Oatmeal", "Oat bran cereal", "Quinoa", "Barley"]
        )

        adjusted["fat"] = prioritize_items(
            adjusted.get("fat", []),
            ["Pumpkin seeds", "Walnuts", "Flax seeds", "Avocado"]
        )

        adjusted["protein"] = [
            p for p in adjusted.get("protein", [])
            if p != "Beef"
        ]

        adjusted["protein"] = prioritize_items(
            adjusted["protein"],
            ["Egg (whole)", "Chicken breast", "Tuna", "Black beans", "Kidney beans", "Pinto beans", "White beans"]
        )

    if "hypertension" in conditions:
        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Egg (whole)", "Tuna", "Chicken breast", "Black beans", "Kidney beans", "Pinto beans", "White beans"]
        )

        adjusted["vegetable"] = prioritize_items(
            adjusted.get("vegetable", []),
            ["Spinach", "Broccoli", "Zucchini", "Cucumber", "Kale"]
        )

    if is_pregnant:
        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Egg (whole)", "Chicken breast", "Black beans", "Kidney beans", "Pinto beans", "White beans", "Tuna", "Beef"]
        )

        adjusted["dairy"] = prioritize_items(
            adjusted.get("dairy", []),
            ["Yogurt (low fat)", "Yogurt (nonfat)", "Milk (2% - reduced fat)", "Almond milk"]
        )

        adjusted["vegetable"] = prioritize_items(
            adjusted.get("vegetable", []),
            ["Spinach", "Broccoli", "Kale"]
        )

    if is_menopause:
        adjusted["dairy"] = prioritize_items(
            adjusted.get("dairy", []),
            ["Yogurt (nonfat)", "Yogurt (low fat)", "Milk (2% - reduced fat)", "Almond milk"]
        )

        adjusted["fat"] = prioritize_items(
            adjusted.get("fat", []),
            ["Walnuts", "Pumpkin seeds", "Flax seeds", "Avocado"]
        )

        adjusted["protein"] = prioritize_items(
            adjusted.get("protein", []),
            ["Egg (whole)", "Tuna", "Chicken breast", "Black beans", "Kidney beans", "Pinto beans", "White beans"]
        )

    # Add Olive oil to FAT so it can appear in lunch/dinner meals
    if "fat" not in adjusted:
        adjusted["fat"] = []

    if "Olive oil" not in adjusted["fat"]:
        adjusted["fat"].insert(0, "Olive oil")

    return adjusted


# In[611]:


import random
def split_foods_by_meal(recommended, state):
    health_conditions = [
        str(c).lower().strip()
        for c in state.get("health_condition", [])
    ]

    has_cholesterol = "cholesterol" in health_conditions

    breakfast = {
        "protein": [
            f for f in recommended.get("protein", [])
            if "egg" in f.lower() and not has_cholesterol
        ],
        "dairy": recommended.get("dairy", []),
        "carb": [
            f for f in recommended.get("carb", [])
            if f not in ["Potato", "Quinoa"]
        ],
        "fruit": recommended.get("fruit", []),
        "vegetable": [
            f for f in recommended.get("vegetable", [])
            if f not in ["Broccoli", "Green peas", "Kale", "Pepper"]
        ],
        "fat": []
    }

    lunch = {
        "protein": [
            f for f in recommended.get("protein", [])
            if "egg" not in f.lower()
        ],
        "carb": [
        f for f in recommended.get("carb", [])
        if "oat" not in f.lower() ],
        "vegetable": recommended.get("vegetable", []),
        "fat": [
            f for f in recommended.get("fat", [])
            if "avocado" in f.lower() or "oil" in f.lower()
        ]
    }

    snack = {
        "fruit": recommended.get("fruit", []),
        "dairy": recommended.get("dairy", []),
        "fat": [
            f for f in recommended.get("fat", [])
            if (
                "seed" in f.lower()
                or "walnut" in f.lower()
                or "almond" in f.lower()
                or "nut" in f.lower()
            )
        ],
        "carb": []
    }

    dinner = {
        "protein": [
            f for f in recommended.get("protein", [])
            if "egg" not in f.lower()
        ],
        "vegetable": recommended.get("vegetable", []),
        "carb": [
         f for f in recommended.get("carb", [])
          if "oat" not in f.lower() ],
        "fat": [
            f for f in recommended.get("fat", [])
            if "avocado" in f.lower() or "oil" in f.lower()
        ]
    }

    return {
        "breakfast": breakfast,
        "lunch": lunch,
        "snack": snack,
        "dinner": dinner
    }

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


def build_day_plan(meals, state=None):
    day_plan = {}
    used_foods = set()

    is_menopause = state.get("menopause", False) if state else False

    # -------- BREAKFAST --------
    breakfast_options = []

    if (
        meals["breakfast"]["dairy"]
        and meals["breakfast"]["carb"]
        and meals["breakfast"]["fruit"]
    ):
        breakfast_options.append("sweet_breakfast")

    if (
        meals["breakfast"]["protein"]
        and meals["breakfast"]["vegetable"]
        and meals["breakfast"]["carb"]
    ):
        breakfast_options.append("savory_breakfast")

    if breakfast_options:
        if is_menopause and "sweet_breakfast" in breakfast_options:
            breakfast_type = "sweet_breakfast"
        else:
            breakfast_type = random.choice(breakfast_options)

        if breakfast_type == "sweet_breakfast":
            day_plan["breakfast"] = [
                safe_choice(meals["breakfast"]["dairy"], used_foods),
                safe_choice(meals["breakfast"]["carb"], used_foods),
                safe_choice(meals["breakfast"]["fruit"], used_foods)
            ]

        elif breakfast_type == "savory_breakfast":
            day_plan["breakfast"] = [
                safe_choice(meals["breakfast"]["protein"], used_foods),
                safe_choice(meals["breakfast"]["vegetable"], used_foods),
                safe_choice(meals["breakfast"]["carb"], used_foods)
            ]
    else:
        day_plan["breakfast"] = []

    # -------- LUNCH --------
    day_plan["lunch"] = [
        safe_choice(meals["lunch"]["protein"], used_foods),
        safe_choice(meals["lunch"]["carb"], used_foods),
        safe_choice(meals["lunch"]["vegetable"], used_foods)
    ]

    if meals["lunch"]["fat"]:
        day_plan["lunch"].append(
            safe_choice(meals["lunch"]["fat"], used_foods)
        )

    if meals["lunch"]["vegetable"] and random.random() > 0.6:
        day_plan["lunch"].append(
            safe_choice(meals["lunch"]["vegetable"], used_foods)
        )

    # -------- SNACK --------
    snack_options = []

    if meals["snack"]["dairy"] and meals["snack"]["fruit"]:
        snack_options.append("dairy_fruit")

    if meals["snack"]["fruit"] and meals["snack"]["fat"]:
        snack_options.append("fruit_fat")

    if snack_options:
        if is_menopause and "dairy_fruit" in snack_options:
            snack_type = "dairy_fruit"
        else:
            snack_type = random.choice(snack_options)

        if snack_type == "dairy_fruit":
            day_plan["snack"] = [
                safe_choice(meals["snack"]["dairy"], used_foods),
                safe_choice(meals["snack"]["fruit"], used_foods)
            ]

        elif snack_type == "fruit_fat":
            day_plan["snack"] = [
                safe_choice(meals["snack"]["fruit"], used_foods),
                safe_choice(meals["snack"]["fat"], used_foods)
            ]
    else:
        day_plan["snack"] = []

    # -------- DINNER --------
    day_plan["dinner"] = [
        safe_choice(meals["dinner"]["protein"], used_foods),
        safe_choice(meals["dinner"]["vegetable"], used_foods)
    ]

    if meals["dinner"]["carb"]:
        day_plan["dinner"].append(
            safe_choice(meals["dinner"]["carb"], used_foods)
        )

    if meals["dinner"]["fat"]:
        day_plan["dinner"].append(
            safe_choice(meals["dinner"]["fat"], used_foods)
        )

    for meal_name in day_plan:
        day_plan[meal_name] = [
            food for food in day_plan[meal_name]
            if food is not None
        ]

    return day_plan


# In[612]:


def name_meal(meal_name, foods):
    if not foods:
        return "Healthy Meal"

    text = " ".join(foods).lower()

    has_protein = any(k in text for k in [
        "chicken", "tuna", "salmon", "beans", "chickpeas", "lentils", "beef", "egg"
    ])

    has_carb = any(k in text for k in [
        "oat", "quinoa", "barley", "potato", "sweet potato"
    ])

    has_fruit = any(k in text for k in [
    "banana",
    "orange",
    "pineapple",
    "apple",
    "raspberries",
    "berries",
    "pomegranate"
])

    has_dairy = any(k in text for k in [
        "yogurt", "milk"
    ])

    has_fat = any(k in text for k in [
        "seeds", "pumpkin", "walnuts", "almonds", "flax", "avocado", "olive oil"
    ])

    if meal_name == "breakfast":
        if has_dairy and has_carb and has_fruit:
            return "Creamy Fruit Breakfast Bowl"
        if has_carb and has_fat:
            return "Energizing Breakfast Bowl"
        return "Balanced Morning Plate"

    if meal_name == "lunch":
        if has_protein and has_carb and has_fat:
            return "Protein & Healthy Fat Bowl"
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
        if has_protein and has_carb and has_fat:
            return "Balanced Dinner Plate"
        if has_protein and has_carb:
            return "Wholesome Dinner Plate"
        return "Light Healthy Dinner"

    return "Healthy Meal"


# In[613]:


def display_day_plan(day_plan):
    print("🍽️ DAILY MEAL PLAN")
    print("------------------")

    for meal_name, foods in day_plan.items():
        title = name_meal(meal_name, foods)

        print(f"\n{meal_name.upper()} - {title}:")
        for food in foods:
            print(f"- {food}")


# In[614]:


def run_case(state, daily_state):
    result = build_recommendation(state, daily_state, food_df)

    recommended = result["foods"]
    recommended = apply_limitations(recommended, result, state)
    recommended = adjust_recommended_foods(recommended, state)

    print("🍽 FINAL FOOD RECOMMENDATIONS")
    for category, foods in recommended.items():
        print("\n" + category.upper())
        for food in foods:
            print("-", food)

    meals = split_foods_by_meal(recommended, state)
    day_plan = build_day_plan(meals, state)

    print()
    display_day_plan(day_plan)
    return result, recommended, day_plan


# In[615]:


result, recommended, day_plan = run_case(state, daily_state)


# In[616]:


meal_portions = {
    "breakfast": {
        "protein": 1.7,
        "carb": 1.8,
        "vegetable": 1.0,
        "fruit": 1.0,
        "fat": 0.2,
        "dairy": 1.5
    },
    "lunch": {
        "protein": 1.8,
        "carb": 1.9,
        "vegetable": 1.0,
        "fruit": 1.0,
        "fat": 0.15,
        "dairy": 1.0
    },
    "snack": {
        "protein": 1.0,
        "carb": 0.8,
        "vegetable": 0.5,
        "fruit": 1.0,
        "fat": 0.2,
        "dairy": 1.0
    },
    "dinner": {
        "protein": 1.4,
        "carb": 1.2,
        "vegetable": 1.0,
        "fruit": 0.7,
        "fat": 0.15,
        "dairy": 0.8
    }
}


# In[617]:


def get_food_category(food_name, recommended):
    food_name = food_name.lower().strip()

    for category, foods in recommended.items():
        for food in foods:
            if food_name == str(food).lower().strip():
                return category

    return None


# In[618]:


def get_food_calories(food_name, df):
    food_key = str(food_name).lower().strip()

    alias_map = {
        "egg (whole)": "egg",
        "yogurt (nonfat)": "yogurt",
        "yogurt (low fat)": "yogurt",
        "milk (2% - reduced fat)": "milk",
        "milk (1% - low fat)": "milk",
        "almond milk": "almond milk",
        "oat bran cereal": "oat bran",
        "chicken breast": "chicken breast",
        "strawberry": "strawberries",
        "sweet potato": "sweet potato",
        "olive oil": "olive oil",
        "tuna": "tuna",
        "spinach": "spinach",
        "quinoa": "quinoa"
    }

    search_key = alias_map.get(food_key, food_key)

    row = df[df["desc_lower"] == search_key]

    if row.empty:
        row = df[df["desc_lower"].str.contains(search_key, na=False, regex=False)]

    if row.empty:
        return None

    row = row.iloc[0]

    protein = row.get("Data.Protein", 0) or 0
    carbs = row.get("Data.Carbohydrate", 0) or 0
    fat = row.get("Data.Fat.Total Lipid", 0) or 0

    calories = (protein * 4) + (carbs * 4) + (fat * 9)

    return round(calories, 1)


# In[619]:
def calculate_meal_calories(day_plan, df, recommended):
    meal_calories = {}
    total_day = 0

    for meal_name, foods in day_plan.items():
        meal_total = 0
        meal_key = meal_name.lower().strip()

        for food in foods:
            base_calories = get_food_calories(food, df)

            if base_calories is None:
                continue

            category = get_food_category(food, recommended)
            factor = meal_portions.get(meal_key, {}).get(category, 1.0)

            meal_total += base_calories * factor

        meal_calories[meal_name] = round(meal_total)
        total_day += meal_total

    total_day = round(total_day)

    note = "Calories are estimated based on meal composition, portion distribution, and nutritional balance."

    if total_day < 1200:
        note += " Calories are low for a full daily meal plan. Consider increasing portions or adding a balanced snack."

    meal_calories["total_day_calories"] = total_day
    meal_calories["note"] = note

    return meal_calories

def display_meal_calories(day_plan, df, recommended):
    total_day = 0

    print("🔥 DAILY CALORIES")
    print("----------------")

    for meal_name, foods in day_plan.items():
        meal_total = 0
        meal_key = meal_name.lower().strip()

        print(f"\n{meal_name.upper()}")

        for food in foods:
            base_calories = get_food_calories(food, df)

            if base_calories is None:
                print(f"- {food}: not found")
                continue

            category = get_food_category(food, recommended)

            # ✅ use meal_portions instead of category_portion
            factor = meal_portions.get(meal_key, {}).get(category, 1.0)

            final_calories = base_calories * factor
            meal_total += final_calories

            print(
                f"- {food}: {round(final_calories, 1)} kcal "
                f"({category}, portion x{factor})"
            )

        print(f"Total {meal_name}: {round(meal_total, 1)} kcal")
        total_day += meal_total

    print("\n----------------")
    print(f"TOTAL DAY: {round(total_day, 1)} kcal")

    if total_day < 1200:
        print("⚠️ Total calories are too low for users aged 15+.")
        print("Suggestion: increase portions or add an extra snack.")
    elif total_day < 1500:
        print("⚠️ Calories are on the low side.")
        print("Suggestion: consider increasing protein or carb portions.")
    else:
        print("✅ Calories look reasonable.")


# In[620]:


display_meal_calories(day_plan, food_df, recommended)


# In[ ]:





# In[ ]:





# In[ ]:




