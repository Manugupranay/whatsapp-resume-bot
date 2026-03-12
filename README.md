# WhatsApp Resume Bot — Setup Guide
## For Pranay Manugu | Powered by Claude AI + Twilio

---

## What This Does

Your recruiters WhatsApp a job description → bot replies in 30 seconds with:
- A tailored DOCX resume (bullets reordered, summary rewritten for that specific JD)
- A list of keywords matched
- Ready to forward to the hiring manager

---

## Step 1 — Install Python dependencies

```bash
cd whatsapp_resume_bot
pip install -r requirements.txt
```

---

## Step 2 — Get your API keys

### Claude API Key
1. Go to https://console.anthropic.com
2. Click "API Keys" → "Create Key"
3. Copy the key (starts with `sk-ant-`)

### Twilio WhatsApp (free sandbox)
1. Go to https://console.twilio.com
2. Sign up free → go to "Messaging" → "Try it out" → "Send a WhatsApp message"
3. Follow the sandbox setup (you'll join by texting a code to a Twilio number)
4. Copy your **Account SID** and **Auth Token** from the dashboard

---

## Step 3 — Configure environment

```bash
cp .env.example .env
# Edit .env and fill in all 5 values
```

---

## Step 4 — Start the bot locally

```bash
# Load env vars and run
export $(cat .env | xargs)
python app.py
```

You'll see: `🤖 Resume Bot running on port 5000`

---

## Step 5 — Expose to internet with ngrok (for testing)

Twilio needs a public URL to send messages to your bot.

```bash
# Install ngrok from https://ngrok.com (free)
ngrok http 5000
```

You'll get a URL like `https://abc123.ngrok.io`

Update your `.env`:
```
BASE_URL=https://abc123.ngrok.io
```

Restart the bot after updating .env.

---

## Step 6 — Connect Twilio to your bot

1. In Twilio console → Messaging → Settings → WhatsApp Sandbox Settings
2. Set **"When a message comes in"** to:
   ```
   https://abc123.ngrok.io/webhook
   ```
3. Save

---

## Step 7 — Test it!

Have your recruiter (or yourself) send a WhatsApp message to the Twilio sandbox number with any job description. Within 30 seconds you'll get back a tailored resume.

---

## Going to Production (when you're ready)

Instead of ngrok, deploy to a free cloud server:

**Option A — Railway (easiest, free tier)**
```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

**Option B — Render**
1. Push code to GitHub
2. Go to render.com → New Web Service → connect repo
3. Add environment variables in Render dashboard
4. Deploy

Then update Twilio webhook URL to your production URL.

---

## File Structure

```
whatsapp_resume_bot/
├── app.py              ← Flask webhook server (WhatsApp handler)
├── tailor_resume.py    ← Claude AI resume tailoring engine
├── generate_docx.py    ← DOCX file generator
├── resume_data.py      ← Your master resume (update this anytime)
├── requirements.txt    ← Python dependencies
├── .env.example        ← Environment variables template
└── README.md           ← This file
```

---

## Updating Your Resume

All your resume content lives in `resume_data.py`.
When you get new experience or skills, just edit that one file — the bot picks it up immediately.

---

## How the AI Tailoring Works

1. Your master resume + the JD get sent to Claude
2. Claude rewrites your summary to match the JD's language
3. Reorders your skill categories (most relevant first)
4. Selects the 6-8 most relevant bullets per job
5. Slightly rephrases bullets to mirror JD terminology
6. Returns a JSON structure that gets rendered into a clean DOCX

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't respond | Check ngrok is running + Twilio webhook URL is correct |
| File not attaching | Make sure BASE_URL in .env matches your ngrok URL |
| Claude API error | Verify ANTHROPIC_API_KEY is set correctly |
| Twilio error | Check Account SID + Auth Token are correct |
