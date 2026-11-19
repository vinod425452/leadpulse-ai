import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__, template_folder="../templates")

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/qualify", methods=["POST"])
def qualify_lead():
    if not client:
        return jsonify({"error": "GEMINI_API_KEY Vercel settings mein add nahi ki gayi hai!"}), 500

    data = request.json
    name = data.get("name", "Customer")
    business_type = data.get("business_type", "Real Estate")
    inquiry = data.get("inquiry", "")
    budget = data.get("budget", "Not specified")

    if not inquiry:
        return jsonify({"error": "Inquiry message khali nahi ho sakta."}), 400

    prompt = f"""
    You are an expert B2B Sales Qualification AI for a {business_type} business in India.
    Analyze the following incoming customer lead and return ONLY a valid JSON object.

    Lead Details:
    - Name: {name}
    - Stated Budget: {budget}
    - Message: "{inquiry}"

    Evaluate urgency, purchasing power, and seriousness.
    Return JSON in this exact format:
    {{
        "score": "HOT" or "WARM" or "COLD",
        "confidence_percent": 85,
        "reason": "1-line sharp explanation for the business owner in Hinglish/English",
        "recommended_action": "What the sales team should do right now",
        "instant_reply": "A natural, persuasive, ready-to-send WhatsApp/Email reply to {name} (under 60 words)"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        result = json.loads(response.text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
  
