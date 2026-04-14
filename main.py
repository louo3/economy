from fastapi import FastAPI, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from datetime import datetime
import json

from .database import SessionLocal, init_db, StockSignal, AppConfig
from .scanner_engine import ScannerEngine
from .notifier import Notifier
from pathlib import Path

# 定義基礎目錄，確保在雲端環境也能正確找到模板與靜態檔案
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 初始化資料庫
init_db()

scheduler = BackgroundScheduler()
scanner = ScannerEngine()

def get_config():
    db = SessionLocal()
    configs = db.query(AppConfig).all()
    config_dict = {c.key: c.value for c in configs}
    db.close()
    return config_dict

def set_config(key, value):
    db = SessionLocal()
    config = db.query(AppConfig).filter(AppConfig.key == key).first()
    if config:
        config.value = value
    else:
        config = AppConfig(key=key, value=value)
        db.add(config)
    db.commit()
    db.close()

async def run_daily_scan():
    config = get_config()
    results = await scanner.run_scan()
    
    # 存入資料庫
    db = SessionLocal()
    for res in results:
        # 檢查是否已存在 (避免重複存入同一訊號)
        exists = db.query(StockSignal).filter(
            StockSignal.symbol == res['symbol'],
            StockSignal.breakout_date == res['breakout_date'],
            StockSignal.pullback_date == res['pullback_date']
        ).first()
        if not exists:
            db.add(StockSignal(**res))
    db.commit()
    db.close()
    
    # 傳送通知
    notifier = Notifier(
        telegram_token=config.get('telegram_token'),
        telegram_chat_id=config.get('telegram_chat_id'),
        email_config={
            'smtp_server': config.get('smtp_server'),
            'smtp_port': int(config.get('smtp_port', 587)),
            'sender_email': config.get('sender_email'),
            'password': config.get('gmail_password'),
            'receiver_email': config.get('receiver_email')
        } if config.get('sender_email') else None
    )
    
    if config.get('enable_telegram') == 'true':
        msg = notifier.format_signals_for_telegram(results)
        notifier.send_telegram(msg)
        
    if config.get('enable_email') == 'true':
        msg = notifier.format_signals_for_email(results)
        notifier.send_email("每日股票掃描報告", msg)

@app.on_event("startup")
def startup_event():
    config = get_config()
    cron_time = config.get('scan_time', '15:30').split(':')
    scheduler.add_job(
        lambda: asyncio.run(run_daily_scan()),
        CronTrigger(hour=int(cron_time[0]), minute=int(cron_time[1])),
        id="daily_scan",
        replace_existing=True
    )
    scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    db = SessionLocal()
    signals = db.query(StockSignal).order_by(StockSignal.pullback_date.desc()).limit(50).all()
    db.close()
    return templates.TemplateResponse(request=request, name="index.html", context={"signals": signals})
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    config = get_config()
    return templates.TemplateResponse(request=request, name="settings.html", context={"config": config})
@app.post("/settings/save")
async def save_settings(
    telegram_token: str = Form(None),
    telegram_chat_id: str = Form(None),
    enable_telegram: str = Form(None),
    smtp_server: str = Form(None),
    smtp_port: str = Form(None),
    sender_email: str = Form(None),
    gmail_password: str = Form(None),
    receiver_email: str = Form(None),
    enable_email: str = Form(None),
    scan_time: str = Form(None)
):
    set_config('telegram_token', telegram_token or "")
    set_config('telegram_chat_id', telegram_chat_id or "")
    set_config('enable_telegram', 'true' if enable_telegram else 'false')
    set_config('smtp_server', smtp_server or "smtp.gmail.com")
    set_config('smtp_port', smtp_port or "587")
    set_config('sender_email', sender_email or "")
    set_config('gmail_password', gmail_password or "")
    set_config('receiver_email', receiver_email or "")
    set_config('enable_email', 'true' if enable_email else 'false')
    set_config('scan_time', scan_time or "15:30")
    
    # 更新排程
    cron_time = scan_time.split(':')
    scheduler.add_job(
        lambda: asyncio.run(run_daily_scan()),
        CronTrigger(hour=int(cron_time[0]), minute=int(cron_time[1])),
        id="daily_scan",
        replace_existing=True
    )
    
    return RedirectResponse(url="/settings", status_code=303)

@app.post("/scan/now")
async def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_daily_scan)
    return {"status": "Scan started in background"}
