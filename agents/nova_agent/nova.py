from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import re
import json

app = FastAPI()

# Request schema
class IdeaInput(BaseModel):
    idea: str

# Response schema
class MarketAnalysis(BaseModel):
    market_size: str
    trends: list[str]
    risks: list[str]

@app.get("/")
def read_root():
    return {"message": "API is running. Use /docs to test the analyze endpoint."}

@app.get("/analyze")
def fallback():
    return {"message": "Use POST /analyze with a JSON body: { 'idea': 'your startup idea' }"}

# 🧠 Prompt for cleanup pass
clean_prompt_template = """
Convert the following startup analysis into a clean, valid JSON using this schema:

{{
  "market_size": "short summary string",
  "trends": ["short trend string", "short trend string"],
  "risks": ["short risk string", "short risk string"]
}}

Text:
{text}

Return only the final JSON.
"""

# 💬 Step 1: Generate prompt and call Ollama
async def query_llm_cleaned(idea: str) -> dict:
    messy_prompt = f"""
You are a startup analyst.

Analyze the startup idea: "{idea}"

Return your findings in valid JSON using this **exact** structure:

{{
  "market_size": "One-sentence estimate of the potential or current market size",
  "trends": [
    "Brief description of a current market trend related to the idea",
    "Another relevant trend"
  ],
  "risks": [
    "Brief description of a possible risk or challenge",
    "Another risk"
  ]
}}

Rules:
- Only return the JSON. No commentary, no explanation.
- Do NOT use markdown, bullets, or headings.
- Each value should be a short, human-readable string.
- Do NOT include nested objects or arrays.
"""


    async with httpx.AsyncClient(timeout=60) as client:
        # First call: get messy analysis
        messy = await client.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": messy_prompt
        })
        messy_lines = messy.text.strip().splitlines()
        messy_response = "".join([
            json.loads(line)["response"]
            for line in messy_lines if '"response":' in line
        ])

        # Second call: ask LLM to clean it into JSON
        clean_prompt = clean_prompt_template.format(text=messy_response)
        clean = await client.post("http://localhost:11434/api/generate", json={
            "model": "openhermes",
            "prompt": clean_prompt
        })
        clean_lines = clean.text.strip().splitlines()
        clean_response = "".join([
            json.loads(line)["response"]
            for line in clean_lines if '"response":' in line
        ])

        try:
            match = re.search(r"\{.*\}", clean_response, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except Exception as e:
            print("❌ Final JSON parse error:", e)
            return {}

# 🧠 Step 2: Parse cleaned output into structured model
def parse_llm_response(raw_text: str) -> MarketAnalysis:
    print("LLM RESPONSE:\n", raw_text)
    try:
        match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found")
        raw_json = match.group(0)

        raw_json = re.sub(
            r'(?<=:\s)(\d{1,3},\d{3})(?=,|\n|\r|\s|\})',
            lambda m: '"' + m.group(1).replace(",", "") + '"',
            raw_json
        )
        raw_json = re.sub(r'\d+\)\s*', '', raw_json)

        parsed = json.loads(raw_json)

        def clean_list(items):
            return [item.strip()[:250] for item in items if isinstance(item, str)]

        return MarketAnalysis(
            market_size=str(parsed.get("market_size", "Unknown"))[:300],
            trends=clean_list(parsed.get("trends", [])[:2]),
            risks=clean_list(parsed.get("risks", [])[:2])
        )

    except Exception as e:
        print("❌ Parse error:", e)
        return MarketAnalysis(
            market_size="Invalid JSON format",
            trends=[],
            risks=[]
        )

def safe_list(input_list):
    return [str(x) for x in input_list if isinstance(x, str)][:2]

@app.post("/analyze", response_model=MarketAnalysis)
async def analyze_idea(input: IdeaInput):
    data = await query_llm_cleaned(input.idea)

    return MarketAnalysis(
        market_size=str(data.get("market_size", "Unknown")),
        trends=safe_list(data.get("trends", [])),
        risks=safe_list(data.get("risks", []))
    )

