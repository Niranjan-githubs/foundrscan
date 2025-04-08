import google.generativeai as genai
import os
from dotenv import load_dotenv
import random

# ✅ Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# ✅ Define Questions
questions = {
    "startup_name": "What is the name of your startup?",
    "one_liner": "Give a one-liner description of your startup. (Optional)",
    "problem_statement": "What problem are you solving?",
    "solution": "How does your product/service solve this problem?",
    "target_audience": "Who is your target customer?",
    "business_model": "How will you deliver the product/service?",
    "revenue_model": "How will you make money?",
    "unique_selling_point": "What is unique about your solution?",
    "stage": "What stage is your startup in?",
    "founder_background": "Tell us about your background and why you're the right person to build this."
}

# ✅ One-time re-ask tracker
reask_tracker = {}

# ✅ Follow-up templates
follow_up_templates = [
    "🤖 Hmm, I think I missed part of that. Could you clarify?\n👉 {rephrased}",
    "🤖 Cool — just one more thing I’m curious about…\n👉 {rephrased}",
    "🤖 Okay got it. Out of curiosity, how are you planning to…\n👉 {rephrased}"
]

def friendly_prompt(rephrased):
    return random.choice(follow_up_templates).format(rephrased=rephrased)

# ✅ Smart Clarity Check
def is_response_clear(key, question, answer):
    answer = answer.strip().lower()
    if len(answer) > 15:
        return "clear"

    # Basic heuristic fallback
    if len(answer) < 5:
        return f"vague:{question} (Can you explain a bit more?)"

    # Gemini fallback for subtle cases
    try:
        prompt = f"""
You're helping collect a startup idea.

Question: "{question}"
Answer: "{answer}"

Is the answer clear? Say 'clear' or return vague:<rephrased question>
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Skipping Gemini validation due to error: {e}")
        return "clear"

# ✅ Input collector with smart clarification
def enhanced_idea_collector():
    responses = {}

    for key, question in questions.items():
        has_reasked = False

        while True:
            user_input = input(f"{question}\n> ").strip()
            clarity = is_response_clear(key, question, user_input)

            if clarity == "clear":
                responses[key] = user_input
                break
            elif clarity.startswith("vague:") and not has_reasked:
                rephrased = clarity.split("vague:")[1]
                print(friendly_prompt(rephrased))
                has_reasked = True
            else:
                print("🔁 Thanks, moving on.")
                responses[key] = user_input
                break
    return responses

# ✅ Final summary
def run_final_summary(responses):
    prompt = f"""
You are a smart startup summarizer. Based on this input, return a clean JSON summary:

{responses}

Return:
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

# 🚀 Run the flow
if __name__ == "__main__":
    data = enhanced_idea_collector()
    print("\n✅ Generating your startup summary...\n")
    print(run_final_summary(data))
