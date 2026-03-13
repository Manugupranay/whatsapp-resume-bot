"""
WhatsApp Resume Bot — Flask webhook
Powered by Twilio WhatsApp API + Claude AI
"""

import os
import traceback
import threading
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from tailor_resume import tailor_resume

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp_message(to, body):
    print(f"[BOT] Sending to {to}: {body[:80]}")
    try:
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to,
            body=body
        )
        print(f"[BOT] Sent! SID: {msg.sid}")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        traceback.print_exc()


@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From", "")
    incoming_msg = request.form.get("Body", "").strip()

    print(f"\n[WEBHOOK] From {sender}: {incoming_msg[:100]}")

    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("Hi! Send me a job description and I'll tailor Pranay's resume for it.")
        return str(resp)

    lower = incoming_msg.lower()
    if lower in ("hi", "hello", "hey", "start", "help"):
        resp.message(
            "👋 *Resume Bot for Pranay Manugu*\n\n"
            "Paste a job description and I'll send back a tailored resume summary within 30 seconds.\n\n"
            "Ready when you are!"
        )
        return str(resp)

    resp.message("Got it! Tailoring Pranay's resume for this role... give me ~30 seconds ⏳")
    thread = threading.Thread(target=process_jd, args=(sender, incoming_msg), daemon=True)
    thread.start()
    return str(resp)


def process_jd(sender, jd_text):
    print(f"\n[PROCESS] Starting for {sender}")
    try:
        print("[PROCESS] Calling Claude API...")
        tailored = tailor_resume(jd_text)
        print("[PROCESS] Claude done!")

        email = tailored.get("email", "pranaybmanugu@gmail.com")
        phone = tailored.get("phone", "(989) 400 7879")
        summary = tailored.get("summary", "")
        keywords = tailored.get("keywords_matched", [])
        keywords_str = ", ".join(keywords[:8]) if keywords else "N/A"
        experience = tailored.get("experience", [])
        skills = tailored.get("skills", {})

        all_skills = []
        if isinstance(skills, dict):
            for v in skills.values():
                if isinstance(v, list):
                    all_skills.extend(v[:3])
        elif isinstance(skills, list):
            all_skills = skills[:10]
        skills_str = ", ".join(all_skills[:10])

        exp_text = ""
        for exp in experience[:2]:
            title = exp.get("title", "")
            company = exp.get("company", "")
            bullets = exp.get("responsibilities", exp.get("achievements", []))
            bullet_str = ""
            for b in bullets[:2]:
                bullet_str += f"• {b}\n"
            exp_text += f"*{title} @ {company}*\n{bullet_str}\n"

        message = (
            f"✅ *Resume tailored for Pranay Manugu!*\n\n"
            f"🎯 *Keywords matched:* {keywords_str}\n\n"
            f"📋 *Summary:* {summary[:300]}\n\n"
            f"💼 *Recent Experience:*\n{exp_text}"
            f"🛠 *Top Skills:* {skills_str}\n\n"
            f"📧 {email} | {phone}\n\n"
            f"_Reply with another JD anytime!_"
        )

        if len(message) > 1500:
            message = message[:1500] + "...\n\n_Reply with another JD anytime!_"

        send_whatsapp_message(sender, message)
        print("[PROCESS] All done!")

    except Exception as e:
        print(f"[ERROR] process_jd failed: {e}")
        traceback.print_exc()
        try:
            send_whatsapp_message(sender, "Sorry, something went wrong. Please try again.")
        except:
            pass


@app.route("/health")
def health():
    return {"status": "ok", "bot": "Pranay Resume Bot"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🤖 Resume Bot running on port {port}")
    print(f"📱 Webhook URL: http://localhost:{port}/webhook")
    app.run(debug=False, host="0.0.0.0", port=port)