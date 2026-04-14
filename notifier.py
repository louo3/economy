import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

class Notifier:
    def __init__(self, telegram_token=None, telegram_chat_id=None, email_config=None):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.email_config = email_config # {smtp_server, smtp_port, sender_email, password, receiver_email}

    def send_telegram(self, message):
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def send_email(self, subject, body):
        if not self.email_config:
            return False
        
        c = self.email_config
        try:
            msg = MIMEMultipart()
            msg['From'] = c['sender_email']
            msg['To'] = c['receiver_email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(c['smtp_server'], c['smtp_port'])
            server.starttls()
            server.login(c['sender_email'], c['password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

    def format_signals_for_telegram(self, signals):
        if not signals:
            return "今日未發現符合條件的股票。"
        
        text = "<b>【股票掃描結果集】</b>\n\n"
        for s in signals:
            text += f"股票: {s['symbol']} {s['name']}\n"
            text += f"突破日期: {s['breakout_date']} | 價格: {s['breakout_price']}\n"
            text += f"拉回日期: {s['pullback_date']} | 價格: {s['pullback_price']}\n"
            text += "----------\n"
        return text

    def format_signals_for_email(self, signals):
        if not signals:
            return "<h3>今日未發現符合條件的股票。</h3>"
        
        html = "<h2>今日股票掃描篩選結果</h2>"
        html += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
        html += "<tr style='background-color: #f2f2f2;'><th>代號</th><th>名稱</th><th>突破日期</th><th>突破價格</th><th>拉回日期</th><th>拉回價格</th></tr>"
        for s in signals:
            html += f"<tr><td>{s['symbol']}</td><td>{s['name']}</td><td>{s['breakout_date']}</td><td>{s['breakout_price']}</td><td>{s['pullback_date']}</td><td>{s['pullback_price']}</td></tr>"
        html += "</table>"
        return html
