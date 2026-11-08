import requests
from bs4 import BeautifulSoup
import time
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ===================== 【这里是你要改的配置】=====================
NEWS_URL = "https://xxx.com/news"  # 改成你的资讯列表页
MAIL_SENDER = "xxx@qq.com"         # 发件邮箱
MAIL_SENDER_PWD = "你的邮箱SMTP授权码"
MAIL_RECEIVER = "xxx@qq.com"       # 收件邮箱
SMTP_SERVER = "smtp.qq.com"        # QQ邮箱：smtp.qq.com；163：smtp.163.com
SMTP_PORT = 465
TIME_ZONE = "Asia/Shanghai"
# 保存历史记录，用来去重
RECORD_FILE = "history.txt"
# =================================================================

def get_md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def load_history():
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_history(history_set):
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(list(history_set)[-100:])) # 只保留最近100条，防止文件过大

def fetch_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(NEWS_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # --------------------------
    # ✅【重点】这里需要适配网站！
    # 下面是示例选择器，大部分网站需要我帮你修改
    # 示例：假设新闻在 <li class="news-item"> 里面
    news_items = soup.select("li.news-item")
    # --------------------------
    news_list = []
    for item in news_items:
        try:
            title_tag = item.select_one("a")
            title = title_tag.get_text(strip=True)
            link = title_tag["href"]
            if not link.startswith("http"):
                link = NEWS_URL.rstrip("/") + "/" + link.lstrip("/")
            news_list.append({"title": title, "link": link})
        except Exception as e:
            continue
    return news_list

def send_email(news_content):
    msg = MIMEText(news_content, "html", "utf-8")
    msg["Subject"] = Header("【每日资讯简报】", "utf-8")
    msg["From"] = Header("资讯助手", "utf-8")
    msg["To"] = Header(MAIL_RECEIVER, "utf-8")
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(MAIL_SENDER, MAIL_SENDER_PWD)
        server.sendmail(MAIL_SENDER, MAIL_RECEIVER, msg.as_string())

def main():
    history = load_history()
    all_news = fetch_news()
    new_news = []
    for n in all_news:
        key = get_md5(n["link"])
        if key not in history:
            new_news.append(n)
            history.add(key)
    save_history(history)

    if not new_news:
        content = "<h3>今日暂无新增资讯</h3>"
    else:
        content = "<h3>今日新增资讯：</h3><ul>"
        for n in new_news:
            content += f'<li><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>'
        content += "</ul>"
    send_email(content)
    print("简报发送完成！")

if __name__ == "__main__":
    main()
