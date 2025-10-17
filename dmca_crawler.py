import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import date
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

BASE_URL = "https://lumendatabase.org/notices/"
START_ID = 28600000
END_ID = START_ID + 1000
KEYWORDS = ["Google Play", "play.google.com"]

# 从环境变量读取配置
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.hupogames.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

def fetch_notices():
    results = []
    for notice_id in range(START_ID, END_ID):
        url = f"{BASE_URL}{notice_id}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator=' ', strip=True)
            if any(k.lower() in text.lower() for k in KEYWORDS):
                title = soup.find("title").text if soup.find("title") else "No title"
                results.append({
                    "notice_id": notice_id,
                    "url": url,
                    "title": title,
                    "date": str(date.today())
                })
        except Exception as e:
            print(f"Error fetching {notice_id}: {e}")
    return results

def save_and_send(results):
    filename = f"dmca_googleplay_{date.today()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    msg = MIMEMultipart()
    msg["Subject"] = f"[DMCA Report] Google Play Notices - {date.today()}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    body = MIMEText(f"共发现 {len(results)} 条与 Google Play 相关的新 DMCA 投诉。\n详情见附件。", "plain", "utf-8")
    msg.attach(body)

    with open(filename, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    # 使用 SSL 安全发送
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ 邮件已成功发送至 {EMAIL_RECEIVER}")
    except Exception as e:
        print("❌ 邮件发送失败:", e)

if __name__ == "__main__":
    data = fetch_notices()
    if data:
        save_and_send(data)
    else:
        print("今日未发现新的 Google Play DMCA 投诉。")


