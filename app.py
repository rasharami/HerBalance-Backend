from flask import Flask, request, jsonify
from recommendation_engine import get_recommendation, get_recommendation_response
from chatbot import get_chat_response
from datetime import datetime

app = Flask(__name__)


@app.route("/")
def home():
    return "HerBalance backend is running"

@app.route("/recommendation", methods=["POST"])
def recommendation():
    data = request.get_json() or {}

    try:
        result = get_recommendation(
            data.get("user_profile", {}),
            data.get("daily_state", {})
        )
        return jsonify(result)

    except Exception as e:
        print("REC ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/meals", methods=["POST"])
def meals():
    data = request.get_json() or {}

    try:
        result = get_recommendation_response(
            data.get("user_profile", {}),
            data.get("daily_state", {})
        )
        return jsonify(result)

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
- Sleep hours
- Stress level
- Mood
- Hydration
- Current activity level
- Cycle phase
- Pregnancy status
- PCOS status
- BMI-related safety
- Health conditions such as hypertension, diabetes, or cholesterol

Decision logic:
- If sleep is very low or stress is very high, prioritize Recovery Day.
- If hydration is low, avoid intense activity.
- If pregnancy is Yes, choose only pregnancy-safe, low-impact activities.
- If hypertension exists, avoid heavy strain or intense exercise.
- If BMI suggests obesity, prefer low-impact joint-friendly activities.
- If mood is low, include gentle mood-supporting activities.
- If menstrual phase, prioritize gentle stretching, walking, yoga, and breathing.
- If sleep, stress, mood, and hydration are good, allow Moderate or Active Day.
- Keep recommendations realistic, safe, and wellness-focused.

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
        response = get_chat_response(
            activity_prompt,
            user_context,
            []
        )

        return jsonify({
            "activity_response": response
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
