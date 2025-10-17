import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from dateutil import parser as dateparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ====== 配置 ======
LUMEN_SEARCH_URL = "https://lumendatabase.org/search?field=recipient&value=Google+LLC"
KEYWORDS = ["Google Play", "Google Play Store", "Play Store", "Google LLC", "Google"]
STATE_FILE = "seen_notices.json"

# SMTP 配置从环境变量读取
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.exmail.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = SMTP_USER
EMAIL_TO = os.getenv("EMAIL_TO", "yangyichen@hupogames.com").split(",")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "新增 Google Play DMCA 通告通知")

HEADERS = {"User-Agent": "lumen-monitor/1.0 (+https://your.domain/)"}

if not SMTP_USER or not SMTP_PASSWORD:
    raise SystemExit("错误：请在环境变量中设置 SMTP_USER 和 SMTP_PASSWORD")

# ====== 工具函数 ======
def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def parse_notice_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1") and soup.find("h1").get_text(strip=True) or ""

    def find_value(label):
        node = soup.find(lambda tag: tag.name in ["h5","h6"] and label in tag.get_text())
        if not node:
            return ""
        nxt = node.find_next_sibling()
        return nxt.get_text(strip=True) if nxt else ""

    sender = find_value("Sender") or ""
    recipient = find_value("Recipient") or ""
    principal = find_value("Principal") or ""

    date = None
    for part in soup.get_text(separator="\n").splitlines():
        if "Sent on" in part or "Sent" in part:
            try:
                date = dateparser.parse(part, fuzzy=True).isoformat()
                break
            except:
                continue

    desc_node = soup.find(lambda t: t.name == "div" and "Description" in t.get_text()) or None
    description = desc_node.get_text(separator=" ", strip=True) if desc_node else ""

    notice_id = url.rstrip("/").split("/")[-1] if "/notices/" in url else url
    return {"id": notice_id, "url": url, "title": title, "sender": sender,
            "recipient": recipient, "principal": principal, "date": date, "description": description}

def load_seen():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    return {}

def save_seen(d):
    json.dump(d, open(STATE_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def is_relevant(notice):
    text = " ".join([notice.get(k,"") for k in ("title","description","recipient","principal","sender")]).lower()
    return any(k.lower() in text for k in KEYWORDS)

def send_email(notices):
    if not notices:
        return
    body = ""
    for n in notices:
        body += f"ID: {n['id']}\nTitle: {n['title']}\nSender: {n['sender']}\nPrincipal: {n['principal']}\nDate: {n['date']}\nURL: {n['url']}\nDescription: {n['description'][:300]}...\n\n"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = ", ".join(EMAIL_TO)
    msg['Subject'] = EMAIL_SUBJECT
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

# ====== 主程序 ======
def main():
    seen = load_seen()
    new_notices = []

    # 简单示例：单条 URL，可改为搜索结果解析
    to_check = ["https://lumendatabase.org/notices/28600464"]

    for url in to_check:
        html = fetch_page(url)
        notice = parse_notice_page(html, url)
        if is_relevant(notice) and notice["id"] not in seen:
            new_notices.append(notice)
            seen[notice["id"]] = {"url": notice["url"], "first_seen": datetime.utcnow().isoformat(), "meta": notice}

    save_seen(seen)
    if new_notices:
        send_email(new_notices)
        print(f"{len(new_notices)} 条新通告已发送到 {EMAIL_TO}")
    else:
        print("没有新增通告")

if __name__ == "__main__":
    main()

