"""
WhatsApp Resume Bot — Flask webhook
Powered by Twilio WhatsApp API + Claude AI
"""

import os
import tempfile
import traceback
import threading
from flask import Flask, request, send_file, abort
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from tailor_resume import tailor_resume
from generate_docx import generate_docx

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

_temp_files = {}


def send_whatsapp_message(to, body, media_url=None):
    print(f"[BOT] Sending message to {to}: {body[:80]}")
    kwargs = {"from_": TWILIO_WHATSAPP_NUMBER, "to": to, "body": body}
    if media_url:
        kwargs["media_url"] = [media_url]
    try:
        msg = twilio_client.messages.create(**kwargs)
        print(f"[BOT] Message sent! SID: {msg.sid}")
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        traceback.print_exc()


@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From", "")
    incoming_msg = request.form.get("Body", "").strip()

    print(f"\n[WEBHOOK] Message from {sender}: {incoming_msg[:100]}")

    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("Hi! Send me a job description and I'll tailor Pranay's resume for it.")
        return str(resp)

    lower = incoming_msg.lower()
    if lower in ("hi", "hello", "hey", "start", "help"):
        resp.message(
            "👋 *Resume Bot for Pranay Manugu*\n\n"
            "Just paste the full job description and I'll send back "
            "a tailored resume DOCX within 30 seconds.\n\n"
            "Ready when you are!"
        )
        return str(resp)

    resp.message("Got it! Tailoring Pranay's resume for this role... give me ~30 seconds ⏳")

    thread = threading.Thread(target=process_jd, args=(sender, incoming_msg), daemon=True)
    thread.start()

    return str(resp)


def process_jd(sender, jd_text):
    print(f"\n[PROCESS] Starting resume tailoring for {sender}")
    try:
        print("[PROCESS] Calling Claude API...")
        tailored = tailor_resume(jd_text)
        print("[PROCESS] Claude done! Generating DOCX...")

        docx_bytes = generate_docx(tailored)
        print(f"[PROCESS] DOCX generated! Size: {len(docx_bytes)} bytes")

        file_id = f"resume_{sender.replace('whatsapp:+', '')}_{os.getpid()}.docx"
        file_path = os.path.join(tempfile.gettempdir(), file_id)
        with open(file_path, "wb") as f:
            f.write(docx_bytes)
        _temp_files[file_id] = file_path
        print(f"[PROCESS] File saved: {file_path}")

        base_url = os.environ.get("BASE_URL", "http://localhost:5000")
        media_url = f"{base_url}/files/{file_id}"
        print(f"[PROCESS] Media URL: {media_url}")

        keywords = tailored.get("keywords_matched", [])
        keywords_str = ", ".join(keywords[:10]) if keywords else "N/A"

        summary = (
            f"✅ *Resume tailored!*\n\n"
            f"🎯 *Keywords matched:* {keywords_str}\n\n"
            f"📄 Resume attached as DOCX — ready to send!"
        )

        send_whatsapp_message(sender, summary, media_url=media_url)
        print("[PROCESS] All done!")

    except Exception as e:
        print(f"[ERROR] process_jd failed: {e}")
        traceback.print_exc()
        send_whatsapp_message(sender, f"Sorry, something went wrong: {str(e)[:200]}")


@app.route("/files/<file_id>")
def serve_file(file_id):
    path = _temp_files.get(file_id)
    if not path or not os.path.exists(path):
        abort(404)
    return send_file(
        path,
        as_attachment=True,
        download_name="Pranay_Manugu_Resume.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.route("/health")
def health():
    return {"status": "ok", "bot": "Pranay Resume Bot"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🤖 Resume Bot running on port {port}")
    print(f"📱 Webhook URL: http://localhost:{port}/webhook")
    app.run(debug=False, port=port)