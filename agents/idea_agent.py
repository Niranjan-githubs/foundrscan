import google.generativeai as genai
import os
from dotenv import load_dotenv
import random

# ✅ Load environment variables from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# 🧠 Startup Questions
questions = {
    "startup_name": "What is the name of your startup?",
    "one_liner": "Give a one-liner description of your startup. (Optional)",
    "category":"what category you idea falls on ?"
    "problem_statement": "What problem are you solving?",
    "solution": "How does your product/service solve this problem?",
    "target_audience": "Who is your target customer?",
    "business_model": "How will you deliver the product/service?",
    "revenue_model": "How will you make money?",
    "unique_selling_point": "What is unique about your solution?",
    "stage": "What stage is your startup in?",
    "founder_background": "Tell us about your background and why you're the right person to build this."
}

# ✅ Fuzzy keyword sets
keyword_map = {
    "target_audience": ["patients", "users", "diabetes", "customers", "people", "clients"],
    "business_model": ["mobile", "android", "ios", "web", "platform", "app", "deliver"],
    "revenue_model": ["yes", "subscription", "₹", "payment", "fee", "price"]
}

# 🧠 Smart response clarity checker
def is_response_clear(key, question, answer):
    answer_lower = answer.strip().lower()

    affirmatives = ["yes", "yeah", "yup", "correct", "exactly", "that's right", "sure", "yep", "affirmative", "true"]
    if answer_lower in affirmatives:
        return "clear"

    if key in ["startup_name", "one_liner"] and answer:
        return "clear"

    if len(answer_lower) >= 10 and any(word in answer_lower for word in ["glucose", "ai", "meal", "predict", "diabetes"]):
        return "clear"

    if key in keyword_map and any(keyword in answer_lower for keyword in keyword_map[key]):
        return "clear"

    if len(answer_lower) < 10:
        return "vague:Can you elaborate on that a bit more so we fully understand your idea?"

    try:
        prompt = f"""
You're helping collect a startup idea. Here's the context:

Question: "{question}"
User's Answer: "{answer}"

Decide if the answer is acceptable. If it gives a clear direction, say "clear".
If it's vague or needs more explanation, say:
"vague:<rephrase to get better answer>"

Respond with:
- "clear"
OR
- "vague:<rephrased_question>"
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Skipping validation due to error: {e}")
        return "clear"

# 🔁 Friendly follow-up prompts
follow_up_templates = [
    "🤖 Hmm, I think I missed part of that. Could you clarify?\n👉 {rephrased}",
    "🤖 Cool — just one more thing I’m curious about…\n👉 {rephrased}",
    "🤖 Nice! That gives me a good picture, but…\n👉 {rephrased}",
    "🤖 That's interesting. Can you add more detail?\n👉 {rephrased}",
    "🤖 Okay got it. Out of curiosity, how are you planning to…\n👉 {rephrased}",
    "🤖 Just to be sure — would you mind elaborating?\n👉 {rephrased}",
    "🤖 Got it! Could you expand a little more?\n👉 {rephrased}"
]

def friendly_prompt(rephrased):
    return random.choice(follow_up_templates).format(rephrased=rephrased)

# 📥 Interactive idea collector
def enhanced_idea_collector():
    responses = {}
    for key, question in questions.items():
        while True:
            user_input = input(f"{question}\n> ").strip()
            eval_result = is_response_clear(key, question, user_input)

            if eval_result.lower() == "clear":
                responses[key] = user_input
                break
            elif eval_result.startswith("vague:"):
                rephrased = eval_result.split("vague:")[1].strip()
                print(friendly_prompt(rephrased))
            else:
                print("❗ Unexpected response. Please try again.")
    return responses

# 📊 Final analysis using Gemini
def run_final_summary(responses):
    prompt = f"""
You are a smart startup summarizer agent. Based on the following collected inputs from a founder, generate a structured JSON summary without judgment or validation.

{responses}

Return only:
- startup_name
- one_liner
- problem_statement
- solution
- target_audience
- business_model
- revenue_model
- unique_selling_point
- stage
- founder_background
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❗ Error during summary: {e}"

# 🚀 Run the product flow
if __name__ == "__main__":
    data = enhanced_idea_collector()
    print("\n✅ Generating your startup summary...\n")
    print(run_final_summary(data))
