import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing. Check your .env file.")

client = OpenAI(api_key=api_key)


def generate_ai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Sorry, I couldn't generate a response. Can you try again?"

        return answer.strip()

    except Exception as e:
        return f"Chatbot error: {str(e)}"


def get_value(context, *keys, default=None):
    for key in keys:
        if key in context and context.get(key) is not None:
            return context.get(key)
    return default


def calculate_cycle_phase(last_period_date, cycle_length=28, period_duration=5, pregnant=False):
    if pregnant or not last_period_date:
        return "none"

    try:
        if "T" in str(last_period_date):
            last_date = datetime.fromisoformat(
                str(last_period_date).replace("Z", "+00:00")
            ).replace(tzinfo=None)
        else:
            last_date = datetime.strptime(str(last_period_date), "%Y-%m-%d")

        today = datetime.now()
        days_since = (today.date() - last_date.date()).days

        if days_since < 0:
            return "none"

        cycle_length = int(cycle_length) if cycle_length else 28
        period_duration = int(period_duration) if period_duration else 5

        day_in_cycle = days_since % cycle_length

        if day_in_cycle < period_duration:
            return "menstrual"
        elif day_in_cycle < 14:
            return "follicular"
        elif day_in_cycle < 17:
            return "ovulation"
        else:
            return "luteal"

    except Exception:
        return "none"


def build_history_text(chat_history):
    if not chat_history:
        return "No previous conversation."

    history_text = ""

    for item in chat_history[-8:]:
        role = item.get("role", "user")
        text = item.get("text", "")

        if text:
            history_text += f"{role}: {text}\n"

    return history_text


def get_chat_response(message, user_context, chat_history=None):
    chat_history = chat_history or []

    age = get_value(user_context, "age", default="unknown")
    height = get_value(user_context, "height", default="unknown")
    weight = get_value(user_context, "weight", default="unknown")
    pcos = get_value(user_context, "pcos", default=False)
    pregnancy_status = get_value(user_context, "pregnancyStatus", default="No")
    health_conditions = get_value(user_context, "healthConditions", default=[])
    cycle_length = get_value(user_context, "cycleLength", default=28)
    period_duration = get_value(user_context, "periodDuration", default=5)
    last_period_date = get_value(user_context, "lastPeriodDate", default=None)

    activity_level = get_value(user_context, "activityLevel", default="Moderate")
    hydration = get_value(user_context, "hydration", default="Good")
    mood = get_value(user_context, "mood", default="Moderate")
    sleep_hours = get_value(user_context, "sleepHours", default=7)
    stress = get_value(user_context, "stress", default=3)

    pregnant_bool = pregnancy_status == "Yes" or pregnancy_status is True

    cycle_phase = get_value(user_context, "cyclePhase", default=None)

    if not cycle_phase or cycle_phase in ["unknown", "none", "null", ""]:
        cycle_phase = calculate_cycle_phase(
            last_period_date=last_period_date,
            cycle_length=cycle_length,
            period_duration=period_duration,
            pregnant=pregnant_bool
        )

    history_text = build_history_text(chat_history)

    prompt = f"""
You are HerBalance, a friendly women wellness chatbot.

Important:
- Continue the conversation naturally.
- Use the recent conversation to understand follow-up messages.
- Do not treat each user message as a completely new topic if it refers to the previous answer.

Recent conversation:
{history_text}

User profile:
- Age: {age}
- Height: {height}
- Weight: {weight}
- PCOS: {pcos}
- Pregnancy status: {pregnancy_status}
- Health conditions: {health_conditions}
- Cycle length: {cycle_length}
- Period duration: {period_duration}
- Last period date: {last_period_date}
- Cycle phase: {cycle_phase}

Today's state:
- Activity level: {activity_level}
- Hydration: {hydration}
- Mood: {mood}
- Sleep hours: {sleep_hours}
- Stress level: {stress}

Current user message:
{message}

Rules:
- Act like a real chat assistant.
- Keep the answer short and natural.
- Use 4 to 6 short lines when giving recommendations.
- Use 2 to 4 short lines for simple answers.
- Personalize based on the user's profile, daily state, and cycle phase.
- If the user asks about her phase, answer using the calculated cycle phase exactly.
- Do not diagnose.
- Do not prescribe medication.
- Give general wellness guidance only.
- If symptoms are severe, persistent, pregnancy-related, or worrying, advise seeing a healthcare professional.
- Do not ask many consecutive questions.
- Ask a maximum of 2 short clarification questions total for the same concern.
- If the user has already answered 2 follow-up questions, stop asking and give helpful recommendations.
- Use the available user profile, today's state, and recent conversation before asking.
- For wellness concerns like hair loss, fatigue, sleep, stress, acne, or PCOS, ask a maximum of 2 short questions total, then provide practical guidance.
- If the user asks "what should I do", "what can I do", or asks for a solution, give recommendations immediately instead of asking another question.
- If the user says they do not want diet or food recommendations, do not include food advice.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Sorry, I couldn't generate a response. Can you try again?"

        return answer.strip()

    except Exception as e:
        return f"Chatbot error: {str(e)}"
