import json
import threading
import time
from datetime import datetime
import dateparser
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
from flask import Flask, request, jsonify

REMINDER_FILE = "reminders.json"

app = Flask(__name__)

# Load GPT2
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f, indent=2)

def parse_input(text):
    """
    Parse the input text for date and type using dateparser and keywords
    """

    # Extract date from text
    dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not dt:
        return None, None, None

    # Basic keyword-based type
    lowered = text.lower()
    if "birthday" in lowered:
        rtype = "birthday"
    elif "doctor" in lowered or "visit" in lowered:
        rtype = "doctor"
    elif "pay" in lowered or "payment" in lowered or "due" in lowered:
        rtype = "payment"
    else:
        rtype = "general"

    # Remove date words for description roughly
    description = text
    if dt:
        # Remove date substring from description (approximate)
        date_str = dt.strftime("%B %d %Y")
        description = description.replace(date_str, "")
    
    return rtype, description.strip(), dt.strftime("%Y-%m-%d")

def add_reminder(text):
    reminders = load_reminders()
    rtype, desc, date_str = parse_input(text)
    if not date_str:
        return False, "Could not detect a date in your input."

    reminders.append({
        "type": rtype,
        "description": desc,
        "date": date_str
    })
    save_reminders(reminders)
    return True, f"Added reminder [{rtype}]: {desc} on {date_str}"

def check_reminders():
    reminders = load_reminders()
    now = datetime.now().strftime("%Y-%m-%d")
    for r in reminders:
        if r["date"] == now:
            print(f"Reminder Today! [{r['type']}] - {r['description']}")

def reminder_loop():
    while True:
        check_reminders()
        time.sleep(60 * 60)  # check every hour

@app.route("/add", methods=["POST"])
def add():
    data = request.json
    text = data.get("text", "")
    success, msg = add_reminder(text)
    return jsonify({"success": success, "message": msg})

@app.route("/list", methods=["GET"])
def list_reminders():
    return jsonify(load_reminders())

if __name__ == "__main__":
    threading.Thread(target=reminder_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
