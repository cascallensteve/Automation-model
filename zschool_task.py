import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from slack_sdk.webhook import WebhookClient

# === CONFIG ===
TOGETHER_API_KEY = "1025aee1a2e0373fdd1613905cd9519a6e500fabb7be8ac0346f267e4140f0b8"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q5es2Z92jZQe9jsaXf6eUXDtg67VHbGAwVnaesakt_c"
SHEET_TAB = "Form responses 1"

# === CLIENT SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(creds)

slack = WebhookClient(SLACK_WEBHOOK_URL)

# === GET LATEST RESPONSE ===
sheet = gc.open_by_url(SHEET_URL)
ws = sheet.worksheet(SHEET_TAB)
rows = ws.get_all_records()
if not rows:
    print("❌ No form submissions found.")
    exit()

latest = rows[-1]
form_text = "\n".join(f"{k}: {v}" for k, v in latest.items())

# === TOGETHER GPT SUMMARY ===
prompt = f"Summarize this Google Form response in two friendly sentences for Slack:\n\n{form_text}"

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7
}

response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=data)

if response.status_code != 200:
    print("❌ Together API error:", response.status_code, response.text)
    exit()

summary = response.json()["choices"][0]["message"]["content"]
print("✅ GPT Summary:", summary)

# === POST TO SLACK ===
slack_response = slack.send(text=f"📬 *New Submission*:\n{summary}")
if slack_response.status_code == 200 and slack_response.body == "ok":
    print("✅ Sent to Slack.")
else:
    print("❌ Slack error:", slack_response.status_code, slack_response.body)
