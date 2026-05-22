

from chatbot import get_chat_response
from datetime import datetime
import os

from flask import Flask, request, jsonify
from recommendation_engine import (
    build_recommendation,
    build_long_term_state,
    food_df,
    apply_limitations,
    adjust_recommended_foods,
    split_foods_by_meal,
    build_day_plan,
    name_meal,
    calculate_meal_calories
)
from chatbot import get_chat_response, generate_ai_response

app = Flask(__name__)


@app.route("/")
def home():
    return "HerBalance backend is running"


@app.route("/recommendation", methods=["POST"])
def recommendation():
    data = request.get_json() or {}

    try:
        user_profile = data.get("user_profile", {})
        daily_state = data.get("daily_state", {})

        state = build_long_term_state(user_profile)
        state["pregnant"] = user_profile.get("pregnant", False)
        state["cycle_phase"] = user_profile.get("cycle_phase")
        state["health_condition"] = user_profile.get("health_condition", [])

        result = build_recommendation(state, daily_state, food_df)

        return jsonify(result)

    except Exception as e:
        print("REC ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/meals", methods=["POST"])
def meals():
    data = request.get_json() or {}

    try:
        user_profile = data.get("user_profile", {})
        daily_state = data.get("daily_state", {})

        state = build_long_term_state(user_profile)
        state["pregnant"] = user_profile.get("pregnant", False)
        state["cycle_phase"] = user_profile.get("cycle_phase")
        state["health_condition"] = user_profile.get("health_condition", [])

        result = build_recommendation(state, daily_state, food_df)

        recommended = result["foods"]
        recommended = apply_limitations(recommended, result, state)
        recommended = adjust_recommended_foods(recommended, state)

        meals_split = split_foods_by_meal(recommended, state)
        day_plan = build_day_plan(meals_split, state)
        daily_calories = calculate_meal_calories(day_plan, food_df, recommended)

        daily_meal_plan = {}

        for meal_name, foods in day_plan.items():
            daily_meal_plan[meal_name] = {
                "title": name_meal(meal_name, foods),
                "foods": foods,
                "calories": daily_calories.get(meal_name.lower(), 0)
            }

        return jsonify({
            "daily_meal_plan": daily_meal_plan,
            "daily_calories": daily_calories
        })

    except Exception as e:
        print("MEALS ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}

    message = data.get("message", "")
    user_context = data.get("user_context", {})
    chat_history = data.get("chat_history", [])

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        response = get_chat_response(message, user_context, chat_history)
        return jsonify({"response": response})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/activity", methods=["POST"])
def activity():
    data = request.get_json() or {}

    user_context = data.get("user_context", {})
    daily_state = data.get("daily_state", {})

    activity_prompt = f"""
You are HerBalance Activity Assistant.

Your task is to generate a safe, personalized daily physical activity recommendation for a women's wellness and nutrition app.

Use ONLY the provided user profile and daily state.
Do not ask follow-up questions.
Do not start a chat conversation.
Do not mention that you are an AI.

User profile:
{user_context}

Daily state:
{daily_state}

Analyze these factors:
- Age
- Sleep hours
- Stress level
- Mood
- Hydration
- Current activity level
- Cycle phase
- Pregnancy status
- PCOS status
- BMI-related safety
- Health conditions such as hypertension, diabetes, cholesterol, joint pain, or arthritis

Sleep interpretation:
- 6–9 hours = good/normal sleep
- 5 hours = low sleep
- 4 hours or less = very low sleep

Important:
- 6 hours should be treated as normal/acceptable sleep.
- Do NOT describe 6 hours as low or slightly low sleep.
- 6 hours alone should not reduce the activity day type.

Stress interpretation :
- stress_boost = min(stress_score // 4, 2)
- stress_boost = 0 → low stress
- stress_boost = 1 → moderate stress
- stress_boost = 2 → high/very high stress

Stress + sleep synergy:
- If stress_score >= 8 and sleep_hours <= 5, treat this as strong fatigue/recovery signal.

Decision logic:
- Choose Recovery Day ONLY if:
  - sleep is very low,
  - OR stress is very high,
  - OR multiple negative factors exist together (high stress + low sleep + low mood + low hydration).

- Do NOT choose Recovery Day for:
  - slightly low sleep alone,
  - moderate stress alone,
  - or low hydration alone.

- If sleep is slightly low or stress is high, prefer Light Activity Day instead of Recovery Day unless other negative factors are also present.

- If hydration is low, avoid intense activity.

- If pregnancy status is Yes or True, choose only pregnancy-safe, low-impact activities.

- If hypertension exists, avoid heavy strain or intense exercise.

- If diabetes exists, prefer moderate consistent activity and avoid exhausting workouts.

- If cholesterol exists, prefer heart-friendly activities such as walking, swimming, and cycling at an easy pace.

- If BMI suggests obesity, prefer low-impact joint-friendly activities.

- If joint pain or arthritis exists, avoid jumping, running, and high-impact exercises.

- If mood is low, include gentle mood-supporting activities.

- If menstrual phase, prioritize gentle stretching, walking, yoga, and breathing.

- If age is 60 or above, prefer low-impact, joint-friendly activities such as gentle walking, swimming, stationary cycling, Tai Chi, balance exercises, and stretching.

- If age is 60 or above, avoid intense cycling, fast running, jumping, heavy lifting, or high-impact exercises.

- Allow Moderate Activity Day or Active Day only when:
  - sleep is good,
  - stress is low to moderate,
  - hydration is good,
  - and there are no major safety limitations.

- Keep recommendations realistic, safe, and wellness-focused.
- If PCOS exists, prefer low to moderate consistent activity such as walking, strength-light exercises, yoga, and cycling at an easy pace.
- Avoid very intense activity when stress is high or sleep is low because it may increase fatigue.
- Menstrual phase: gentle walking, stretching, yoga, breathing.
- Follicular phase: light to moderate activity is usually suitable if daily state is good.
- Ovulation phase: moderate activity can be recommended if sleep, hydration, and stress are good.
- Luteal phase: prefer light to moderate activity, stretching, walking, and calming exercises, especially if stress or mood is low.

Give the answer in this exact structure:

1. Activity Day Type:
[Choose only one: Recovery Day / Light Activity Day / Moderate Activity Day / Active Day]

2. Recommended Intensity:
[Choose only one: Very Light / Light / Light to Moderate / Moderate]

3. Recommended Activities:
- Activity 1
- Activity 2
- Activity 3
- Activity 4
- Activity 5

4. Why this plan:
- Reason 1
- Reason 2
- Reason 3

5. Safety Note:
One short sentence only.

Output rules:
- Keep the answer short and clear.
- Do not include extra sections.
- Do not recommend unsafe, extreme, high-impact, or medical activities.
- Do not give diagnosis or treatment.
- Use simple user-friendly language.
- The answer must be suitable to display directly inside an app screen.
"""

    try:
        response = generate_ai_response(activity_prompt)

        return jsonify({
            "activity_response": response
        })

    except Exception as e:
        print("ACTIVITY ERROR:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
