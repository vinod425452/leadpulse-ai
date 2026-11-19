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
    <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="border-b border-slate-800 pb-5 mb-6">
            <span class="bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-500/20">AI SALES ENGINE v1.1</span>
            <h1 class="text-3xl font-bold mt-2 tracking-tight">LeadPulse AI</h1>
            <p class="text-slate-400 text-sm mt-1">Qualify incoming leads in 2 seconds & generate instant WhatsApp replies.</p>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
                <h2 class="text-lg font-semibold mb-4 text-slate-200">Simulate Incoming Lead</h2>
                <form id="leadForm" class="space-y-4">
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Client Business Niche</label>
                        <select id="business_type" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm">
                            <option value="Real Estate Agency">Real Estate Agency</option>
                            <option value="Dental / Skin Clinic">Dental / Skin Clinic</option>
                            <option value="B2B Software / Marketing Agency">B2B Agency</option>
                            <option value="Luxury Interior Designer">Interior Designer</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Customer Name</label>
                        <input type="text" id="name" value="Rahul Sharma" required class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Budget / Deal Size</label>
                        <input type="text" id="budget" value="₹85 Lakh" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm">
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 uppercase mb-1">Customer Inquiry Message</label>
                        <textarea id="inquiry" rows="3" required class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm">Hi, mujhe Navi Mumbai mein 2BHK ready-to-move flat chahiye. Loan pre-approved hai, is weekend site visit kar sakte hain kya?</textarea>
                    </div>
                    <button type="submit" id="submitBtn" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-3 rounded-lg transition">
                        Analyze & Qualify Lead ⚡
                    </button>
                </form>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
                <h2 class="text-lg font-semibold mb-4 text-slate-200">AI Decision & Instant Action</h2>
                
                <div id="placeholder" class="text-slate-500 text-sm py-12 text-center border border-dashed border-slate-800 rounded-xl">
                    Upar se lead submit karo, AI 2 second mein score aur WhatsApp reply taiyar karega.
                </div>

                <div id="errorBox" class="hidden bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs p-4 rounded-xl break-words"></div>

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
                            <button type="button" id="copyBtn" onclick="copyReply()" class="text-xs text-emerald-400 underline">Copy Text</button>
                        </div>
                        <div id="replyText" class="text-sm text-slate-200 bg-slate-950 border border-slate-800 p-3.5 rounded-lg leading-relaxed"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('leadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const errorBox = document.getElementById('errorBox');
            const resultBox = document.getElementById('resultBox');
            const placeholder = document.getElementById('placeholder');

            btn.innerText = 'Analyzing with Gemini AI...';
            btn.disabled = true;
            errorBox.classList.add('hidden');

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
                const text = await res.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch {
                    throw new Error("Server response invalid: " + text.slice(0, 150));
                }

                if (!res.ok || data.error) {
                    placeholder.classList.add('hidden');
                    resultBox.classList.add('hidden');
                    errorBox.innerText = 'Error: ' + (data.error || res.statusText);
                    errorBox.classList.remove('hidden');
                } else {
                    placeholder.classList.add('hidden');
                    errorBox.classList.add('hidden');
                    resultBox.classList.remove('hidden');

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
                placeholder.classList.add('hidden');
                resultBox.classList.add('hidden');
                errorBox.innerText = 'Network/Server Error: ' + err.message;
                errorBox.classList.remove('hidden');
            } finally {
                btn.innerText = 'Analyze & Qualify Lead ⚡';
                btn.disabled = false;
            }
        });

        function copyReply() {
            const text = document.getElementById('replyText').innerText;
            navigator.clipboard.writeText(text);
            document.getElementById('copyBtn').innerText = 'Copied ✓';
            setTimeout(() => document.getElementById('copyBtn').innerText = 'Copy Text', 2000);
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
        return jsonify({"error": "GEMINI_API_KEY Vercel settings mein missing hai!"}), 500

    data = request.json or {}
    name = data.get("name", "Customer")
    business_type = data.get("business_type", "Real Estate")
    inquiry = data.get("inquiry", "")
    budget = data.get("budget", "Not specified")

    prompt = f"""
    You are an expert B2B Sales Qualification AI for a {business_type} business in India.
    Analyze this lead and return ONLY valid JSON:
    - Name: {name}
    - Budget: {budget}
    - Message: "{inquiry}"

    JSON format:
    {{
        "score": "HOT" or "WARM" or "COLD",
        "confidence_percent": 85,
        "reason": "1-line sharp explanation in Hinglish/English",
        "recommended_action": "Exact next step for sales team",
        "instant_reply": "Persuasive ready-to-send WhatsApp reply to {name} (under 60 words)"
    }}
    """

    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    last_error = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            return jsonify(json.loads(response.text))
        except Exception as e:
            last_error = f"[{model_name}]: {str(e)}"
            continue

    return jsonify({"error": last_error}), 500
    
