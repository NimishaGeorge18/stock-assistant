import anthropic
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def analyze_chart(stock_name: str, image_path: str) -> dict:
    image_data = encode_image(image_path)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                },
                {
                    "type": "text",
                    "text": f"""You are an expert technical analyst analyzing the {stock_name} stock chart.
                    
Return ONLY a valid JSON object with no extra text, exactly like this:
{{
    "stock": "{stock_name}",
    "signal": "BUY or SELL or HOLD",
    "current_price": <number or null if not visible>,
    "entry": <number>,
    "stop_loss": <number>,
    "target": <number>,
    "reason": "<one sentence max>"
}}

Rules:
- signal must be BUY, SELL, or HOLD
- stop_loss must be below entry for BUY, above entry for SELL
- target must give at least 2:1 reward vs risk
- If price is not readable, estimate based on chart shape"""
                }
            ]
        }]
    )

    raw = response.content[0].text.strip()
    
    # clean up if Claude wraps in markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw.strip())
    
    # enforce 2:1 ratio programmatically
    if result["signal"] == "BUY":
        risk = result["entry"] - result["stop_loss"]
        result["target"] = round(result["entry"] + (risk * 2), 2)
    elif result["signal"] == "SELL":
        risk = result["stop_loss"] - result["entry"]
        result["target"] = round(result["entry"] - (risk * 2), 2)

    print(f"\n{stock_name} Analysis:")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    # test with the latest screenshot
    import os, glob
    latest = sorted(glob.glob("screenshots/ITC_*.png"))[-1]
    print(f"Testing with: {latest}")
    analyze_chart("ITC", latest)