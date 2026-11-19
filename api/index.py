import os
import json
from flask import Flask, request, jsonify, render_template_string
from google import genai
from google.genai import types

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LeadPulse AI — Instant B2B Lead Qualifier</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans">
    <div class="max-w-4xl mx-auto px-4 py-10">
        <div class="flex justify-between items-center border-b border-slate-800 pb-6 mb-8">
            <div>
                <span class="bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-500/20">AI SALES ENGINE v1.0</span>
                <h1 class="text-3xl font-bold mt-2 tracking-tight">LeadPulse AI</h1>
                <p class="text-slate-400 text-sm mt-1">Qualify incoming leads in 2 seconds & generate instant high-converting replies.</p>
            </div>
        </div>

        <div class="grid md:grid-cols-2 gap-8">
            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
                <h2 class="text-lg font-semibold mb-4 text-slate-200">Simulate Incoming Lead</h2>
                <form id="leadForm" class="space-y-4">
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Client Business Niche</label>
                        <select id="business_type" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500">
                            <option value="Real Estate Agency">Real Estate Agency</option>
                            <option value="Dental / Skin Clinic">Dental / Skin Clinic</option>
                            <option value="B2B Software / Marketing Agency">B2B Agency</option>
                            <option value="Luxury Interior Designer">Interior Designer</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Customer Name</label>
                        <input type="text" id="name" value="Rahul Sharma" required class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Budget / Deal Size</label>
                        <input type="text" id="budget" value="₹85 Lakh" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Customer Inquiry Message</label>
                        <textarea id="inquiry" rows="3" required class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500">Hi, mujhe Navi Mumbai mein 2BHK ready-to-move flat chahiye. Loan pre-approved hai, is weekend site visit kar sakte hain kya?</textarea>
                    </div>
                    <button type="submit" id="submitBtn" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2.5 rounded-lg transition cursor-pointer">
                        Analyze & Qualify Lead ⚡
                    </button>
                </form>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
                <div>
                    <h2 class="text-lg font-semibold mb-4 text-slate-200">AI Decision & Instant Action</h2>
                    <div id="placeholder" class="text-slate-500 text-sm py-16 text-center border border-dashed border-slate-800 rounded-xl">
                        Left side se lead submit karo, AI 2 second mein score aur WhatsApp reply taiyar karega.
                    </div>
                    <div id="resultBox" class="hidden space-y-4">
                        <div class="flex items-center justify-between bg-slate-800/60 p-4 rounded-xl border border-slate-700">
                            <div>
                                <p class="text-xs text-slate-400 uppercase">Lead Priority</p>
                                <span id="scoreBadge" class="text-2xl font-extrabold">HOT</span>
                            </div>
                            <div class="text-right">
                                <p class="text-xs text-slate-400 uppercase">AI Confidence</p>
                                <span id="confidenceVal" class="text-lg font-bold text-slate-200">95%</span>
                            </div>
                        </div>
                        <div>
                            <p class="text-xs text-slate-400 uppercase mb-1">Why this score?</p>
                            <p id="reasonText" class="text-sm text-slate-300 bg-slate-800/40 p-3 rounded-lg"></p>
                        </div>
                        <div>
                            <p class="text-xs text-slate-400 uppercase mb-1">Recommended Next Step</p>
                            <p id="actionText" class="text-sm font-medium text-emerald-400"></p>
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-1">
                                <p class="text-xs text-slate-400 uppercase">Auto-Generated WhatsApp Reply</p>
                                <button onclick="copyReply()" class="text-xs text-emerald-400 hover:underline cursor-pointer">Copy Text</button>
                            </div>
                            <div id="replyText" class="text-sm text-slate-200 bg-slate-950 border border-slate-800 p-3.5 rounded-lg leading-relaxed"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('leadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.innerText = 'Analyzing with Gemini AI...';
            btn.disabled = true;

            const payload = {
                business_type: document.getElementById('business_type').value,
                name: document.getElementById('name').value,
                budget: document.getElementById('budget').value,
                inquiry: document.getElementById('inquiry').value
            };

            try {
                const res = await fetch('/api/qualify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    document.getElementById('placeholder').classList.add('hidden');
                    document.getElementById('resultBox').classList.remove('hidden');

                    const badge = document.getElementById('scoreBadge');
                    badge.innerText = data.score;
                    badge.className = 'text-2xl font-extrabold ' + (
                        data.score === 'HOT' ? 'text-emerald-400' :
                        data.score === 'WARM' ? 'text-amber-400' : 'text-rose-400'
                    );

                    document.getElementById('confidenceVal').innerText = data.confidence_percent + '%';
                    document.getElementById('reasonText').innerText = data.reason;
                    document.getElementById('actionText').innerText = '→ ' + data.recommended_action;
                    document.getElementById('replyText').innerText = data.instant_reply;
                }
            } catch (err) {
                alert('Server error: ' + err.message);
            } finally {
                btn.innerText = 'Analyze & Qualify Lead ⚡';
                btn.disabled = false;
            }
        });

        function copyReply() {
            const text = document.getElementById('replyText').innerText;
            navigator.clipboard.writeText(text);
            alert('WhatsApp reply copied!');
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

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
