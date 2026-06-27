import requests
import time
import json
import os
import re
import threading
import telebot

# ==========================
# CONFIG
# ==========================
BOT_TOKEN = "8996577471:AAG9pOR2Hj_OAmawKX2oL4qPEWu4dRnO6dY"
GROUP_ID = "-1003960397555"
API_TOKEN = "258166|sHG7YNz8amnXrRTRg499zzNm9vUqICoLvVJB16JK36d3fd26"

API_URL = "https://api.iprn.pro/api/stock/public/edr"

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================
# FILE FOR SAVED SMS
# ==========================
DB_FILE = "sent_sms.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)

def load_sent():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_sent(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def extract_otp(text):
    match = re.search(r"\b\d{4,8}\b", text)
    if match:
        return match.group(0)
    return "Not Found"

# ==========================
# START COMMAND
# ==========================
@bot.message_handler(commands=['start'])
def start_message(message):
    text = f"""
👋 Welcome {message.from_user.first_name}!

🤖 OTP Forwarder Bot Active

✅ This bot automatically receives OTPs from the API.

📩 All OTPs are forwarded to the configured Telegram group.

Developer: @nooxvau
"""

    bot.reply_to(message, text)

# ==========================
# SEND TELEGRAM MESSAGE
# ==========================
def send_telegram(message):
    try:
        bot.send_message(
            GROUP_ID,
            message,
            parse_mode="HTML"
        )
    except Exception as e:
        print("Telegram Error:", e)

# ==========================
# CHECK SMS API
# ==========================
def check_sms():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            timeout=30
        )

        data = response.json()

        if "data" not in data:
            return

        sent = load_sent()

        for sms in reversed(data["data"]):

            unique_id = (
                str(sms.get("created_at", "")) +
                str(sms.get("b_number", "")) +
                str(sms.get("message", ""))
            )

            if unique_id in sent:
                continue

            otp = extract_otp(
                sms.get("message", "")
            )

            text = f"""
📩 <b>NEW OTP RECEIVED</b>

🏢 <b>Service:</b> {sms.get('a_number','N/A')}
📱 <b>Number:</b> {sms.get('b_number','N/A')}
🌍 <b>Destination:</b> {sms.get('destination','N/A')}

🔐 <b>OTP:</b> <code>{otp}</code>

💬 <b>Message:</b>

<code>{sms.get('message','')}</code>
"""

            send_telegram(text)

            sent.append(unique_id)

            if len(sent) > 5000:
                sent = sent[-5000:]

            save_sent(sent)

            print("New SMS Sent")

    except Exception as e:
        print("API Error:", e)

# ==========================
# BACKGROUND SMS LOOP
# ==========================
def sms_loop():
    print("SMS Monitoring Started...")

    while True:
        check_sms()
        time.sleep(10)

# ==========================
# MAIN
# ==========================
threading.Thread(
    target=sms_loop,
    daemon=True
).start()

print("Bot Started...")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
)